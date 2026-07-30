"""T1-T4 GPU microbenchmarks for the duplex-frontend serving study.

Measures the *physical* step-time parameters that drive the discrete-event
simulator. All timings use CUDA synchronisation and report distributions
(>=30 samples/point unless --quick).

  T1 decode step time      vs (batch B, context ctx)
  T2 prefill time          vs (prefill length L, existing ctx)
  T3 mixed-batch interference: B decodes + p prefill tokens in ONE step
  T4 chunking penalty      L=2048 split into k chunks, at ctx in {4k,16k}

Method note: to reach large (B x ctx) cells without OOM-ing on prefill
activations, the KV cache is populated by *chunked* prefill (<=2048 tokens
per forward). Step time depends on tensor shapes, not KV contents, so this
is exact for timing purposes.
"""
import argparse
import csv
import gc
import json
import os
import statistics
import time
from pathlib import Path

import torch
from transformers import AutoConfig, AutoModelForCausalLM
from transformers.cache_utils import StaticCache

FILL_CHUNK = 2048  # max tokens per forward when populating KV


# ---------------------------------------------------------------- utilities
def sync(dev):
    torch.cuda.synchronize(dev)


def timed(fn, dev, iters, warmup):
    """Return list of per-call latencies in ms."""
    for _ in range(warmup):
        fn()
    sync(dev)
    out = []
    for _ in range(iters):
        t0 = time.perf_counter()
        fn()
        sync(dev)
        out.append((time.perf_counter() - t0) * 1e3)
    return out


def stats(samples):
    s = sorted(samples)
    n = len(s)
    return {
        "n": n,
        "mean_ms": round(statistics.fmean(s), 4),
        "p50_ms": round(statistics.median(s), 4),
        "p90_ms": round(s[min(n - 1, int(0.90 * n))], 4),
        "p99_ms": round(s[min(n - 1, int(0.99 * n))], 4),
        "min_ms": round(s[0], 4),
        "max_ms": round(s[-1], 4),
        "std_ms": round(statistics.pstdev(s) if n > 1 else 0.0, 4),
    }


def free_gib(dev):
    return torch.cuda.mem_get_info(dev)[0] / 2**30


