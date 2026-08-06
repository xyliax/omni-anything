// Production Metronome Realtime gateway (Go): terminates the OpenAI-Realtime WebSocket protocol,
// buffers audio per session (goroutine-per-connection so I/O scales across cores), and runs a
// per-tick batched-sampling loop on a SEPARATE goroutine that ships each tick's batch to the
// Python/vLLM worker over gRPC and streams tokens back. Emits the same events the benchmark
// client expects (session.created/updated, response.created/text.delta/done, metronome.tick).
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
	"sync"
	"sync/atomic"
	"syscall"
	"time"

	"github.com/gorilla/websocket"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/keepalive"
	pb "metronome/gateway/pb"
)

type Response struct {
	maxTokens int32
	createdAt time.Time
	firstTok  bool
	nTokens   int32
}

type Session struct {
	id        uint64
	conn      *websocket.Conn
	writeMu   sync.Mutex // gorilla allows one concurrent writer
	mu        sync.Mutex // guards the fields below
	audioBuf  []byte
	images    [][]byte // VISION: pending encoded images to attach to the next turn/frame
	sr        int32
	mods      []string
	pendNew   bool // response.create pending -> stage as new_turn next tick
	pendCxl   bool
	resp      *Response
	fullDup   bool // continuous full-duplex: process every tick from buffered audio, no turns
	fdStart   time.Time
	fdFirst   bool
	alive     bool
}

var (
	upgrader = websocket.Upgrader{ReadBufferSize: 1 << 16, WriteBufferSize: 1 << 16,
		CheckOrigin: func(r *http.Request) bool { return true }}
	sessions sync.Map
	nextID   uint64
	client   pb.InferenceClient
	periodMS = flag.Int("period-ms", 1000, "tick period")
	tpt      = flag.Int("tpt", 25, "tokens per tick")
	port     = flag.String("port", "8902", "ws listen port")
	worker   = flag.String("worker", "127.0.0.1:50051", "vLLM gRPC worker addr")
	maxSess  = flag.Int("max-sessions", 0, "admission cap (0 = unlimited); reject WS beyond it")
	liveSess int64 // current open session count (atomic)
	// Online deadline-aware admission (Metronome): AIMD controller that DISCOVERS N* from the
	// per-frame latency feedback (no hand-set cap). Admit while latency has headroom; shed when it
	// approaches the budget. effCap is the current online estimate of N*.
	onlineAdmit = flag.Bool("online-admit", false, "online AIMD deadline-aware admission (discovers N*)")
	admitTarget = flag.Float64("admit-target", 0.7, "target per-frame latency as a fraction of budget")
	effCap      int64 = 1 << 50 // current online N* estimate (atomic); unbounded until the loop sets it

	// Per-tick admission trace (Metronome): when METRONOME_ADMITLOG is set, the tick loop appends one
	// line per tick (elapsed, live sessions, effCap=N* estimate, per-frame gpu ms, cumulative
	// admitted/rejected) so the AIMD convergence-over-time can be plotted.
	admittedTot int64
	rejectedTot int64
	admitLog    *os.File
	gwStart     = time.Now()
)

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
	// admission control: reject connections beyond the capacity cap (backpressure).
	// static cap (--max-sessions) OR the online AIMD estimate of N* (--online-admit).
	admCap := int64(0)
	if *maxSess > 0 {
		admCap = int64(*maxSess)
	}
	if *onlineAdmit {
		ec := atomic.LoadInt64(&effCap)
		if admCap == 0 || ec < admCap {
			admCap = ec
		}
	}
	if admCap > 0 && atomic.LoadInt64(&liveSess) >= admCap {
		atomic.AddInt64(&rejectedTot, 1)
		_ = c.WriteJSON(map[string]any{"type": "error",
			"error": map[string]any{"type": "server_overloaded",
				"message": "session capacity reached"}})
		c.Close()
		return
	}
	atomic.AddInt64(&admittedTot, 1)
	atomic.AddInt64(&liveSess, 1)
	id := atomic.AddUint64(&nextID, 1)
	s := &Session{id: id, conn: c, sr: 16000, mods: []string{"text"}, alive: true}
	sessions.Store(id, s)
	defer func() {
		s.mu.Lock(); s.alive = false; s.mu.Unlock()
		sessions.Delete(id)
		atomic.AddInt64(&liveSess, -1)
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
			Type     string          `json:"type"`
			Audio    string          `json:"audio"`
			Image    string          `json:"image"`  // VISION: single base64 image
			Images   []string        `json:"images"` // VISION: batch of base64 images
			Session  json.RawMessage `json:"session"`
			Response json.RawMessage `json:"response"`
		}
		if json.Unmarshal(data, &ev) != nil {
			continue
		}
		switch ev.Type {
		case "session.update":
			var cfg struct {
				Modalities []string `json:"modalities"`
				SR         int32    `json:"input_sample_rate"`
				TD         struct {
					Type string `json:"type"`
				} `json:"turn_detection"`
			}
			json.Unmarshal(ev.Session, &cfg)
			s.mu.Lock()
			if len(cfg.Modalities) > 0 {
				s.mods = cfg.Modalities
			}
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
		case "input_image.append":
			// VISION: attach one or more base64-encoded images to this session; the tick
			// loop ships them with the next turn/frame as SessionInput.images.
			var raws [][]byte
			if ev.Image != "" {
				if b, e := base64.StdEncoding.DecodeString(ev.Image); e == nil {
					raws = append(raws, b)
				}
			}
			for _, im := range ev.Images {
				if b, e := base64.StdEncoding.DecodeString(im); e == nil {
					raws = append(raws, b)
				}
			}
			if len(raws) > 0 {
				s.mu.Lock()
				s.images = append(s.images, raws...)
				s.mu.Unlock()
			}
		case "input_audio_buffer.commit":
			// no-op: the tick loop drains the buffer when staging the response
		case "response.create":
			s.mu.Lock()
			s.pendNew = true
			s.resp = &Response{maxTokens: 64, createdAt: time.Now()}
			s.mu.Unlock()
			s.send(map[string]any{"type": "response.created",
				"response": map[string]any{"status": "in_progress"}})
		case "response.cancel":
			s.mu.Lock(); s.pendCxl = true; s.mu.Unlock()
		}
	}
}

