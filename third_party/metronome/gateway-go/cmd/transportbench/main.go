// Transport ablation client: ships an N-session per-frame audio batch to a no-op server
// over one of {grpc, zmq, uds, shm} and reports per-round-trip latency. Isolates pure
// transport + dispatch cost (the server does no GPU work), so the delta vs gRPC is exactly
// the transport tax the gateway pays every frame.
package main

import (
	"context"
	"encoding/binary"
	"flag"
	"fmt"
	"net"
	"os"
	"sort"
	"syscall"
	"time"

	"github.com/go-zeromq/zmq4"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	pb "metronome/gateway/pb"
)

const shmPath = "/dev/shm/mtb_ring"
const shmSize = 64 * 1024 * 1024

func pctl(d []float64, q float64) float64 {
	sort.Float64s(d)
	return d[int(float64(len(d)-1)*q)]
}

func reqFrame(n, chunkBytes int, audio []byte) []byte {
	buf := make([]byte, 8+n*chunkBytes)
	binary.LittleEndian.PutUint32(buf[0:], uint32(n))
	binary.LittleEndian.PutUint32(buf[4:], uint32(chunkBytes))
	for i := 0; i < n; i++ {
		copy(buf[8+i*chunkBytes:], audio)
	}
	return buf
}

func readN(c net.Conn, n int) []byte {
	b := make([]byte, n)
	off := 0
	for off < n {
		m, err := c.Read(b[off:])
		if err != nil {
			panic(err)
		}
		off += m
	}
	return b
}

func main() {
	mode := flag.String("mode", "grpc", "grpc|zmq|uds|shm")
	n := flag.Int("n", 128, "sessions")
	chunkMs := flag.Int("chunk-ms", 200, "per-frame audio ms")
	sr := flag.Int("sr", 16000, "sample rate")
	iters := flag.Int("iters", 400, "round trips")
	warm := flag.Int("warm", 50, "warmup round trips")
	grpcAddr := flag.String("grpc", "127.0.0.1:50071", "")
	zmqEp := flag.String("zmq", "ipc:///tmp/mtb_zmq", "")
	udsPath := flag.String("uds", "/tmp/mtb_uds.sock", "")
	flag.Parse()

	chunkBytes := *sr * 2 * *chunkMs / 1000
	audio := make([]byte, chunkBytes)
	for i := range audio {
		audio[i] = byte(i)
	}
	lat := make([]float64, 0, *iters)

	var rt func()

	switch *mode {
	case "grpc":
		conn, err := grpc.NewClient(*grpcAddr, grpc.WithTransportCredentials(insecure.NewCredentials()),
			grpc.WithDefaultCallOptions(grpc.MaxCallRecvMsgSize(256<<20), grpc.MaxCallSendMsgSize(256<<20)))
		if err != nil {
			panic(err)
		}
		defer conn.Close()
		cl := pb.NewInferenceClient(conn)
		req := &pb.StepRequest{TokensPerTick: 25}
		for i := 0; i < *n; i++ {
			req.Sessions = append(req.Sessions, &pb.SessionInput{Sid: uint64(i), AudioPcm16: audio, SampleRate: uint32(*sr)})
		}
		rt = func() {
			ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
			_, err := cl.Step(ctx, req)
			cancel()
			if err != nil {
				panic(err)
			}
		}

	case "zmq":
		sock := zmq4.NewReq(context.Background())
		if err := sock.Dial(*zmqEp); err != nil {
			panic(err)
		}
		defer sock.Close()
		frame := reqFrame(*n, chunkBytes, audio)
		rt = func() {
			if err := sock.Send(zmq4.NewMsg(frame)); err != nil {
				panic(err)
			}
			if _, err := sock.Recv(); err != nil {
				panic(err)
			}
		}

	case "uds":
		c, err := net.Dial("unix", *udsPath)
		if err != nil {
			panic(err)
		}
		defer c.Close()
		frame := reqFrame(*n, chunkBytes, audio)
		rt = func() {
			if _, err := c.Write(frame); err != nil {
				panic(err)
			}
			hdr := readN(c, 4)
			rn := int(binary.LittleEndian.Uint32(hdr))
			readN(c, rn*8)
		}

	case "shm":
		f, err := os.OpenFile(shmPath, os.O_RDWR, 0600)
		if err != nil {
			panic(err)
		}
		ring, err := syscall.Mmap(int(f.Fd()), 0, shmSize, syscall.PROT_READ|syscall.PROT_WRITE, syscall.MAP_SHARED)
		if err != nil {
			panic(err)
		}
		c, err := net.Dial("unix", *udsPath)
		if err != nil {
			panic(err)
		}
		defer c.Close()
		ctrl := make([]byte, 8)
		binary.LittleEndian.PutUint32(ctrl[0:], uint32(*n))
		binary.LittleEndian.PutUint32(ctrl[4:], uint32(chunkBytes))
		rt = func() {
			for i := 0; i < *n; i++ { // write audio straight into the shared ring (zero-copy on read side)
				copy(ring[i*chunkBytes:], audio)
			}
			if _, err := c.Write(ctrl); err != nil {
				panic(err)
			}
			hdr := readN(c, 4)
			rn := int(binary.LittleEndian.Uint32(hdr))
			readN(c, rn*8)
		}

	default:
		panic("bad mode")
	}

	for i := 0; i < *warm; i++ {
		rt()
	}
	for i := 0; i < *iters; i++ {
		t0 := time.Now()
		rt()
		lat = append(lat, time.Since(t0).Seconds()*1000)
	}
	payloadKB := float64(*n*chunkBytes) / 1024
	fmt.Printf("mode=%-4s N=%-3d chunk=%dms payload=%.0fKB | p50=%.3fms p99=%.3fms min=%.3fms\n",
		*mode, *n, *chunkMs, payloadKB, pctl(lat, 0.50), pctl(lat, 0.99), pctl(lat, 0.0))
}