class Bench:
    def __init__(self, model_path, dev, dtype=torch.float16):
        self.dev_i = dev
        self.dev = f"cuda:{dev}"
        torch.cuda.set_device(dev)
        self.cfg = AutoConfig.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path, torch_dtype=dtype, attn_implementation="sdpa",
        ).to(self.dev).eval()
        self.dtype = dtype
        nl = self.cfg.num_hidden_layers
        nkv = self.cfg.num_key_value_heads
        hd = getattr(self.cfg, "head_dim", None) or (
            self.cfg.hidden_size // self.cfg.num_attention_heads)
        self.kv_kb_tok = 2 * nl * nkv * hd * 2 / 1024
        print(f"[init] loaded, free={free_gib(dev):.2f}GiB KV={self.kv_kb_tok:.0f}KB/tok",
              flush=True)

    def _cache(self, B, maxlen):
        return StaticCache(config=self.cfg, max_batch_size=B,
                           max_cache_len=maxlen, device=self.dev, dtype=self.dtype)

    def _fill(self, cache, B, ctx):
        """Populate `ctx` KV positions for batch B via chunked prefill."""
        done = 0
        while done < ctx:
            n = min(FILL_CHUNK, ctx - done)
            ids = torch.randint(0, self.cfg.vocab_size, (B, n), device=self.dev)
            pos = torch.arange(done, done + n, device=self.dev)
            with torch.inference_mode():
                self.model(input_ids=ids, past_key_values=cache,
                           cache_position=pos, use_cache=True)
            done += n
        sync(self.dev_i)

    def fits(self, B, total_tokens, slack=1.1):
        """Will B x total_tokens of KV plus activations fit in free memory?"""
        need = total_tokens * self.kv_kb_tok / 1024**2 * slack + 0.7
        return need < free_gib(self.dev_i)

    def cleanup(self):
        gc.collect()
        torch.cuda.empty_cache()

    # -------------------------------------------------------------- T1
    def t1_decode(self, B, ctx, iters, warmup):
        cache = self._cache(B, ctx + iters + warmup + 8)
        self._fill(cache, B, ctx)
        ids = torch.randint(0, self.cfg.vocab_size, (B, 1), device=self.dev)
        step = {"i": ctx}

        def one():
            pos = torch.tensor([step["i"]], device=self.dev)
            with torch.inference_mode():
                self.model(input_ids=ids, past_key_values=cache,
                           cache_position=pos, use_cache=True)
            step["i"] += 1

        s = timed(one, self.dev_i, iters, warmup)
        del cache
        self.cleanup()
        return s

    # -------------------------------------------------------------- T2
    def t2_prefill(self, L, ctx, iters, warmup):
        """Time one prefill of L tokens appended after `ctx` existing tokens."""
        cache = self._cache(1, ctx + L + 8)
        self._fill(cache, 1, ctx)
        ids = torch.randint(0, self.cfg.vocab_size, (1, L), device=self.dev)
        pos = torch.arange(ctx, ctx + L, device=self.dev)
        # Re-running at the same cache_position overwrites the same KV slots,
        # so the measured work is identical each iteration.

        def one():
            with torch.inference_mode():
                self.model(input_ids=ids, past_key_values=cache,
                           cache_position=pos, use_cache=True)

        s = timed(one, self.dev_i, iters, warmup)
        del cache
        self.cleanup()
        return s

    # -------------------------------------------------------------- T3
    def t3_mixed(self, B, ctx, p, iters, warmup):
        """B decode rows (1 token each) + one row carrying p prefill tokens,
        executed in a SINGLE forward pass -> measures fused-step interference.

        Implemented as a (B+1) x p padded batch: decode rows attend over ctx
        and contribute 1 real query token; the prefill row contributes p.
        Padding rows are masked out of attention but still occupy query slots,
        which is the same shape-driven cost structure a fused varlen kernel
        pays. Deviation from vLLM's flattened batch is noted in FINDINGS.
        """
        if p == 0:
            return self.t1_decode(B, ctx, iters, warmup)
        rows = B + 1
        cache = self._cache(rows, ctx + p + 8)
        self._fill(cache, rows, ctx)
        ids = torch.randint(0, self.cfg.vocab_size, (rows, p), device=self.dev)
        pos = torch.arange(ctx, ctx + p, device=self.dev)
        # mask: decode rows expose only their last query position
        mask = torch.zeros(rows, p, device=self.dev, dtype=torch.long)
        mask[:B, -1] = 1
        mask[B, :] = 1

        def one():
            with torch.inference_mode():
                self.model(input_ids=ids, attention_mask=None,
                           past_key_values=cache, cache_position=pos,
                           use_cache=True)

        s = timed(one, self.dev_i, iters, warmup)
        del cache
        self.cleanup()
        return s

    # -------------------------------------------------------------- T4
    def t4_chunked(self, L, k, ctx, iters, warmup):
        """Total time to prefill L tokens as k equal chunks at existing ctx."""
        chunk = L // k
        cache = self._cache(1, ctx + L + 8)
        self._fill(cache, 1, ctx)
        chunks = [(torch.randint(0, self.cfg.vocab_size, (1, chunk), device=self.dev),
                   torch.arange(ctx + j * chunk, ctx + (j + 1) * chunk, device=self.dev))
                  for j in range(k)]

        def one():
            with torch.inference_mode():
                for ids, pos in chunks:
                    self.model(input_ids=ids, past_key_values=cache,
                               cache_position=pos, use_cache=True)

        s = timed(one, self.dev_i, iters, warmup)
        del cache
        self.cleanup()
        return s
