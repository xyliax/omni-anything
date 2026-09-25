// Conveyor gateway with release-offset scheduling.
//
// Each session receives a stable slot within period T. The slot wheel uses an
// absolute time grid, so a late wake does not re-anchor later releases. The
// offsets spread offered input and restore demand across the period; they do
// not create the per-session reuse interval, which follows from periodicity.
//
// Step enqueues current input and returns any already-undelivered output. The
// inherited deadline_met wire field therefore reports only whether this service
// RPC completed within the configured period; it is not a statement that a
// required token amount or an audio playback deadline was met. Per-release
// output counts are recorded in GW_TICKLOG for later evaluation design.
package main

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"time"

	pb "conveyor/gateway/pb"

	"github.com/gorilla/websocket"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/keepalive"
	"google.golang.org/grpc/metadata"
)

type Session struct {
	id            uint64
	slot          int // release slot on the periodic wheel, fixed at admission
	conn          *websocket.Conn
	writeMu       sync.Mutex // gorilla allows one concurrent writer
	mu            sync.Mutex // guards the fields below
	audioBuf      []byte
	sr            int32
	fullDup       bool // continuous full-duplex: process every tick from buffered audio, no turns
	fdStart       time.Time
	fdFirst       bool // first nonzero delivery seen (TTFA semantics)
	alive         bool
	admitted      bool
	connectedAt   time.Time
	blockedReason string
	ending        bool
	completed     bool
	inputSequence uint64
	inputFrames   []InputFrame
	sourceStart   time.Time // immutable exogenous clock, supplied before admission
	firstRelease  time.Time
	drainTick     time.Time
}

var (
	upgrader = websocket.Upgrader{ReadBufferSize: 1 << 16, WriteBufferSize: 1 << 16,
		CheckOrigin: func(r *http.Request) bool { return true }}
	sessions       sync.Map
	nextID         uint64
	client         pb.InferenceClient
	periodMS       = flag.Int("period-ms", 1000, "tick period")
	slots          = flag.Int("slots", 8, "phase slots per period; multiple sessions may share a slot")
	admission      = flag.Bool("admission", false, "queue sessions until the residency planner accepts them")
	openLoop       = flag.Bool("open-loop", false, "preserve source clocks and reject infeasible arrivals once")
	phasePolicy    = flag.String("phase-policy", "assigned", "assigned or natural phase")
	manager        *GatewaySessionManager
	outputTokenCap = flag.Int("output-token-cap", 25, "maximum output tokens consumed per session release")
	port           = flag.String("port", "8902", "ws listen port")
	worker         = flag.String("worker", "127.0.0.1:50051", "vLLM gRPC worker addr")
	tickLog        *os.File // GW_TICKLOG per-firing trace (header change 4)
)

// stepTimeout bounds one gRPC Step. Conveyor Steps normally return in
// milliseconds by design, so a long stall is transport or worker death — fail
// the firing fast and let the absolute grid resume, instead of freezing the
// whole wheel behind one call.
const stepTimeout = 10 * time.Second

// tickTrace appends one machine-readable line per slot firing (format in header change 4).
// Timestamps are epoch-clock so trace alignment with scheduler.log is exact; no-op unless
// GW_TICKLOG is set.
func tickTrace(wake time.Time, slot int, lateMs, sampleMs, grpcMs, gpuMs float64, deliv []string) {
	if tickLog == nil {
		return
	}
	line := fmt.Sprintf("%.6f slot=%d late_ms=%.1f sample_ms=%.1f grpc_ms=%.1f gpu_ms=%.1f n=%d",
		float64(wake.UnixNano())/1e9, slot, lateMs, sampleMs, grpcMs, gpuMs, len(deliv))
	if len(deliv) > 0 {
		line += " deliv=" + strings.Join(deliv, ",")
	}
	fmt.Fprintln(tickLog, line)
}

func (s *Session) send(v any) {
	if s.conn == nil {
		return
	}
	s.writeMu.Lock()
	defer s.writeMu.Unlock()
	_ = s.conn.SetWriteDeadline(time.Now().Add(time.Second))
	_ = s.conn.WriteJSON(v)
}