// tickLoop runs isolated from connection I/O: gather the batch, one gRPC Step, fan out tokens.
func tickLoop() {
	period := time.Duration(*periodMS) * time.Millisecond
	budgetMs := float64(*periodMS)
	last := time.Now()
	for {
		next := last.Add(period)
		time.Sleep(time.Until(next))
		last = time.Now()
		tickT0 := time.Now()

		req := &pb.StepRequest{TokensPerTick: uint32(*tpt)}
		var active []*Session
		sessions.Range(func(_, v any) bool {
			s := v.(*Session)
			s.mu.Lock()
			if s.alive && s.fullDup && (len(s.audioBuf) > 0 || len(s.images) > 0) {
				// CONTINUOUS full-duplex: sample the new audio since last tick, no turns.
				in := &pb.SessionInput{Sid: s.id, NewTurn: false, AudioPcm16: s.audioBuf,
					SampleRate: uint32(s.sr), Images: s.images}
				s.audioBuf = nil
				s.images = nil
				if !s.fdFirst {
					s.fdStart = time.Now()
				}
				req.Sessions = append(req.Sessions, in)
				active = append(active, s)
			} else if s.alive && (s.resp != nil || s.pendCxl) {
				in := &pb.SessionInput{Sid: s.id}
				cancelled := false
				if s.pendCxl {
					in.Cancel = true
					s.pendCxl = false
					s.resp = nil
					cancelled = true
				} else if s.pendNew {
					in.NewTurn = true
					in.AudioPcm16 = s.audioBuf
					in.SampleRate = uint32(s.sr)
					in.MaxTokens = uint32(s.resp.maxTokens)
					in.Images = s.images
					s.audioBuf = nil
					s.images = nil
					s.pendNew = false
				}
				req.Sessions = append(req.Sessions, in)
				if cancelled {
					// tell the client the cancelled response is done (was left hanging)
					s.send(map[string]any{"type": "response.done",
						"response": map[string]any{"status": "cancelled"}})
				} else {
					active = append(active, s)
				}
			}
			s.mu.Unlock()
			return true
		})
		if len(req.Sessions) == 0 {
			continue
		}
		sampleMs := time.Since(tickT0).Seconds() * 1000
		grpcT0 := time.Now()
		ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
		resp, err := client.Step(ctx, req)
		cancel()
		if err != nil {
			log.Printf("Step error: %v", err)
			continue
		}
		grpcMs := time.Since(grpcT0).Seconds() * 1000
		fanoutT0 := time.Now()
		byID := map[uint64]*pb.SessionOutput{}
		for _, o := range resp.Outputs {
			byID[o.Sid] = o
		}
		batch := uint32(len(active))
		over := resp.GpuMs > budgetMs
		if *onlineAdmit {
			// AIMD: discover N* online from per-frame latency. If we're over the target, the current
			// concurrency is too high -> multiplicative decrease the cap below the live count (shed on
			// next admits). If there's headroom, additively grow the cap to probe for more capacity.
			tgt := *admitTarget * budgetMs
			live := atomic.LoadInt64(&liveSess)
			if resp.GpuMs > tgt {
				nc := int64(float64(live) * 0.9)
				if nc < 1 {
					nc = 1
				}
				if nc < atomic.LoadInt64(&effCap) {
					atomic.StoreInt64(&effCap, nc)
				}
			} else if live >= atomic.LoadInt64(&effCap)-2 {
				atomic.AddInt64(&effCap, 1) // headroom + near cap -> probe higher
			}
		}
		if admitLog != nil {
			ec := atomic.LoadInt64(&effCap)
			if ec >= 1<<40 {
				ec = -1 // unbounded (controller not active / probing)
			}
			fmt.Fprintf(admitLog, "%.1f live=%d cap=%d gpu=%.1f adm=%d rej=%d batch=%d\n",
				time.Since(gwStart).Seconds(), atomic.LoadInt64(&liveSess), ec, resp.GpuMs,
				atomic.LoadInt64(&admittedTot), atomic.LoadInt64(&rejectedTot), len(active))
			admitLog.Sync()
		}
		for _, s := range active {
			o := byID[s.id]
			if o == nil {
				continue
			}
			s.mu.Lock()
			fd := s.fullDup
			r := s.resp
			var fdTtfa float64
			if fd && !s.fdFirst && len(o.Tokens) > 0 {
				s.fdFirst = true
				fdTtfa = float64(time.Since(s.fdStart).Milliseconds())
			}
			s.mu.Unlock()
			if fd { // continuous full-duplex: stream deltas + tick forever, no response.done
				if o.Text != "" {
					s.send(map[string]any{"type": "response.text.delta", "delta": o.Text})
					s.send(map[string]any{"type": "response.audio_transcript.delta", "delta": o.Text})
				}
				if len(o.AudioOut) > 0 {
					s.send(map[string]any{"type": "response.audio.delta",
						"audio": base64.StdEncoding.EncodeToString(o.AudioOut),
						"sample_rate": o.AudioSr})
				}
				s.send(map[string]any{"type": "metronome.tick", "latency_ms": resp.GpuMs,
					"budget_ms": budgetMs, "deadline_met": !over, "batch": batch,
					"server_ttfa_ms": fdTtfa})
				continue
			}
			if r == nil {
				continue
			}
			var sttfa float64
			if len(o.Tokens) > 0 && !r.firstTok {
				r.firstTok = true
				sttfa = float64(time.Since(r.createdAt).Milliseconds())
			}
			if o.Text != "" {
				s.send(map[string]any{"type": "response.text.delta", "delta": o.Text})
				s.send(map[string]any{"type": "response.audio_transcript.delta", "delta": o.Text})
			}
			if len(o.AudioOut) > 0 {
				s.send(map[string]any{"type": "response.audio.delta",
					"audio": base64.StdEncoding.EncodeToString(o.AudioOut),
					"sample_rate": o.AudioSr})
			}
			s.send(map[string]any{"type": "metronome.tick", "latency_ms": resp.GpuMs,
				"budget_ms": budgetMs, "deadline_met": !over, "batch": batch,
				"server_ttfa_ms": sttfa})
			r.nTokens += int32(len(o.Tokens))
			if o.Finished || r.nTokens >= r.maxTokens {
				s.send(map[string]any{"type": "response.done",
					"response": map[string]any{"status": "completed"}})
				s.mu.Lock(); s.resp = nil; s.mu.Unlock()
			} else if time.Since(r.createdAt) > 90*time.Second {
				// safety valve: a response that never finishes (worker/gateway desync) would
				// otherwise stream metronome.tick forever and hang the client — force it done.
				s.send(map[string]any{"type": "response.done",
					"response": map[string]any{"status": "incomplete"}})
				s.mu.Lock(); s.resp = nil; s.mu.Unlock()
			}
		}
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
	if p := os.Getenv("METRONOME_ADMITLOG"); p != "" {
		if f, e := os.Create(p); e == nil {
			admitLog = f
			defer admitLog.Close()
			log.Printf("[admit-trace] logging per-tick admission to %s", p)
		} else {
			log.Printf("[admit-trace] could not open %s: %v", p, e)
		}
	}
	// connect to the vLLM worker (gRPC), wait until healthy
	conn, err := grpc.NewClient(*worker, grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithDefaultCallOptions(grpc.MaxCallRecvMsgSize(256<<20), grpc.MaxCallSendMsgSize(256<<20)),
		grpc.WithKeepaliveParams(keepalive.ClientParameters{Time: 20 * time.Second, Timeout: 10 * time.Second}))
	if err != nil {
		log.Fatalf("dial worker: %v", err)
	}
	defer conn.Close()
	client = pb.NewInferenceClient(conn)
	for i := 0; i < 600; i++ {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		h, e := client.Health(ctx, &pb.HealthRequest{})
		cancel()
		if e == nil && h.Ready {
			log.Printf("worker ready: model=%s", h.Model)
			break
		}
		time.Sleep(time.Second)
	}
	go tickLoop()

	srv := &http.Server{Addr: ":" + *port, Handler: http.HandlerFunc(handle)}
	go func() {
		log.Printf("[go-gateway] WS on :%s  tick=%dms tpt=%d -> worker %s", *port, *periodMS, *tpt, *worker)
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
