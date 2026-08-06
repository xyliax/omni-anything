"""Orchestrate tau-interact-mm: stand up the local user-simulator LLM as an OpenAI-
compatible vLLM server, then run the interaction benchmark against each agent model
through the Realtime API. Tears the server down at the end.
"""
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def wait_health(base_url, proc, timeout=600):
    url = base_url.rstrip("/").replace("/v1", "") + "/health"
    t0 = time.time()
    while time.time() - t0 < timeout:
        if proc.poll() is not None:
            raise RuntimeError(f"user-sim server exited early (code {proc.returncode})")
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(3)
    raise TimeoutError("user-sim server did not become healthy")


def main():
    ap = argparse.ArgumentParser()
    # Qwen3-1.7B by default: adequate for simple image-QA user simulation + assertion
    # judging, and small enough to actually land on the thrashing shared GPU (an 8B user-
    # sim makes the dual-model window ~50GiB, which co-tenants keep racing away).
    ap.add_argument("--usersim-model", default="Qwen/Qwen3-1.7B")
    ap.add_argument("--usersim-mem", type=float, default=0.10)
    ap.add_argument("--usersim-port", type=int, default=8055)
    ap.add_argument("--agents", nargs="*", default=["qwen-omni"])
    ap.add_argument("--agent-mem", type=float, default=0.28)
    ap.add_argument("--n-tasks", type=int, default=0)
    args = ap.parse_args()
    py = sys.executable
    base_url = f"http://127.0.0.1:{args.usersim_port}/v1"

    # Gate the WHOLE run on a window big enough for BOTH models (user-sim + agent), so we
    # never half-load the user-sim server and then starve the agent.
    sys.path.insert(0, ROOT)
    from bench.gpu_probe import query, wait_for_window
    total = query().mem_total_mib / 1024.0
    need = (args.usersim_mem + args.agent_mem) * total + 3.0
    # The shared GPU thrashes (co-tenants grab memory between the guard and allocation),
    # so launching the server can lose the race. Retry: re-wait for a window, relaunch,
    # until it comes up healthy.
    srv = None
    for attempt in range(1, 9):
        print(f"[tau-interact] (try {attempt}) waiting for a >= {need:.0f} GiB window",
              flush=True)
        wait_for_window(need_free_gib=need, max_util_pct=100, timeout_s=36000)
        print(f"[usersim] launching vLLM server: {args.usersim_model} "
              f"(mem={args.usersim_mem}) on :{args.usersim_port}", flush=True)
        srv = subprocess.Popen(
            [py, "-m", "vllm.entrypoints.openai.api_server", "--model", args.usersim_model,
             "--port", str(args.usersim_port), "--gpu-memory-utilization", str(args.usersim_mem),
             "--max-model-len", "4096", "--enforce-eager", "--disable-log-stats"],
            cwd=ROOT, env={**os.environ, "VLLM_LOGGING_LEVEL": "WARNING"})
        try:
            wait_health(base_url, srv, timeout=240)
            break
        except Exception as e:
            print(f"[usersim] launch failed ({e}); killing + retrying", flush=True)
            try:
                srv.kill(); srv.wait(timeout=20)
            except Exception:
                pass
            srv = None
    if srv is None:
        raise RuntimeError("user-sim server could not be brought up after retries")
    try:
        wait_health(base_url, srv)
        print("[usersim] healthy", flush=True)
        for agent in args.agents:
            agent_need = args.agent_mem * total + 1.5
            cmd = [py, "experiments/tau_interact_mm.py", "--agent-model", agent,
                   "--usersim-base-url", base_url, "--usersim-model", args.usersim_model,
                   "--gpu-mem", str(args.agent_mem), "--need-free-gib", f"{agent_need:.0f}",
                   "--max-util", "100", "--max-len", "2048"]
            if args.n_tasks:
                cmd += ["--n-tasks", str(args.n_tasks)]
            print(f"\n[agent={agent}] $ {' '.join(cmd)}", flush=True)
            for attempt in range(1, 5):           # agent can also lose the memory race
                t0 = time.time()
                r = subprocess.run(cmd, cwd=ROOT)
                print(f"[agent={agent}] (try {attempt}) exit={r.returncode} in "
                      f"{time.time()-t0:.0f}s", flush=True)
                if r.returncode == 0:
                    break
    finally:
        print("[usersim] shutting down server", flush=True)
        srv.send_signal(signal.SIGINT)
        try:
            srv.wait(timeout=20)
        except Exception:
            srv.kill()


if __name__ == "__main__":
    main()