func handle(w http.ResponseWriter, r *http.Request) {
	if *openLoop && r.URL.Path == "/clock" {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{"epoch_ns": manager.epoch.UnixNano(), "period_ns": int64(*periodMS) * int64(time.Millisecond)})
		return
	}
	c, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		return
	}
	id := atomic.AddUint64(&nextID, 1)
	s := &Session{id: id, slot: int((id - 1) % uint64(*slots)), conn: c, sr: 16000,
		alive: true, admitted: !*admission, connectedAt: time.Now()}
	if *admission {
		s.slot = -1
	}
	if *openLoop {
		ns, err := strconv.ParseInt(r.URL.Query().Get("source_start_ns"), 10, 64)
		if err != nil || ns <= 0 {
			c.Close()
			return
		}
		s.sourceStart = time.Unix(0, ns)
	}
	sessions.Store(id, s)
	defer func() {
		manager.close(s)
		c.Close()
	}()
	s.send(map[string]any{"type": "session.created", "session": map[string]any{"id": id},
		"admission_required": *admission})
	if *admission {
		manager.enqueue(s)
	}
	c.SetReadLimit(8 << 20)
	for {
		_, data, err := c.ReadMessage()
		if err != nil {
			return
		}
		var ev struct {
			Type    string          `json:"type"`
			Audio   string          `json:"audio"`
			Session json.RawMessage `json:"session"`
		}
		if json.Unmarshal(data, &ev) != nil {
			continue
		}
		switch ev.Type {
		case "session.update":
			var cfg struct {
				SR int32 `json:"input_sample_rate"`
				TD struct {
					Type string `json:"type"`
				} `json:"turn_detection"`
			}
			json.Unmarshal(ev.Session, &cfg)
			s.mu.Lock()
			if cfg.SR > 0 {
				s.sr = cfg.SR
			}
			s.fullDup = cfg.TD.Type == "full_duplex"
			s.mu.Unlock()
			s.send(map[string]any{"type": "session.updated"})
		case "input_audio_buffer.append":
			if raw, e := base64.StdEncoding.DecodeString(ev.Audio); e == nil {
				s.mu.Lock()
				if !s.admitted || s.ending {
					s.mu.Unlock()
					s.send(map[string]any{"type": "error", "error": "wait for session.admitted before sending audio"})
					continue
				}
				s.audioBuf = append(s.audioBuf, raw...)
				if frameLog != nil {
					s.stageFrames(false)
				}
				s.mu.Unlock()
			}
		case "input_audio_buffer.commit":
			// no-op: the tick loop drains the buffer when staging the frame
		case "session.end":
			if !*admission {
				s.send(map[string]any{"type": "error", "error": "session.end requires managed admission"})
				continue
			}
			s.mu.Lock()
			s.ending = true
			if frameLog != nil {
				s.stageFrames(true)
			}
			s.mu.Unlock()
		}
	}
}

// tickLoop runs isolated from connection I/O. It walks the slot wheel: one firing every
// period/slots, serving only that slot's sessions — each session still experiences a full
// `period` between its own consecutive ticks, but the engine sees arrivals spread evenly
// across the period instead of one synchronized stampede. Firing k is scheduled at
// t0 + k*slotPeriod (absolute grid): a late firing does not shift the grid, the next one
// lands back on it.
func tickLoop() {
	period := time.Duration(*periodMS) * time.Millisecond
	slotPeriod := period / time.Duration(*slots)
	t0 := manager.epoch.Add(-slotPeriod)
	for k := int64(1); ; k++ {
		slot := int((k - 1) % int64(*slots))
		next := t0.Add(time.Duration(k) * slotPeriod)
		time.Sleep(time.Until(next))
		dispatchTick(next, slot, false)
	}
}

