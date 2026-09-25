package main

import (
	"fmt"
	"testing"
	"time"
)

func testSession(id uint64) *Session {
	return &Session{id: id, alive: true, connectedAt: time.Now(), slot: -1}
}

func TestQueueWaitsForConfirmedCleanup(t *testing.T) {
	m := newSessionManager(true, time.Now())
	occupied, canRelease := false, false
	m.admit = func(s *Session) (bool, int, string, error) {
		if occupied {
			return false, 0, "gpu_capacity", nil
		}
		occupied = true
		return true, 2, "", nil
	}
	m.release = func(s *Session) error {
		if !canRelease {
			return fmt.Errorf("copy still in flight")
		}
		occupied = false
		return nil
	}
	a, b := testSession(1), testSession(2)
	m.enqueue(a)
	m.enqueue(b)
	if !m.advance() || !a.admitted || a.slot != 2 {
		t.Fatal("first session not admitted")
	}
	if m.advance() || b.admitted {
		t.Fatal("capacity refusal did not queue")
	}
	m.close(a)
	if m.advance() || b.admitted {
		t.Fatal("unconfirmed cleanup reused capacity")
	}
	canRelease = true
	if !m.advance() || !m.advance() || !b.admitted {
		t.Fatal("queue did not resume after cleanup")
	}
	m.close(a)
	if len(m.closing) != 0 {
		t.Fatal("duplicate close enqueued twice")
	}
}

func TestDisconnectDuringAdmissionIsReclaimed(t *testing.T) {
	m := newSessionManager(true, time.Now())
	a := testSession(1)
	m.admit = func(s *Session) (bool, int, string, error) {
		m.close(s)
		return true, 0, "", nil
	}
	released := false
	m.release = func(s *Session) error { released = true; return nil }
	m.enqueue(a)
	if !m.advance() || a.admitted {
		t.Fatal("disconnected session was published")
	}
	if !m.advance() || !released {
		t.Fatal("racing reservation leaked")
	}
}

func TestThousandQueuedSessionsDrainInFIFOOrder(t *testing.T) {
	m := newSessionManager(true, time.Now())
	var order []uint64
	m.admit = func(s *Session) (bool, int, string, error) {
		order = append(order, s.id)
		return true, int(s.id % 4), "", nil
	}
	m.release = func(s *Session) error { return nil }
	for i := 1; i <= 1000; i++ {
		m.enqueue(testSession(uint64(i)))
	}
	for m.advance() {
	}
	if len(order) != 1000 || len(m.waiting) != 0 {
		t.Fatal("queue did not drain")
	}
	for i, id := range order {
		if id != uint64(i+1) {
			t.Fatal("FIFO order changed")
		}
	}
}
