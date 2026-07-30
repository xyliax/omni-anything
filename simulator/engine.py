"""Discrete-event simulator of a vLLM-style engine serving duplex voice
sessions plus background tool-call injections.

Baseline mechanisms implemented FAITHFULLY (no opportunistic optimisation):

 M1 step loop + membership freeze: each step composes its batch at step start
    (running sequences first, then the FCFS waiting queue); once launched,
    membership is fixed for that step.
 M2 per-step token budget: decode_tokens + prefill_tokens <=
    max_num_batched_tokens; long prefills are chunked across steps, and a
    partially prefilled request stays in `running` so it keeps priority over
    newly waiting ones (vLLM V0 _schedule_chunked_prefill ordering).
 M3 session = resident resumable request: between beats a session holds no
    scheduler slot; the next beat's chunk re-enters the waiting queue
    (park/wake).
 M4 no deadline awareness: the scheduler knows nothing about the 480ms beat.
    Nothing here reads a deadline; ordering is arrival order only.
 M5 tool results are spliced back as ONE prefill request on arrival, with no
    priority and no cancellation check (current vLLM issue #3344 semantics).
 M6 step time comes from the T1-T4 calibration tables (interpolated).

Sequence life cycle, matching what the engine actually does:

    beat fires -> waiting[prefill 8 tokens, then decode m-1]
                  (the last prefill chunk samples the first token, so a beat
                   of m tokens costs 1 prefill step + m-1 decode steps)
    tool returns -> waiting[prefill L tokens, no decode]

Time advances one engine step at a time; each step's duration is looked up
from the calibration model given that step's batch composition.
"""
from __future__ import annotations

import heapq
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

BEAT_MS = 480.0
MICRO_PREFILL_TOKENS = 8


class Policy(str, Enum):
    WHOLE = "whole"        # (a) splice the entire tool result as one prefill
    CHUNKED = "chunked"    # (b) chunk it under the token budget, FCFS
    IDLE_ONLY = "idle"     # (c) only feed prefill when the engine would idle


@dataclass
class Seq:
    """One scheduled sequence: a beat's work, or a tool result being absorbed."""
    sid: int
    kind: str                 # 'beat' | 'tool'
    prefill_total: int = 0
    prefill_done: int = 0
    decode_left: int = 0
    beat_idx: int = -1
    arrival_ms: float = 0.0
    tool_id: int = -1
    started_ms: float = -1.0

    @property
    def in_prefill(self):
        return self.prefill_done < self.prefill_total

    @property
    def is_tool(self):
        return self.kind == "tool"


@dataclass
class Session:
    sid: int
    ctx: int                     # current KV length (tokens), never reclaimed
    phase_ms: float              # beat phase offset
    beat: int = 0
    misses: int = 0
    beats_done: int = 0
    wasted_tokens: int = 0       # KV computed for content that got invalidated
    invalid_ctx: int = 0         # tokens of ctx that are known-stale
    stale_splices: int = 0
    interrupts: int = 0
    beat_latencies: list = field(default_factory=list)


@dataclass
class ToolCall:
    tid: int
    sid: int
    L: int
    issued_ms: float
    return_ms: float
    cancelled: bool = False          # invalidated by an interrupt
    cancelled_ms: float = -1.0
    cancel_stage: str = ""           # in_flight | returned | spliced
    splice_start_ms: float = -1.0    # entered the queue
    splice_done_ms: float = -1.0     # KV fully computed
    spoken_ms: float = -1.0
    kv_resident_from: float = -1.0
    tokens_computed: int = 0


