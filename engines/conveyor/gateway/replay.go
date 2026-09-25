package main

import "time"

// Caller holds the session lock. A late/missing network input never changes
// its original release or deadline. Empty polls only drain existing output.
func replayDue(s *Session) time.Time {
	if !s.alive || !s.admitted || !s.fullDup || s.firstRelease.IsZero() {
		return time.Time{}
	}
	period := time.Duration(*periodMS) * time.Millisecond
	if len(s.inputFrames) > 0 {
		return s.firstRelease.Add(time.Duration(s.inputFrames[0].Sequence-1) * period)
	}
	if s.ending {
		return s.drainTick
	}
	return time.Time{}
}

func firstRelease(source, epoch time.Time, slot int) time.Time {
	period := time.Duration(*periodMS) * time.Millisecond
	available := source.Add(period)
	if *phasePolicy == "natural" {
		return available
	}
	phase := epoch.Add(time.Duration(slot) * (period / time.Duration(*slots)))
	delta := available.Sub(phase)
	cycles := delta / period
	if delta%period > 0 {
		cycles++
	}
	return phase.Add(cycles * period)
}

func replayLoop() {
	for {
		now, next := time.Now(), time.Time{}
		sessions.Range(func(_, value any) bool {
			s := value.(*Session)
			s.mu.Lock()
			due := replayDue(s)
			s.mu.Unlock()
			if !due.IsZero() && !due.After(now) && (next.IsZero() || due.Before(next)) {
				next = due
			}
			return true
		})
		if next.IsZero() {
			time.Sleep(time.Millisecond)
			continue
		}
		dispatchTick(next, -1, true)
	}
}
