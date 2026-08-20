// Conveyor gateway: the Metronome Realtime gateway with STAGGERED PHASE ASSIGNMENT.
//
// ORIGIN: copied from third_party/metronome/gateway-go (the pin stays untouched and is
// still built verbatim as .build/metronome-gateway for the baseline arm) and permanently
// diverged; upstream updates are not tracked. Behavioral changes vs that origin:
//  1. The single global ticker is replaced by a slot wheel: the loop wakes every
//     period/slots and serves only the sessions whose slot matches, so per-session tick
//     grids are spread uniformly across the period instead of all firing at once. The
//     wheel runs on an ABSOLUTE grid (firing k is scheduled at t0 + k*slotPeriod): sleep
//     overshoot and firing overruns are not re-anchored into the grid, so they self-correct
//     instead of accumulating (the inherited wake-and-re-anchor loop drifted ~0.5ms per
//     wake — x8 wakes per period made it ~4ms/period here).
//  2. Sessions are assigned a slot round-robin at admission (slot = arrival order mod
//     slots). Slicing instants are server-internal: any arrival pattern — including N
//     simultaneous connects — lands evenly on the wheel, and no user-visible latency
//     distribution changes (time-to-next-cut is uniform over the period regardless of
//     slot). The unused transportbench tool was dropped.
//  3. Full-duplex metrics carry take-from-stock semantics. The worker's Step returns
//     instantly from inventory, so gpu_ms no longer holds the real-time verdict: per-session
//     deadline_met is redefined as "delivered >= tpt tokens this tick" (starvation = the
//     engine fell behind; ticks before the session's first token are exempt), fdStart is set
//     once at the first staged fire (never reset, so server_ttfa_ms honestly includes the
//     one-slice pipeline lag), and starved firings are logged as gateway.log '[starve]'
//     lines for the runner's issue scan. Client-side latency p50/p99 remain meaningless
//     under this engine — latency distributions come from the trace side (per_request.log).
//  4. Per-firing trace. GW_TICKLOG=<path> appends one line per slot firing on the epoch
//     clock (exact alignment with scheduler.log, no clock pairing needed):
//     <wake_epoch> slot=<s> late_ms=<grid lateness> sample_ms=<walk+stage> grpc_ms=<Step
//     round-trip> gpu_ms=<worker-reported> n=<sessions served> deliv=<sid>:<tokens>,...
//     Empty firings log through n=0 (grid evidence); the line is written after fan-out so
//     delivered token counts are per-session facts measured at the delivery point.
//  5. Inherited paths unreachable on this repo's stack were pruned (the pin keeps them
//     for the baseline arm): the turn-based response lifecycle (response.create/cancel),
//     vision attachments (input_image.append), and the AIMD online-admission controller
//     with its admit log. This fork serves exactly one shape — full-duplex sessions on
//     the slot wheel, driven by the pinned sustained_fd client. A worker that never
//     becomes healthy is now fatal instead of silently served.
//
// Everything else is inherited: WebSocket termination, per-session audio buffering,
// one gRPC Step per firing, token fan-out.
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
)

type Session struct {
	id       uint64
	slot     int // phase slot on the tick wheel, fixed at admission
	conn     *websocket.Conn
	writeMu  sync.Mutex // gorilla allows one concurrent writer
	mu       sync.Mutex // guards the fields below
	audioBuf []byte
	sr       int32
	fullDup  bool // continuous full-duplex: process every tick from buffered audio, no turns
	fdStart  time.Time
	fdFirst  bool // first nonzero delivery seen (TTFA semantics)
	fdFull   bool // first FULL (>= tpt) delivery seen (starvation counting starts here:
	//               partial deliveries during pipeline ramp are fill, not falling behind)
	alive bool
}

var (
	upgrader = websocket.Upgrader{ReadBufferSize: 1 << 16, WriteBufferSize: 1 << 16,
		CheckOrigin: func(r *http.Request) bool { return true }}
	sessions sync.Map
	nextID   uint64
	client   pb.InferenceClient
	periodMS = flag.Int("period-ms", 1000, "tick period")
	slots    = flag.Int("slots", 8, "phase slots per tick period; sessions are round-robin assigned at admission")
	tpt      = flag.Int("tpt", 25, "tokens per tick")
	port     = flag.String("port", "8902", "ws listen port")
	worker   = flag.String("worker", "127.0.0.1:50051", "vLLM gRPC worker addr")
	tickLog  *os.File // GW_TICKLOG per-firing trace (header change 4)
)

// stepTimeout bounds one gRPC Step. Take-from-stock Steps return in
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
	s.writeMu.Lock()
	defer s.writeMu.Unlock()
	_ = s.conn.WriteJSON(v)
}

