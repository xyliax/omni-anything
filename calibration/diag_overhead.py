"""Diagnose whether HF-eager decode step time is GPU-bound or CPU-bound.

If wall-clock >> CUDA-event time, the measurement reflects Python dispatch
overhead, not the hardware, and is unusable for calibrating a real serving
engine. Also tests whether StaticCache's max_cache_len inflates per-step cost.
"""
import sys
import time
from pathlib import Path

import torch
from transformers import AutoConfig, AutoModelForCausalLM
from transformers.cache_utils import StaticCache

model_path, dev = sys.argv[1], int(sys.argv[2])
torch.cuda.set_device(dev)
cfg = AutoConfig.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path, torch_dtype=torch.float16, attn_implementation="sdpa").to(f"cuda:{dev}").eval()
d = f"cuda:{dev}"
print(f"layers={cfg.num_hidden_layers} hidden={cfg.hidden_size}")

wbytes = sum(p.numel() * p.element_size() for p in model.parameters())
print(f"weights = {wbytes/2**30:.2f} GiB -> bandwidth floor on 3090 (936GB/s) "
      f"= {wbytes/936e9*1e3:.2f} ms/decode-step")


def measure(B, ctx, maxlen, iters=30):
    cache = StaticCache(config=cfg, max_batch_size=B, max_cache_len=maxlen,
                        device=d, dtype=torch.float16)
    # fill ctx
    done = 0
    while done < ctx:
        n = min(2048, ctx - done)
        ids = torch.randint(0, cfg.vocab_size, (B, n), device=d)
        pos = torch.arange(done, done + n, device=d)
        with torch.inference_mode():
            model(input_ids=ids, past_key_values=cache, cache_position=pos, use_cache=True)
        done += n
    torch.cuda.synchronize(dev)

    ids = torch.randint(0, cfg.vocab_size, (B, 1), device=d)
    i = ctx
    for _ in range(5):
        with torch.inference_mode():
            model(input_ids=ids, past_key_values=cache,
                  cache_position=torch.tensor([i], device=d), use_cache=True)
        i += 1
    torch.cuda.synchronize(dev)

    # wall clock with sync each step
    wall = []
    for _ in range(iters):
        t0 = time.perf_counter()
        with torch.inference_mode():
            model(input_ids=ids, past_key_values=cache,
                  cache_position=torch.tensor([i], device=d), use_cache=True)
        torch.cuda.synchronize(dev)
        wall.append((time.perf_counter() - t0) * 1e3)
        i += 1

    # pure GPU time via CUDA events (no host sync between launches)
    ev0, ev1 = torch.cuda.Event(True), torch.cuda.Event(True)
    torch.cuda.synchronize(dev)
    ev0.record()
    for _ in range(iters):
        with torch.inference_mode():
            model(input_ids=ids, past_key_values=cache,
                  cache_position=torch.tensor([i], device=d), use_cache=True)
        i += 1
    ev1.record()
    torch.cuda.synchronize(dev)
    gpu_avg = ev0.elapsed_time(ev1) / iters

    # CPU-only dispatch time (no sync at all, measures python+launch)
    t0 = time.perf_counter()
    for _ in range(iters):
        with torch.inference_mode():
            model(input_ids=ids, past_key_values=cache,
                  cache_position=torch.tensor([i], device=d), use_cache=True)
        i += 1
    cpu_launch = (time.perf_counter() - t0) * 1e3 / iters
    torch.cuda.synchronize(dev)

    wall.sort()
    del cache
    torch.cuda.empty_cache()
    return wall[len(wall) // 2], gpu_avg, cpu_launch


print(f"\n{'B':>3}{'ctx':>7}{'maxlen':>8}{'wall_ms':>10}{'gpu_ms':>9}"
      f"{'cpu_launch':>12}{'verdict':>16}")
TOTAL_STEPS = 5 + 30 * 3 + 16   # warmup + three measurement loops + slack
for B, ctx, maxlen in [(1, 1024, 1024 + TOTAL_STEPS), (1, 1024, 17000),
                       (1, 4096, 4096 + TOTAL_STEPS), (4, 1024, 1024 + TOTAL_STEPS),
                       (8, 1024, 1024 + TOTAL_STEPS), (1, 8192, 8192 + TOTAL_STEPS)]:
    try:
        w, g, c = measure(B, ctx, maxlen)
    except torch.cuda.OutOfMemoryError:
        print(f"{B:>3}{ctx:>7}{maxlen:>8}{'OOM':>10}")
        torch.cuda.empty_cache()
        continue
    v = "CPU-BOUND" if c > g * 1.2 else "GPU-bound"
    print(f"{B:>3}{ctx:>7}{maxlen:>8}{w:>10.2f}{g:>9.2f}{c:>12.2f}{v:>16}")
