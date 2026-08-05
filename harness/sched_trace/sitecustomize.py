# Injected via PYTHONPATH into every python process of the worker tree — including the
# spawned EngineCore subprocess, which is where the Scheduler actually lives (a monkeypatch
# in the front-end process would never reach it). Activates ONLY when SCHED_TRACE is set,
# so the client and any unrelated python on this host are untouched.
#
# Appends one line per engine step:
#   <unix_time> <req_id>:<ntok>[E] <req_id>:<ntok>[E] ...
# ntok = tokens scheduled for that request this step (53 = a 2s-audio chunk's prefill,
# 1 = one decode token); trailing E = this step also scheduled that request's encoder input.
# req_id carries the worker's external id as a prefix (assign_request_id appends 8 random
# chars), so lanes map straight back to sessions.
import os

if os.environ.get("SCHED_TRACE"):
    try:
        import time
        from vllm.v1.core.sched.scheduler import Scheduler

        _f = open(os.environ["SCHED_TRACE"], "a", buffering=1)
        _orig = Scheduler.schedule

        def _traced(self):
            out = _orig(self)
            try:
                nst = out.num_scheduled_tokens
                if nst:
                    enc = out.scheduled_encoder_inputs or {}
                    _f.write(f"{time.time():.6f} " + " ".join(
                        f"{r}:{n}{'E' if r in enc else ''}" for r, n in nst.items()) + "\n")
            except Exception:
                pass
            return out

        Scheduler.schedule = _traced
    except Exception:
        pass
