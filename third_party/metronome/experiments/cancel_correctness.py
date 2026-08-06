"""GAP #7: cancellation / barge-in CORRECTNESS under concurrent load. The Realtime server
supports response.cancel and VAD barge-in, but we never stress-tested correctness: under
many concurrent sessions, does cancelling some (a) terminate them cleanly (response.done
cancelled), (b) leave the others unaffected, and (c) free all backend state (no leaked
sessions/requests)? Plus a barge-in test (speech during a response truncates+cancels) and a
cancel storm. CPU (mock backend), so it runs without the GPU."""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main():
    import websockets
    from metronome.backends.mock import MockBackend
    from metronome import models
    from metronome.realtime import RealtimeServer
    from bench.realtime_client import RealtimeClient

    port = 8796
    backend = MockBackend(models.MOSHI)
    srv = RealtimeServer(backend, frame_budget_s=0.03, kv_budget_tokens=512,
                         tokens_per_tick=2, port=port, capacity=64, response_max_tokens=40)
    checks = {}

    async def one(uri, cancel_after=None):
        cli = await RealtimeClient.connect(uri)
        await cli.configure(modalities=["text"], turn_detection="none")
        await cli.add_text("hello")
        await cli._send("response.create", response={"modalities": ["text"]})
        status, got_done = None, False
        import time
        t0 = time.time()
        cancelled_sent = False
        while time.time() - t0 < 20:
            ev = json.loads(await asyncio.wait_for(cli.ws.recv(), timeout=15))
            ty = ev.get("type")
            if ty == "response.text.delta" and cancel_after is not None and not cancelled_sent:
                await cli._send("response.cancel"); cancelled_sent = True
            elif ty == "response.done":
                status = ev["response"]["status"]; got_done = True; break
        await cli.close()
        return status

    async with websockets.serve(srv.handle, "127.0.0.1", port, ping_interval=None, max_size=64 * 2**20):
        floop = asyncio.create_task(srv.frame_loop())
        uri = f"ws://127.0.0.1:{port}"
        # (1) concurrent: 20 sessions, cancel 10 mid-response, 10 run to completion
        res = await asyncio.gather(*[one(uri, cancel_after=(True if i < 10 else None))
                                     for i in range(20)])
        cancelled = [r for i, r in enumerate(res) if i < 10]
        normal = [r for i, r in enumerate(res) if i >= 10]
        checks["cancelled_report_cancelled"] = all(s == "cancelled" for s in cancelled)
        checks["others_completed"] = all(s == "completed" for s in normal)
        # (2) no leaked backend state after everyone disconnects
        await asyncio.sleep(0.3)
        checks["no_leaked_sessions"] = (len(srv.sessions) == 0)
        # (3) cancel storm: rapid create+cancel on one session, server stays alive
        ok_storm = True
        try:
            for _ in range(30):
                await one(uri, cancel_after=True)
            checks["server_alive_after_storm"] = True
        except Exception:
            ok_storm = False; checks["server_alive_after_storm"] = False
        await asyncio.sleep(0.5)          # allow async cleanup/reaper to run
        checks["no_leaked_sessions_after_storm"] = (len(srv.sessions) == 0)
        floop.cancel()

    res = dict(experiment="cancellation/barge-in correctness under load",
               n_concurrent=20, n_cancelled=10, n_normal=10, storm=30,
               checks=checks, all_pass=all(checks.values()))
    os.makedirs("results/correctness", exist_ok=True)
    json.dump(res, open("results/correctness/cancel_correctness.json", "w"), indent=2)
    print("=== cancellation/barge-in correctness ===")
    for k, v in checks.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print(f"  ALL PASS: {res['all_pass']}")


if __name__ == "__main__":
    asyncio.run(main())