func dispatchTick(next time.Time, slot int, replay bool) {
	period := time.Duration(*periodMS) * time.Millisecond
	budgetMs := float64(*periodMS)
	tickT0 := time.Now()
	lateMs := tickT0.Sub(next).Seconds() * 1000

	// TokensPerTick is the inherited protobuf field name. Conveyor treats it
	// as an output cap, not as a required delivery amount.
	req := &pb.StepRequest{TokensPerTick: uint32(*outputTokenCap)}
	var active []*Session
	var ending []string
	frameIDs := map[string]uint64{}
	sessions.Range(func(_, v any) bool {
		s := v.(*Session)
		s.mu.Lock()
		defer s.mu.Unlock()
		if (!replay && s.slot != slot) || !s.alive || !s.admitted || !s.fullDup {
			return true
		}
		if replay && !replayDue(s).Equal(next) {
			return true
		}
		if frameLog != nil {
			var audio []byte
			if len(s.inputFrames) > 0 {
				frame := s.inputFrames[0]
				if !replay && frame.Ready.After(next) {
					return true
				}
				s.inputFrames = s.inputFrames[1:]
				audio = frame.Audio
				if s.fdStart.IsZero() {
					s.fdStart = frame.Ready
				}
				frameIDs[fmt.Sprint(s.id)] = frame.Sequence
				serviceEvent("input_release", s.id, frame.Sequence, map[string]any{
					"release_ns": next.UnixNano(), "deadline_ns": next.Add(period).UnixNano(),
					"slot": slot, "samples": len(audio) / 2})
			} else if !s.ending {
				return true
			}
			req.Sessions = append(req.Sessions, &pb.SessionInput{Sid: s.id, AudioPcm16: audio, SampleRate: uint32(s.sr)})
			if s.ending && len(s.inputFrames) == 0 {
				ending = append(ending, fmt.Sprint(s.id))
			}
			if replay {
				s.drainTick = next.Add(period)
			}
			active = append(active, s)
			return true
		}
		// A first slice below ~40ms of audio yields zero encoder output tokens and
		// kills the session in the model runner (vLLM qwen2_5_omni "too short to be
		// represented"). Hold the first fire until one slot-period of audio buffered;
		// the session starts one period later on its own grid.
		if !s.ending && !s.fdFirst && len(s.audioBuf) < int(s.sr)*2*(*periodMS / *slots)/1000 {
			return true
		}
		if len(s.audioBuf) == 0 && !s.ending {
			return true
		}
		// CONTINUOUS full-duplex: sample the new audio since last tick, no turns.
		in := &pb.SessionInput{Sid: s.id, NewTurn: false, AudioPcm16: s.audioBuf,
			SampleRate: uint32(s.sr)}
		s.audioBuf = nil
		// Set once, never reset: the first slice legitimately returns no
		// tokens from the undelivered-output buffer, so resetting here every tick would make
		// server_ttfa_ms measure one gRPC round-trip instead of the true
		// audio-in -> first-token-out latency including the pipeline lag.
		if !s.fdFirst && s.fdStart.IsZero() {
			s.fdStart = time.Now()
		}
		req.Sessions = append(req.Sessions, in)
		if s.ending {
			ending = append(ending, fmt.Sprint(s.id))
		}
		active = append(active, s)
		return true
	})
	if len(req.Sessions) == 0 {
		tickTrace(tickT0, slot, lateMs, 0, 0, 0, nil)
		return
	}
	sampleMs := time.Since(tickT0).Seconds() * 1000
	grpcT0 := time.Now()
	ctx, cancel := context.WithTimeout(context.Background(), stepTimeout)
	frameJSON, _ := json.Marshal(frameIDs)
	ctx = metadata.NewOutgoingContext(ctx, metadata.Pairs(
		"x-pilarius-frame-ids", string(frameJSON),
		"x-pilarius-next-tick-ns", fmt.Sprint(next.Add(period).UnixNano()),
		"x-pilarius-period-ns", fmt.Sprint(period.Nanoseconds()),
		"x-pilarius-ending-sids", strings.Join(ending, ",")))
	resp, err := client.Step(ctx, req)
	cancel()
	if err != nil {
		log.Printf("Step error: %v", err)
		if frameLog != nil {
			for _, s := range active {
				s.send(map[string]any{"type": "error", "error": fmt.Sprintf("input execution failed: %v", err)})
				manager.close(s)
			}
		}
		// keep the grid evidence gap-free: an errored firing still logs
		// (n reflects staged sessions; no deliveries happened).
		tickTrace(tickT0, slot, lateMs, sampleMs, 0, 0, nil)
		return
	}
	grpcMs := time.Since(grpcT0).Seconds() * 1000
	fanoutT0 := time.Now()
	byID := map[uint64]*pb.SessionOutput{}
	for _, o := range resp.Outputs {
		byID[o.Sid] = o
	}
	batch := uint32(len(active))
	deliv := make([]string, 0, len(active)) // per-session delivered tokens, measured at the delivery point
	for _, s := range active {
		o := byID[s.id]
		if o == nil {
			deliv = append(deliv, fmt.Sprintf("%d:0", s.id))
			continue
		}
		deliv = append(deliv, fmt.Sprintf("%d:%d", s.id, len(o.Tokens)))
		s.mu.Lock()
		var fdTtfa float64
		if !s.fdFirst && len(o.Tokens) > 0 {
			s.fdFirst = true
			fdTtfa = float64(time.Since(s.fdStart).Milliseconds())
		}
		s.mu.Unlock()
		if o.Text != "" {
			s.send(map[string]any{"type": "response.text.delta", "delta": o.Text})
			s.send(map[string]any{"type": "response.audio_transcript.delta", "delta": o.Text})
		}
		if len(o.AudioOut) > 0 {
			s.send(map[string]any{"type": "response.audio.delta",
				"audio":       base64.StdEncoding.EncodeToString(o.AudioOut),
				"sample_rate": o.AudioSr})
		}
		rpcMet := grpcMs <= budgetMs
		s.send(map[string]any{"type": "metronome.tick", "latency_ms": grpcMs,
			"budget_ms": budgetMs, "deadline_met": rpcMet, "batch": batch,
			"server_ttfa_ms": fdTtfa})
		if o.Finished {
			s.mu.Lock()
			ended := s.ending
			s.completed = ended
			s.mu.Unlock()
			if !ended {
				s.send(map[string]any{"type": "error", "error": "backend session ended unexpectedly"})
			}
			manager.close(s)
		}
	}
	tickTrace(tickT0, slot, lateMs, sampleMs, grpcMs, float64(resp.GpuMs), deliv)
	if os.Getenv("GW_DEBUG") != "" {
		fanoutMs := time.Since(fanoutT0).Seconds() * 1000
		totalMs := time.Since(tickT0).Seconds() * 1000
		// transport = gRPC round-trip minus the worker's own GPU compute
		log.Printf("[gwtick] N=%d sample=%.1fms grpc=%.1fms gpu=%.1fms transport=%.1fms fanout=%.1fms total=%.1fms OVERHEAD=%.1fms",
			batch, sampleMs, grpcMs, resp.GpuMs, grpcMs-resp.GpuMs, fanoutMs, totalMs, totalMs-resp.GpuMs)
	}
}

