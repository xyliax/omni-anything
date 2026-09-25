package main

import (
	"encoding/json"
	"fmt"
	"os"
	"sync"
	"time"
)

type InputFrame struct {
	Sequence uint64
	Ready    time.Time
	Audio    []byte
}

var frameLog *os.File
var frameLogMu sync.Mutex

func serviceEvent(kind string, sid, seq uint64, fields map[string]any) {
	if frameLog == nil {
		return
	}
	if fields == nil {
		fields = map[string]any{}
	}
	fields["schema_version"], fields["event"], fields["session"] = 1, kind, sid
	fields["epoch"], fields["frame"], fields["time_ns"] = 1, seq, time.Now().UnixNano()
	raw, err := json.Marshal(fields)
	if err != nil {
		panic(err)
	}
	frameLogMu.Lock()
	defer frameLogMu.Unlock()
	if _, err = fmt.Fprintln(frameLog, string(raw)); err != nil {
		panic(err)
	}
}

// Caller holds s.mu. Chunk boundaries depend on sample count, never on a late
// gateway tick. The final incomplete chunk is retained exactly once.
func (s *Session) stageFrames(final bool) {
	size := int(s.sr) * 2 * *periodMS / 1000
	for len(s.audioBuf) >= size || (final && len(s.audioBuf) > 0) {
		count := size
		if count > len(s.audioBuf) {
			count = len(s.audioBuf)
		}
		s.inputSequence++
		frame := InputFrame{Sequence: s.inputSequence, Ready: time.Now(), Audio: s.audioBuf[:count]}
		s.audioBuf = s.audioBuf[count:]
		s.inputFrames = append(s.inputFrames, frame)
		serviceEvent("input_ready", s.id, frame.Sequence, map[string]any{"samples": count / 2, "ready_ns": frame.Ready.UnixNano()})
	}
}
