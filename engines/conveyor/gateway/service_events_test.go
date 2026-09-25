package main

import "testing"

func TestFramesKeepSampleBoundariesWhenTickIsLate(t *testing.T) {
	old := *periodMS
	*periodMS = 2000
	defer func() { *periodMS = old }()
	s := &Session{id: 1, sr: 1000}
	// Three periods arrive before a tick; they remain three model inputs.
	s.audioBuf = make([]byte, 12000)
	for i := range s.audioBuf {
		s.audioBuf[i] = byte(i / 4000)
	}
	s.stageFrames(false)
	if len(s.inputFrames) != 3 {
		t.Fatalf("got %d frames", len(s.inputFrames))
	}
	for i, f := range s.inputFrames {
		if f.Sequence != uint64(i+1) || len(f.Audio) != 4000 || f.Audio[0] != byte(i) {
			t.Fatal("frame identity or boundary changed")
		}
	}
	s.audioBuf = []byte{4, 5}
	s.stageFrames(true)
	s.stageFrames(true)
	if len(s.inputFrames) != 4 || len(s.inputFrames[3].Audio) != 2 {
		t.Fatal("terminal input dropped or duplicated")
	}
}