func main() {
	flag.Parse()
	if (*phasePolicy != "natural" && *phasePolicy != "assigned") || (*openLoop && (!*admission || os.Getenv("GW_SERVICE_EVENTS") == "")) {
		log.Fatal("open-loop requires admission, service events and a valid phase policy")
	}
	if *periodMS <= 0 || *slots <= 0 || *periodMS / *slots < 1 {
		log.Fatal("period and slots must define a positive millisecond slot interval")
	}
	if path := os.Getenv("GW_SERVICE_EVENTS"); path != "" {
		var err error
		frameLog, err = os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
		if err != nil {
			log.Fatal(err)
		}
		defer frameLog.Close()
	}
	if p := os.Getenv("GW_TICKLOG"); p != "" {
		if f, e := os.Create(p); e == nil {
			tickLog = f
			defer tickLog.Close()
			log.Printf("[tick-trace] logging per-firing lines to %s", p)
		} else {
			log.Printf("[tick-trace] could not open %s: %v", p, e)
		}
	}
	// connect to the vLLM worker (gRPC); a worker that never turns healthy is
	// fatal — serving clients against a dead backend would only manufacture
	// Step errors that look like engine evidence.
	conn, err := grpc.NewClient(*worker, grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithDefaultCallOptions(grpc.MaxCallRecvMsgSize(256<<20), grpc.MaxCallSendMsgSize(256<<20)),
		grpc.WithKeepaliveParams(keepalive.ClientParameters{Time: 20 * time.Second, Timeout: 10 * time.Second}))
	if err != nil {
		log.Fatalf("dial worker: %v", err)
	}
	defer conn.Close()
	client = pb.NewInferenceClient(conn)
	ready := false
	for i := 0; i < 600 && !ready; i++ {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		h, e := client.Health(ctx, &pb.HealthRequest{})
		cancel()
		if e == nil && h.Ready {
			log.Printf("worker ready: model=%s", h.Model)
			ready = true
			break
		}
		time.Sleep(time.Second)
	}
	if !ready {
		log.Fatalf("worker at %s never became healthy", *worker)
	}
	manager = newSessionManager(*admission, time.Now().Add(time.Duration(*periodMS)*time.Millisecond/time.Duration(*slots)))
	controlCtx, stopControl := context.WithCancel(context.Background())
	defer stopControl()
	go manager.run(controlCtx)
	if *openLoop {
		go replayLoop()
	} else {
		go tickLoop()
	}

	srv := &http.Server{Addr: ":" + *port, Handler: http.HandlerFunc(handle)}
	go func() {
		log.Printf("[conveyor-gateway] WS on :%s period=%dms slots=%d output_cap=%d -> worker %s",
			*port, *periodMS, *slots, *outputTokenCap, *worker)
		if e := srv.ListenAndServe(); e != nil && e != http.ErrServerClosed {
			log.Fatalf("listen: %v", e)
		}
	}()
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	<-sig
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	srv.Shutdown(ctx)
}