class Engine:
    def __init__(self, calib, n_sessions, max_batched_tokens=2048,
                 policy=Policy.WHOLE, seed=0, sim_ms=60_000,
                 tool_rate_per_min=0.0, tool_L=2048, tool_delay_ms=(1000, 10000),
                 interrupt_prob=0.0, phase="random", init_ctx=2048,
                 speak_prob=0.7, max_ctx=32768, record_steps=False,
                 kv_pool_tokens=None, max_num_seqs=256, fixed_tools=None,
                 track_beats=False):
        self.cal = calib
        self.rng = random.Random(seed)
        self.budget = max_batched_tokens
        self.max_num_seqs = max_num_seqs
        self.policy = policy
        self.sim_ms = sim_ms
        self.tool_rate = tool_rate_per_min
        self.tool_L = tool_L
        self.tool_delay = tool_delay_ms
        self.interrupt_prob = interrupt_prob
        self.speak_prob = speak_prob
        self.max_ctx = max_ctx
        self.record_steps = record_steps
        self.kv_pool_tokens = kv_pool_tokens

        self.now = 0.0
        self.waiting: list[Seq] = []      # FCFS waiting queue
        self.running: list[Seq] = []      # admitted, holds a slot this step
        self.sessions: dict[int, Session] = {}
        for i in range(n_sessions):
            ph = self.rng.uniform(0, BEAT_MS) if phase == "random" else 0.0
            self.sessions[i] = Session(sid=i, ctx=init_ctx, phase_ms=ph)

        self.tools: dict[int, ToolCall] = {}
        self._next_tid = 0
        self.timers: list[tuple[float, int, str, object]] = []
        self._tie = 0
        self.steps = 0
        self.step_log = []
        self.busy_ms = 0.0
        # under-batching accounting (S2)
        self.sum_B = 0
        self.sum_dec_tokens = 0
        self.sum_pre_tokens = 0
        self.decode_steps = 0
        self.kv_peak = 0
        self.invalid_ctx_peak = 0
        self.kv_overflow_steps = 0
        # metrics
        self.total_misses = 0
        self.total_beats = 0
        self.dropped_beats = 0       # beat fired while the previous still ran
        self.miss_events = []
        self.answer_latencies = []
        self.wasted_tokens = 0
        self.wasted_gpu_ms = 0.0
        self.stale_splice_count = 0
        self._awaiting_answer: list[ToolCall] = []
        # history of steps that carried tool prefill: (t0, t1, sids, tokens).
        # Used for blast-radius attribution: a miss is blamed on every tool
        # prefill that held the engine while that beat was waiting or running,
        # which captures head-of-line blocking as well as same-step sharing.
        self._tool_steps: list[tuple[float, float, frozenset, int]] = []
        self._live_beat: dict[int, Seq] = {}

        self.track_beats = track_beats
        self.beat_log = []
        # Deterministic injections for S1: (issue_ms, sid, L, delay_ms). Used so
        # the shock lands at a known beat instead of somewhere in a Poisson tail.
        for spec in (fixed_tools or []):
            self._sched(spec[0], "tool_fixed", spec)

        for s in self.sessions.values():
            self._sched(s.phase_ms, "beat", s.sid)
            if self.tool_rate > 0:
                self._sched(s.phase_ms + self._tool_gap(), "tool", s.sid)
            if self.interrupt_prob > 0 and self.rng.random() < self.interrupt_prob:
                self._sched(self.rng.uniform(2000, max(2001.0, self.sim_ms - 2000)),
                            "interrupt", s.sid)

    # -------------------------------------------------------------- helpers
    def _sched(self, t, kind, payload):
        self._tie += 1
        heapq.heappush(self.timers, (t, self._tie, kind, payload))

    def _tool_gap(self):
        lam = self.tool_rate / 60_000.0      # per ms
        return self.rng.expovariate(lam) if lam > 0 else float("inf")

    def _beat_tokens(self):
        """m_t: content-driven decode tokens for one beat."""
        if self.rng.random() < self.speak_prob:
            n = self.rng.randint(2, 4)       # speaking beat
        else:
            n = self.rng.randint(1, 2)       # silent / listening beat
        if self.rng.random() < 0.05:          # occasional tail
            n += self.rng.randint(2, 5)
        return n

    # ------------------------------------------------------------ main loop
    def run(self):
        while self.now < self.sim_ms:
            while self.timers and self.timers[0][0] <= self.now:
                t, _, kind, payload = heapq.heappop(self.timers)
                self._fire(t, kind, payload)

            if not self.waiting and not self.running:
                if not self.timers:
                    break
                self.now = max(self.now, self.timers[0][0])
                continue

            if not self._one_step():
                # Nothing was schedulable: IDLE_ONLY is holding tool prefill
                # back. The engine really is idle now, which is exactly the
                # window policy (c) waits for -- but only up to the next timer,
                # because a step started here must still finish before the beat
                # that timer releases can run. Feed one chunk, then re-check.
                gap = (self.timers[0][0] - self.now) if self.timers else 0.0
                if gap > 0 and self._one_step(force_idle=True):
                    continue
                if not self.timers:
                    break
                self.now = max(self.now, self.timers[0][0])
        return self.report()

    def _fire(self, t, kind, payload):
        if kind == "beat":
            s = self.sessions[payload]
            m = self._beat_tokens()
            # M4: nothing is told about the deadline; this is just new work.
            # A beat whose predecessor is still unfinished piles up behind it
            # (the engine has no notion of dropping stale audio).
            if s.sid in self._live_beat:
                self.dropped_beats += 1
            # A beat costs one prefill step (absorbs the ~8-token input chunk,
            # samples nothing) plus m decode steps -- see validation_steps.csv.
            seq = Seq(sid=s.sid, kind="beat",
                      prefill_total=MICRO_PREFILL_TOKENS,
                      decode_left=m, beat_idx=s.beat, arrival_ms=t)
            self._live_beat[s.sid] = seq
            self.waiting.append(seq)         # M3: park/wake through the queue
            s.beat += 1
            nxt = t + BEAT_MS
            if nxt < self.sim_ms:
                self._sched(nxt, "beat", s.sid)

        elif kind == "tool":
            s = self.sessions[payload]
            tid = self._next_tid
            self._next_tid += 1
            d = self.rng.uniform(*self.tool_delay)
            tc = ToolCall(tid=tid, sid=s.sid, L=self.tool_L, issued_ms=t,
                          return_ms=t + d)
            self.tools[tid] = tc
            self._sched(t + d, "tool_return", tid)
            nxt = t + self._tool_gap()
            if nxt < self.sim_ms:
                self._sched(nxt, "tool", s.sid)

        elif kind == "tool_fixed":
            issue_ms, sid, L, delay = payload
            tid = self._next_tid
            self._next_tid += 1
            tc = ToolCall(tid=tid, sid=sid, L=L, issued_ms=t, return_ms=t + delay)
            self.tools[tid] = tc
            self._sched(t + delay, "tool_return", tid)

        elif kind == "tool_return":
            tc = self.tools[payload]
            # M5: NO cancellation check. The result is queued for splicing even
            # if the session was interrupted while the call was in flight.
            self.waiting.append(Seq(sid=tc.sid, kind="tool", prefill_total=tc.L,
                                    decode_left=0, arrival_ms=t, tool_id=tc.tid))
            tc.splice_start_ms = t
            if tc.cancelled:
                self.stale_splice_count += 1
                self.sessions[tc.sid].stale_splices += 1

        elif kind == "interrupt":
            s = self.sessions[payload]
            s.interrupts += 1
            # User barge-in. Everything this session's tool calls produced is
            # now garbage: in flight, returned-but-unspliced, and already
            # spliced alike. The current system cancels nothing and reclaims
            # no KV, so we only mark, never free.
            for tc in self.tools.values():
                if tc.sid != s.sid or tc.cancelled:
                    continue
                tc.cancelled = True
                tc.cancelled_ms = t
                if tc.splice_done_ms >= 0:
                    tc.cancel_stage = "spliced"
                    s.invalid_ctx += tc.L
                elif tc.splice_start_ms >= 0:
                    tc.cancel_stage = "returned"
                else:
                    tc.cancel_stage = "in_flight"

    # ------------------------------------------------------------- one step
    def _admit(self, force_idle=False):
        """Compose this step's batch. Returns (decode_seqs, [(seq, ntok)]).

        Ordering mirrors vLLM V0 chunked-prefill scheduling: already-running
        sequences (decodes and partially absorbed prefills) are considered
        first in arrival order, then the waiting queue FCFS. Membership is
        frozen the moment this function returns (M1).
        """
        dec, pre = [], []
        dec_tok = pre_tok = 0
        n_seqs = 0

        def has_decode_work():
            return any(not q.in_prefill for q in self.running) or any(
                q.kind == "beat" for q in self.waiting)

        keep_running, keep_waiting = [], []
        for src, keep in ((self.running, keep_running), (self.waiting, keep_waiting)):
            for q in src:
                if n_seqs >= self.max_num_seqs:
                    keep.append(q)
                    continue
                if q.in_prefill:
                    remaining = q.prefill_total - q.prefill_done
                    if self.policy == Policy.IDLE_ONLY and q.is_tool and not force_idle:
                        # (c) feed the tool result only when nothing else wants
                        # the engine. Deliberately starvation-prone: that is
                        # the property this policy is being measured for.
                        if dec_tok > 0 or pre_tok > 0 or has_decode_work():
                            keep.append(q)
                            continue
                    if self.policy == Policy.WHOLE and q.is_tool:
                        # (a) status quo: the result is one prefill request,
                        # never split. If it does not fit alongside what is
                        # already in the batch it runs alone in a later step,
                        # and that step takes as long as it takes.
                        if (dec_tok + pre_tok) > 0 and remaining > (
                                self.budget - dec_tok - pre_tok):
                            keep.append(q)
                            continue
                        pre.append((q, remaining))
                        pre_tok += remaining
                        n_seqs += 1
                        continue
                    space = self.budget - dec_tok - pre_tok
                    if space <= 0:
                        keep.append(q)
                        continue
                    take = min(remaining, space)
                    pre.append((q, take))
                    pre_tok += take
                    n_seqs += 1
                else:
                    if dec_tok + pre_tok + 1 > self.budget:
                        keep.append(q)
                        continue
                    dec.append(q)
                    dec_tok += 1          # one token per decode row per step
                    n_seqs += 1
        self.running, self.waiting = keep_running, keep_waiting
        return dec, pre, dec_tok, pre_tok

    def _one_step(self, force_idle=False):
        dec, pre, dec_tok, pre_tok = self._admit(force_idle)
        if not dec and not pre:
            return False

        ctxs = [self.sessions[q.sid].ctx for q in dec]
        avg_ctx = sum(ctxs) / len(ctxs) if ctxs else (
            sum(self.sessions[q.sid].ctx for q, _ in pre) / len(pre) if pre else 2048)
        # The prefill attends over the history it is being appended to, which is
        # what makes a late splice expensive; pass it separately from the decode
        # rows' context.
        pctx = (sum(self.sessions[q.sid].ctx for q, _ in pre) / len(pre)
                if pre else avg_ctx)
        B = len(dec)
        dt = self.cal.step_ms(B=B, ctx=avg_ctx, decode_tokens=dec_tok,
                              prefill_tokens=pre_tok, prefill_ctx=pctx)
        t0 = self.now
        self.now += dt
        self.steps += 1
        self.busy_ms += dt
        self.sum_B += B
        self.sum_dec_tokens += dec_tok
        self.sum_pre_tokens += pre_tok
        if B > 0:
            self.decode_steps += 1

        kv_now = sum(s.ctx for s in self.sessions.values())
        self.kv_peak = max(self.kv_peak, kv_now)
        # Known-stale context resident right now, capped per session by the
        # context it actually holds (an interrupt does not delete the tokens).
        inv_now = sum(min(s.invalid_ctx, s.ctx) for s in self.sessions.values())
        self.invalid_ctx_peak = max(self.invalid_ctx_peak, inv_now)
        if self.kv_pool_tokens and kv_now > self.kv_pool_tokens:
            # Recorded, not modelled: past this point a real engine would
            # preempt/swap, which this simulator does not do. Reported so the
            # affected runs can be discounted instead of silently trusted.
            self.kv_overflow_steps += 1

        # GPU time spent computing KV for content an interrupt already
        # invalidated. Attributed by this step's share of prefill tokens, since
        # a mixed step also carries useful decode work.
        if pre_tok > 0:
            dead = sum(n for q, n in pre
                       if q.is_tool and self.tools[q.tool_id].cancelled)
            if dead:
                self.wasted_gpu_ms += dt * dead / pre_tok

        tool_sids = {q.sid for q, _ in pre if q.is_tool}
        if tool_sids:
            self._tool_steps.append((t0, self.now, frozenset(tool_sids),
                                     sum(n for q, n in pre if q.is_tool)))
            if len(self._tool_steps) > 40000:
                self._tool_steps = self._tool_steps[-20000:]
        if self.record_steps:
            self.step_log.append({
                "step": self.steps, "t0": round(t0, 3), "dt": round(dt, 3),
                "B": B, "dec": dec_tok, "pre": pre_tok,
                "avg_ctx": round(avg_ctx), "tool_sids": sorted(tool_sids),
            })

        # ---- completions: prefill chunks first (they only absorb input)
        for q, took in pre:
            q.prefill_done += took
            s = self.sessions[q.sid]
            s.ctx = min(self.max_ctx, s.ctx + took)
            if q.is_tool:
                tc = self.tools[q.tool_id]
                tc.tokens_computed += took
                if tc.kv_resident_from < 0:
                    tc.kv_resident_from = self.now
            if q.in_prefill:
                # M2: unfinished prefill stays running and resumes next step
                self.running.append(q)
                continue
            if q.is_tool:
                tc = self.tools[q.tool_id]
                tc.splice_done_ms = self.now
                self._awaiting_answer.append(tc)
                if tc.cancelled:
                    # KV computed for content the user already invalidated
                    self.wasted_tokens += tc.tokens_computed
                    s.wasted_tokens += tc.tokens_computed
                    s.invalid_ctx += tc.L
            else:
                # Measured (validation_steps.csv): the prefill step absorbs the
                # beat's input chunk but does NOT sample a token -- a separate
                # decode step produces the first one. So no ctx bump here.
                if q.decode_left > 0:
                    self.running.append(q)
                else:
                    self._retire_beat(q)

        for q in dec:
            s = self.sessions[q.sid]
            s.ctx = min(self.max_ctx, s.ctx + 1)
            q.decode_left -= 1
            if q.decode_left > 0:
                self.running.append(q)
            else:
                self._retire_beat(q)
        return True

    def _retire_beat(self, q):
        s = self.sessions[q.sid]
        s.beats_done += 1
        self.total_beats += 1
        lat = self.now - q.arrival_ms
        s.beat_latencies.append(lat)
        self._live_beat.pop(q.sid, None)
        if self.track_beats:
            self.beat_log.append({
                "sid": s.sid, "beat": q.beat_idx,
                "arrival_ms": round(q.arrival_ms, 2), "done_ms": round(self.now, 2),
                "latency_ms": round(lat, 2), "miss": int(lat > BEAT_MS),
                "ctx": s.ctx})
        if lat > BEAT_MS:
            s.misses += 1
            self.total_misses += 1
            blocked_by, tool_ms = set(), 0.0
            for (a, b_, sids, _tk) in self._tool_steps:
                if b_ > q.arrival_ms and a < self.now:
                    blocked_by |= sids
                    tool_ms += min(b_, self.now) - max(a, q.arrival_ms)
            self.miss_events.append({
                "t": round(self.now, 2), "sid": s.sid, "beat": q.beat_idx,
                "lateness_ms": round(lat - BEAT_MS, 2),
                "blamed_tool_sids": sorted(blocked_by - {s.sid}),
                "own_tool_involved": s.sid in blocked_by,
                "tool_ms_in_window": round(tool_ms, 2),
            })
        # A spliced tool result counts as answered at the first beat this
        # session completes after the splice landed (spec: "the moment the
        # session next speaks that content").
        if self._awaiting_answer:
            still = []
            for tc in self._awaiting_answer:
                if tc.sid == s.sid and 0 <= tc.splice_done_ms <= self.now:
                    tc.spoken_ms = self.now
                    self.answer_latencies.append({
                        "tool_id": tc.tid, "sid": tc.sid, "L": tc.L,
                        "issued_ms": round(tc.issued_ms, 2),
                        "returned_ms": round(tc.return_ms, 2),
                        "spliced_ms": round(tc.splice_done_ms, 2),
                        "spoken_ms": round(self.now, 2),
                        "answer_latency_ms": round(self.now - tc.splice_start_ms, 2),
                        "wait_for_splice_ms": round(
                            tc.splice_done_ms - tc.splice_start_ms, 2),
                        "cancelled": tc.cancelled,
                    })
                else:
                    still.append(tc)
            self._awaiting_answer = still

    # -------------------------------------------------------------- report
    def report(self):
        beats = max(1, self.total_beats)
        lat_all = sorted(l for s in self.sessions.values() for l in s.beat_latencies)
        n = len(lat_all) or 1
        # Invalidated KV is never reclaimed, so it stays resident to the end of
        # the run; residency is measured from the moment its first token landed.
        resid = [self.sim_ms - t.kv_resident_from for t in self.tools.values()
                 if t.cancelled and t.kv_resident_from >= 0]
        blast = [m for m in self.miss_events if m["blamed_tool_sids"]]
        n_sess = len(self.sessions)
        # Under-batching: an ideal scheduler would gather all N sessions into
        # one batch per beat. Phase scatter instead makes many small batches,
        # so the per-step fixed cost is paid far more often than necessary.
        ideal_steps = sum(s.beats_done for s in self.sessions.values()) / max(1, n_sess)
        answers = sorted(a["answer_latency_ms"] for a in self.answer_latencies)
        sess_miss = {s.sid: (s.misses / s.beats_done if s.beats_done else 0.0)
                     for s in self.sessions.values()}
        return {
            "steps": self.steps,
            "sim_ms": self.sim_ms,
            "utilisation": round(self.busy_ms / self.sim_ms, 4),
            "n_sessions": n_sess,
            "avg_decode_B": round(self.sum_B / max(1, self.decode_steps), 3),
            "decode_steps": self.decode_steps,
            "batch_fill_ratio": round(
                (self.sum_B / max(1, self.decode_steps)) / max(1, n_sess), 4),
            "ideal_decode_steps": round(ideal_steps, 1),
            "step_inflation_vs_ideal": round(
                self.decode_steps / max(1.0, ideal_steps), 3),
            "prefill_token_share": round(
                self.sum_pre_tokens / max(1, self.sum_pre_tokens + self.sum_dec_tokens), 4),
            "total_beats": self.total_beats,
            "total_misses": self.total_misses,
            "miss_rate": round(self.total_misses / beats, 6),
            "dropped_beats": self.dropped_beats,
            "beat_p50_ms": round(lat_all[n // 2], 2) if lat_all else 0,
            "beat_p99_ms": round(lat_all[min(n - 1, int(0.99 * n))], 2) if lat_all else 0,
            "beat_max_ms": round(lat_all[-1], 2) if lat_all else 0,
            "answer_p50_ms": answers[len(answers) // 2] if answers else None,
            "answer_p99_ms": answers[min(len(answers) - 1, int(0.99 * len(answers)))]
                             if answers else None,
            "answers_delivered": len(answers),
            "wasted_tokens": self.wasted_tokens,
            "wasted_gpu_ms": round(self.wasted_gpu_ms, 2),
            "stale_splices": self.stale_splice_count,
            "cancelled_tools": sum(1 for t in self.tools.values() if t.cancelled),
            "cancel_stages": {
                st: sum(1 for t in self.tools.values() if t.cancel_stage == st)
                for st in ("in_flight", "returned", "spliced")},
            "total_tools": len(self.tools),
            "kv_residency_ms_mean": round(sum(resid) / len(resid), 1) if resid else 0,
            "kv_residency_ms_max": round(max(resid), 1) if resid else 0,
            # Cumulative over the run: nothing is ever reclaimed, so this can
            # exceed the pool. The peak is the physically meaningful figure --
            # how much of the pool is held by known-dead context at once.
            "invalid_ctx_tokens": sum(s.invalid_ctx for s in self.sessions.values()),
            "invalid_ctx_peak_tokens": self.invalid_ctx_peak,
            "kv_peak_tokens": self.kv_peak,
            "kv_overflow_steps": self.kv_overflow_steps,
            "cross_session_misses": len(blast),
            "cross_miss_fraction": round(len(blast) / max(1, self.total_misses), 4),
            "mean_blast_sessions": round(
                sum(len(m["blamed_tool_sids"]) for m in blast) / max(1, len(blast)), 3),
            "sessions_within_1pct": sum(1 for v in sess_miss.values() if v <= 0.01),
            "answer_latencies": self.answer_latencies,
            "miss_events": self.miss_events,
            "beat_log": self.beat_log,
            "per_session": {
                s.sid: {"misses": s.misses, "beats": s.beats_done,
                        "miss_rate": round(sess_miss[s.sid], 5),
                        "ctx_final": s.ctx, "wasted": s.wasted_tokens,
                        "invalid_ctx": s.invalid_ctx, "interrupts": s.interrupts,
                        "beat_p50_ms": round(
                            sorted(s.beat_latencies)[len(s.beat_latencies) // 2], 2)
                            if s.beat_latencies else 0}
                for s in self.sessions.values()
            },
            "step_log": self.step_log,
        }