func handle(w http.ResponseWriter, r *http.Request) {
	c, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		return
	}
	id := atomic.AddUint64(&nextID, 1)
	s := &Session{id: id, slot: int((id - 1) % uint64(*slots)), conn: c, sr: 16000, alive: true}
	sessions.Store(id, s)
	defer func() {
		s.mu.Lock()
		s.alive = false
		s.mu.Unlock()
		sessions.Delete(id)
		c.Close()
	}()
	s.send(map[string]any{"type": "session.created", "session": map[string]any{"id": id}})
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
				s.audioBuf = append(s.audioBuf, raw...)
				s.mu.Unlock()
			}
		case "input_audio_buffer.commit":
			// no-op: the tick loop drains the buffer when staging the frame
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
	budgetMs := float64(*periodMS)
	t0 := time.Now()
	for k := int64(1); ; k++ {
		slot := int((k - 1) % int64(*slots))
		next := t0.Add(time.Duration(k) * slotPeriod)
		time.Sleep(time.Until(next))
		tickT0 := time.Now()
		lateMs := tickT0.Sub(next).Seconds() * 1000

		req := &pb.StepRequest{TokensPerTick: uint32(*tpt)}
		var active []*Session
		sessions.Range(func(_, v any) bool {
			s := v.(*Session)
			if s.slot != slot {
				return true
			}
			s.mu.Lock()
			defer s.mu.Unlock()
			if !s.alive || !s.fullDup {
				return true
			}
			// A first slice below ~40ms of audio yields zero encoder output tokens and
			// kills the session in the model runner (vLLM qwen2_5_omni "too short to be
			// represented"). Hold the first fire until one slot-period of audio buffered;
			// the session starts one period later on its own grid.
			if !s.fdFirst && len(s.audioBuf) < int(s.sr)*2*(*periodMS / *slots)/1000 {
				return true
			}
			if len(s.audioBuf) == 0 {
				return true
			}
			// CONTINUOUS full-duplex: sample the new audio since last tick, no turns.
			in := &pb.SessionInput{Sid: s.id, NewTurn: false, AudioPcm16: s.audioBuf,
				SampleRate: uint32(s.sr)}
			s.audioBuf = nil
			// Set once, never reset: the first slice legitimately returns no
			// tokens (take-from-stock), so resetting here every tick would make
			// server_ttfa_ms measure one gRPC round-trip instead of the true
			// audio-in -> first-token-out latency including the pipeline lag.
			if !s.fdFirst && s.fdStart.IsZero() {
				s.fdStart = time.Now()
			}
			req.Sessions = append(req.Sessions, in)
			active = append(active, s)
			return true
		})
		if len(req.Sessions) == 0 {
			tickTrace(tickT0, slot, lateMs, 0, 0, 0, nil)
			continue
		}
		sampleMs := time.Since(tickT0).Seconds() * 1000
		grpcT0 := time.Now()
		ctx, cancel := context.WithTimeout(context.Background(), stepTimeout)
		resp, err := client.Step(ctx, req)
		cancel()
		if err != nil {
			log.Printf("Step error: %v", err)
			// keep the grid evidence gap-free: an errored firing still logs
			// (n reflects staged sessions; no deliveries happened).
			tickTrace(tickT0, slot, lateMs, sampleMs, 0, 0, nil)
			continue
		}
		grpcMs := time.Since(grpcT0).Seconds() * 1000
		fanoutT0 := time.Now()
		byID := map[uint64]*pb.SessionOutput{}
		for _, o := range resp.Outputs {
			byID[o.Sid] = o
		}
		batch := uint32(len(active))
		starvedN := 0                           // sessions short-delivered this firing (take-from-stock miss)
		deliv := make([]string, 0, len(active)) // per-session delivered tokens, measured at the delivery point
		for _, s := range active {
			o := byID[s.id]
			if o == nil {
				s.mu.Lock()
				hadFull := s.fdFull
				s.mu.Unlock()
				deliv = append(deliv, fmt.Sprintf("%d:0", s.id))
				if hadFull {
					starvedN++
				}
				continue
			}
			deliv = append(deliv, fmt.Sprintf("%d:%d", s.id, len(o.Tokens)))
			s.mu.Lock()
			hadFull := s.fdFull // before this tick's update: ramp ticks are exempt below
			var fdTtfa float64
			if !s.fdFirst && len(o.Tokens) > 0 {
				s.fdFirst = true
				fdTtfa = float64(time.Since(s.fdStart).Milliseconds())
			}
			if !s.fdFull && len(o.Tokens) >= *tpt {
				s.fdFull = true
			}
			s.mu.Unlock()
			// TAKE-FROM-STOCK deadline: Step returns instantly, so gpu_ms carries no
			// real-time verdict. The property that must hold each tick is "the previous
			// slice's tokens are in stock" — short delivery means the engine fell behind.
			starved := hadFull && len(o.Tokens) < *tpt
			if starved {
				starvedN++
			}
			if o.Text != "" {
				s.send(map[string]any{"type": "response.text.delta", "delta": o.Text})
				s.send(map[string]any{"type": "response.audio_transcript.delta", "delta": o.Text})
			}
			if len(o.AudioOut) > 0 {
				s.send(map[string]any{"type": "response.audio.delta",
					"audio":       base64.StdEncoding.EncodeToString(o.AudioOut),
					"sample_rate": o.AudioSr})
			}
			s.send(map[string]any{"type": "metronome.tick", "latency_ms": resp.GpuMs,
				"budget_ms": budgetMs, "deadline_met": !starved, "batch": batch,
				"server_ttfa_ms": fdTtfa})
		}
		if starvedN > 0 {
			// One line per starved firing so the runner's issue scan catches a
			// falling-behind engine even in non-trace runs.
			log.Printf("[starve] slot=%d starved=%d/%d", slot, starvedN, len(active))
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
}

func main() {
	flag.Parse()
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
	go tickLoop()

	srv := &http.Server{Addr: ":" + *port, Handler: http.HandlerFunc(handle)}
	go func() {
		log.Printf("[conveyor-gateway] WS on :%s  tick=%dms slots=%d tpt=%d -> worker %s",
			*port, *periodMS, *slots, *tpt, *worker)
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
