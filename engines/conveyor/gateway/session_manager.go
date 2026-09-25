package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"

	pb "conveyor/gateway/pb"
	"google.golang.org/grpc"
	"google.golang.org/grpc/metadata"
)

// GatewaySessionManager owns waiting, active and closing lifetimes. The
// EngineCore ResidencyPlanner chooses slots and budgets from physical pools.
// No arrival moves existing sessions to a different phase.
type GatewaySessionManager struct {
	mu      sync.Mutex
	waiting []*Session
	closing []*Session
	wake    chan struct{}
	enabled bool
	epoch   time.Time
	admit   func(*Session) (bool, int, string, error)
	release func(*Session) error
}

func newSessionManager(enabled bool, epoch time.Time) *GatewaySessionManager {
	m := &GatewaySessionManager{enabled: enabled, epoch: epoch, wake: make(chan struct{}, 1)}
	m.admit = m.requestAdmission
	m.release = m.releaseBackend
	return m
}

func (m *GatewaySessionManager) signal() {
	select {
	case m.wake <- struct{}{}:
	default:
	}
}

func (m *GatewaySessionManager) enqueue(s *Session) {
	m.mu.Lock()
	m.waiting = append(m.waiting, s)
	m.mu.Unlock()
	m.signal()
}

func (m *GatewaySessionManager) close(s *Session) {
	s.mu.Lock()
	if !s.alive {
		s.mu.Unlock()
		return
	}
	s.alive = false
	s.audioBuf = nil
	s.inputFrames = nil
	s.mu.Unlock()
	sessions.Delete(s.id)
	m.mu.Lock()
	m.closing = append(m.closing, s)
	m.mu.Unlock()
	m.signal()
}

// advance never holds the queue lock during RPCs. Only this control loop calls
// it. Closing reservations take priority; failed cleanup cannot create a free
// admission slot. A disconnected head is removed without starving the queue.
func (m *GatewaySessionManager) advance() bool {
	m.mu.Lock()
	if len(m.closing) > 0 {
		s := m.closing[0]
		m.mu.Unlock()
		if err := m.release(s); err != nil {
			log.Printf("session cleanup pending sid=%d: %v", s.id, err)
			return false
		}
		m.mu.Lock()
		m.closing = m.closing[1:]
		m.mu.Unlock()
		log.Printf("session released sid=%d", s.id)
		s.mu.Lock()
		completed := s.completed
		s.mu.Unlock()
		if completed {
			s.send(map[string]any{"type": "session.completed"})
		}
		if s.conn != nil {
			_ = s.conn.Close()
		}
		return true
	}
	if !m.enabled || len(m.waiting) == 0 {
		m.mu.Unlock()
		return false
	}
	s := m.waiting[0]
	m.mu.Unlock()
	s.mu.Lock()
	alive := s.alive
	s.mu.Unlock()
	if !alive {
		m.mu.Lock()
		m.waiting = m.waiting[1:]
		m.mu.Unlock()
		return true
	}
	admitted, slot, reason, err := m.admit(s)
	if err != nil {
		log.Printf("admission pending sid=%d: %v", s.id, err)
		return false
	}
	if !admitted {
		if *openLoop && reason != "plan_transition" {
			m.mu.Lock()
			m.waiting = m.waiting[1:]
			m.mu.Unlock()
			s.send(map[string]any{"type": "session.rejected", "reason": reason})
			serviceEvent("session_rejected", s.id, 0, map[string]any{"reason": reason})
			m.close(s)
			return true
		}
		s.mu.Lock()
		changed := s.blockedReason != reason
		s.blockedReason = reason
		s.mu.Unlock()
		if changed {
			log.Printf("session queued sid=%d reason=%s", s.id, reason)
		}
		return false
	}
	m.mu.Lock()
	m.waiting = m.waiting[1:]
	m.mu.Unlock()
	s.mu.Lock()
	alive = s.alive
	if alive {
		s.slot = slot
		s.admitted = true
		if *openLoop {
			s.firstRelease = firstRelease(s.sourceStart, m.epoch, slot)
			s.drainTick = s.firstRelease
		}
	}
	s.mu.Unlock()
	// If disconnect raced this RPC, close() already queued backend cleanup.
	if alive {
		log.Printf("session admitted sid=%d slot=%d", s.id, slot)
		s.send(map[string]any{"type": "session.admitted", "slot": slot,
			"epoch_ns": m.epoch.UnixNano(), "period_ns": int64(*periodMS) * int64(time.Millisecond), "slots": *slots,
			"first_release_ns": s.firstRelease.UnixNano(), "phase_policy": *phasePolicy,
			"wait_ms": float64(time.Since(s.connectedAt).Microseconds()) / 1000})
	}
	return true
}

func (m *GatewaySessionManager) run(ctx context.Context) {
	timer := time.NewTicker(100 * time.Millisecond)
	defer timer.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-m.wake:
		case <-timer.C:
		}
		for m.advance() {
			select {
			case <-ctx.Done():
				return
			default:
			}
		}
	}
}

func (m *GatewaySessionManager) requestAdmission(s *Session) (bool, int, string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), stepTimeout)
	defer cancel()
	ctx = metadata.NewOutgoingContext(ctx, metadata.Pairs(
		"x-pilarius-control", "admit",
		"x-pilarius-period-ns", fmt.Sprint((time.Duration(*periodMS)*time.Millisecond).Nanoseconds()),
		"x-pilarius-slots", fmt.Sprint(*slots),
		"x-pilarius-epoch-ns", fmt.Sprint(m.epoch.UnixNano())))
	if *openLoop {
		ctx = metadata.AppendToOutgoingContext(ctx, "x-pilarius-source-start-ns", fmt.Sprint(s.sourceStart.UnixNano()))
	}
	var header metadata.MD
	_, err := client.Step(ctx, &pb.StepRequest{Sessions: []*pb.SessionInput{{Sid: s.id}}}, grpc.Header(&header))
	if err != nil {
		return false, 0, "", err
	}
	values := header.Get("x-pilarius-admission")
	if len(values) != 1 {
		return false, 0, "", fmt.Errorf("missing admission result")
	}
	var result struct {
		Admitted bool   `json:"admitted"`
		Reason   string `json:"reason"`
		Plan     struct {
			Slot int `json:"slot"`
		} `json:"plan"`
	}
	if err = json.Unmarshal([]byte(values[0]), &result); err != nil {
		return false, 0, "", err
	}
	if result.Admitted && (result.Plan.Slot < 0 || result.Plan.Slot >= *slots) {
		return false, 0, "", fmt.Errorf("planner returned invalid slot")
	}
	return result.Admitted, result.Plan.Slot, result.Reason, nil
}

func (m *GatewaySessionManager) releaseBackend(s *Session) error {
	ctx, cancel := context.WithTimeout(context.Background(), stepTimeout)
	defer cancel()
	ctx = metadata.NewOutgoingContext(ctx, metadata.Pairs("x-pilarius-control", "close"))
	response, err := client.Step(ctx, &pb.StepRequest{Sessions: []*pb.SessionInput{{Sid: s.id, Cancel: true}}})
	if err != nil {
		return err
	}
	for _, output := range response.Outputs {
		if output.Sid == s.id && output.Finished {
			return nil
		}
	}
	return fmt.Errorf("backend did not confirm session cleanup")
}
