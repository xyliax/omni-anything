"""Is the 34ms decode step real hardware cost, or neighbour time-slicing?

Two probes, run on each GPU:
  (1) eager decode step (many small kernels -> very sensitive to time-slicing)
  (2) CUDA-graph-replayed decode step (one launch -> what vLLM actually does)

A large gap between GPUs, or between eager and graph, tells us the earlier
34ms figure is an artifact rather than the hardware's decode cost.
"""
import sys
import time

import torch
from transformers import AutoConfig, AutoModelForCausalLM
from transformers.cache_utils import StaticCache

model_path = sys.argv[1]
gpus = [int(x) for x in sys.argv[2].split(",")]
B, CTX = 1, 1024
ITERS = 50


def run(dev):
    torch.cuda.set_device(dev)
    d = f"cuda:{dev}"
    cfg = AutoConfig.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path, dtype=torch.float16, attn_implementation="sdpa").to(d).eval()
    maxlen = CTX + ITERS * 3 + 64
    cache = StaticCache(config=cfg, max_batch_size=B, max_cache_len=maxlen,
                        device=d, dtype=torch.float16)
    ids = torch.randint(0, cfg.vocab_size, (B, CTX), device=d)
    with torch.inference_mode():
        model(input_ids=ids, past_key_values=cache,
              cache_position=torch.arange(CTX, device=d), use_cache=True)
    torch.cuda.synchronize(dev)

    step_ids = torch.randint(0, cfg.vocab_size, (B, 1), device=d)
    pos = torch.tensor([CTX], device=d)

    # ---- eager
    for _ in range(10):
        with torch.inference_mode():
            model(input_ids=step_ids, past_key_values=cache,
                  cache_position=pos, use_cache=True)
    torch.cuda.synchronize(dev)
    e = []
    for _ in range(ITERS):
        t0 = time.perf_counter()
        with torch.inference_mode():
            model(input_ids=step_ids, past_key_values=cache,
                  cache_position=pos, use_cache=True)
        torch.cuda.synchronize(dev)
        e.append((time.perf_counter() - t0) * 1e3)
    e.sort()
    eager = e[len(e) // 2]

    # ---- CUDA graph capture of the same step
    graph_ms = None
    try:
        g = torch.cuda.CUDAGraph()
        s = torch.cuda.Stream(device=dev)
        s.wait_stream(torch.cuda.current_stream(dev))
        with torch.cuda.stream(s):
            for _ in range(3):
                with torch.no_grad():
                    model(input_ids=step_ids, past_key_values=cache,
                          cache_position=pos, use_cache=True)
        torch.cuda.current_stream(dev).wait_stream(s)
        torch.cuda.synchronize(dev)
        with torch.no_grad(), torch.cuda.graph(g):
            model(input_ids=step_ids, past_key_values=cache,
                  cache_position=pos, use_cache=True)
        for _ in range(10):
            g.replay()
        torch.cuda.synchronize(dev)
        gs = []
        for _ in range(ITERS):
            t0 = time.perf_counter()
            g.replay()
            torch.cuda.synchronize(dev)
            gs.append((time.perf_counter() - t0) * 1e3)
        gs.sort()
        graph_ms = gs[len(gs) // 2]
    except Exception as ex:
        graph_ms = f"ERR {type(ex).__name__}"

    # ---- raw bandwidth probe: read the weights once
    wb = sum(p.numel() * p.element_size() for p in model.parameters())
    buf = torch.empty(int(2**28), dtype=torch.float16, device=d)   # 512MiB
    torch.cuda.synchronize(dev)
    t0 = time.perf_counter()
    for _ in range(20):
        buf.sum()
    torch.cuda.synchronize(dev)
    bw = 20 * buf.numel() * 2 / ((time.perf_counter() - t0)) / 1e9

    try:
        util = torch.cuda.utilization(dev)
    except Exception:
        util = -1
    free, tot = torch.cuda.mem_get_info(dev)
    del cache, model
    torch.cuda.empty_cache()
    return {"gpu": dev, "eager_ms": round(eager, 2),
            "graph_ms": graph_ms if isinstance(graph_ms, str) else round(graph_ms, 2),
            "achieved_GBs": round(bw, 1),
            "floor_ms": round(wb / (bw * 1e9) * 1e3, 2),
            "util_pct": util, "free_GiB": round(free / 2**30, 2)}


print(f"{'gpu':>4}{'eager_ms':>10}{'graph_ms':>10}{'GB/s':>9}"
      f"{'floor_ms':>10}{'util%':>7}{'free':>8}")
for gp in gpus:
    try:
        r = run(gp)
        print(f"{r['gpu']:>4}{r['eager_ms']:>10}{str(r['graph_ms']):>10}"
              f"{r['achieved_GBs']:>9}{r['floor_ms']:>10}{r['util_pct']:>7}"
              f"{r['free_GiB']:>8.1f}")
    except Exception as ex:
        print(f"{gp:>4}  ERROR {type(ex).__name__}: {str(ex)[:80]}")
