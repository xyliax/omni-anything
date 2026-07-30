"""T1-T4 calibration against a REAL vLLM engine (V0 step loop).

Why vLLM and not HF-eager: HF's python decode loop costs ~34ms/step for a
1.7B model regardless of batch or context (launch-latency bound, verified in
diag_contention.py -- contended and clean GPUs give the same number while
their memory bandwidth differs 2.5x). A serving engine uses CUDA graphs and
paged attention, so calibrating on HF would inflate decode ~7x and destroy
every conclusion about the 480ms beat budget.

The V0 `LLMEngine` exposes exactly the mechanisms the simulator models:
  add_request() -> waiting queue, step() -> one scheduled batch,
  max_num_batched_tokens budget, chunked prefill, FCFS.
So each timed step() here is the same object the simulator predicts.
"""
from __future__ import annotations

import argparse
import contextlib
import gc
import json
import os
import statistics
import time
from pathlib import Path

os.environ.setdefault("VLLM_USE_V1", "0")
os.environ.setdefault("VLLM_LOGGING_LEVEL", "WARNING")


def stats(samples):
    s = sorted(samples)
    n = len(s)
    if not n:
        return {}
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


class VEngine:
    """Thin wrapper giving precise control over one engine step."""

    def __init__(self, model, max_batched=2048, max_len=8192, util=0.34,
                 prefix_caching=True, eager=False, max_seqs=64,
                 seq_len_to_capture=None):
        from vllm import EngineArgs, LLMEngine
        # vLLM only CUDA-graphs sequences up to max_seq_len_to_capture (default
        # 8192); longer ones fall back to eager and cost ~2.4x more per step.
        # Default None => cover the whole context range so the T1 curve
        # reflects attention cost rather than a graph-coverage cliff.
        cap = seq_len_to_capture or max_len
        self.args = dict(max_batched=max_batched, max_len=max_len, util=util,
                         seq_len_to_capture=cap)
        ea = EngineArgs(
            model=model, dtype="float16", gpu_memory_utilization=util,
            max_model_len=max_len, enable_chunked_prefill=True,
            max_num_batched_tokens=max_batched, enforce_eager=eager,
            enable_prefix_caching=prefix_caching, max_num_seqs=max_seqs,
            max_seq_len_to_capture=cap,
            disable_log_stats=True, swap_space=0,
        )
        self.engine = LLMEngine.from_engine_args(ea)
        self.rid = 0
        cc = self.engine.cache_config
        self.kv_tokens = cc.num_gpu_blocks * cc.block_size
        self.block = cc.block_size
        mc = self.engine.model_config
        self.n_layers = mc.hf_text_config.num_hidden_layers
        nkv = mc.hf_text_config.num_key_value_heads
        hd = getattr(mc.hf_text_config, "head_dim", None) or (
            mc.hf_text_config.hidden_size // mc.hf_text_config.num_attention_heads)
        self.kv_kb_tok = 2 * self.n_layers * nkv * hd * 2 / 1024

    # ------------------------------------------------------------- requests
    def add(self, n_prompt_tokens, max_tokens, token_offset=0):
        """Add a request with a synthetic prompt of exactly n tokens."""
        from vllm import SamplingParams, TokensPrompt
        self.rid += 1
        rid = str(self.rid)
        # deterministic but distinct token ids -> avoids accidental prefix reuse
        ids = [(token_offset + i) % 100000 + 1000 for i in range(n_prompt_tokens)]
        self.engine.add_request(
            rid, TokensPrompt(prompt_token_ids=ids),
            SamplingParams(max_tokens=max_tokens, temperature=0.0,
                           ignore_eos=True, detokenize=False))
        return rid

    def add_shared_prefix(self, prefix_ids, n_new, max_tokens):
        """Prompt = prefix (likely cached) + n_new fresh tokens."""
        from vllm import SamplingParams, TokensPrompt
        self.rid += 1
        rid = str(self.rid)
        base = 500000 + self.rid * 100003
        ids = list(prefix_ids) + [(base + i) % 100000 + 1000 for i in range(n_new)]
        self.engine.add_request(
            rid, TokensPrompt(prompt_token_ids=ids),
            SamplingParams(max_tokens=max_tokens, temperature=0.0,
                           ignore_eos=True, detokenize=False))
        return rid

    def add_ids(self, ids, max_tokens):
        """Add a request with an exact token-id list (caller owns the context).

        Used by the validation replay, where a session's context must grow
        across beats so that prefix caching gives the park/wake behaviour of a
        resident duplex session.
        """
        from vllm import SamplingParams, TokensPrompt
        self.rid += 1
        rid = str(self.rid)
        self.engine.add_request(
            rid, TokensPrompt(prompt_token_ids=list(ids)),
            SamplingParams(max_tokens=max_tokens, temperature=0.0,
                           ignore_eos=True, detokenize=False))
        return rid

    def step_timed(self):
        """One engine step; returns (elapsed_ms, outputs, sched_info)."""
        import torch
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        outs = self.engine.step()
        torch.cuda.synchronize()
        dt = (time.perf_counter() - t0) * 1e3
        return dt, outs

    def has_work(self):
        return self.engine.has_unfinished_requests()

    def drain(self, limit=100000):
        n = 0
        while self.has_work() and n < limit:
            self.engine.step()
            n += 1
        return n

    def abort_all(self):
        ids = list(self.engine.scheduler[0].waiting) if hasattr(
            self.engine, "scheduler") else []
        with contextlib.suppress(Exception):
            self.drain()

    def shutdown(self):
        import torch
        with contextlib.suppress(Exception):
            del self.engine
        gc.collect()
        torch.cuda.empty_cache()
