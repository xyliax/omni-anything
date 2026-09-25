package main

import (
	"testing"
	"time"
)

func TestReplayKeepsFractionalSourceClockAndLateFrameDeadline(t *testing.T) {
	oldPeriod, oldSlots, oldPolicy := *periodMS, *slots, *phasePolicy
	defer func() { *periodMS, *slots, *phasePolicy = oldPeriod, oldSlots, oldPolicy }()
	*periodMS, *slots, *phasePolicy = 2000, 4, "natural"
	epoch := time.Unix(100, 0)
	source := epoch.Add(173 * time.Millisecond)
	first := firstRelease(source, epoch, 0)
	if !first.Equal(source.Add(2 * time.Second)) {
		t.Fatal("natural phase was rounded")
	}
	s := &Session{alive: true, admitted: true, fullDup: true, firstRelease: first,
		inputFrames: []InputFrame{{Sequence: 2, Ready: epoch.Add(time.Minute)}}}
	if !replayDue(s).Equal(source.Add(4 * time.Second)) {
		t.Fatal("late network input moved its tick")
	}
	*phasePolicy = "assigned"
	assigned := firstRelease(source, epoch, 1)
	if !assigned.Equal(epoch.Add(2500 * time.Millisecond)) {
		t.Fatal("wrong earliest assigned tick")
	}
}

func TestOpenLoopRejectsOnceButWaitsForPlanTransition(t *testing.T) {
	old := *openLoop
	defer func() { *openLoop = old }()
	*openLoop = true
	m := newSessionManager(true, time.Now())
	calls, reason := 0, "plan_transition"
	m.admit = func(s *Session) (bool, int, string, error) { calls++; return false, 0, reason, nil }
	m.release = func(s *Session) error { return nil }
	s := testSession(1)
	m.enqueue(s)
	if m.advance() || len(m.waiting) != 1 {
		t.Fatal("transition was treated as rejection")
	}
	reason = "gpu_capacity"
	if !m.advance() || s.alive || len(m.waiting) != 0 {
		t.Fatal("infeasible arrival was queued")
	}
	for m.advance() {
	}
	if calls != 2 {
		t.Fatal("rejected session was retried")
	}
}
