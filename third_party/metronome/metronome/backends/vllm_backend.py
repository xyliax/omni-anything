"""vLLM backend — Metronome driving real models on vLLM.

Each Metronome *periodic session* is served on vLLM as a growing, prefix-cached
sequence: every frame the session's resident context is prefilled (a cache hit on
the shared prefix), the new input chunk is prefilled, and ``out_tokens`` are decoded
— exactly the per-tick prefill+decode of an interaction model. vLLM owns the paged
KV and the batching; Metronome owns *which* sessions are admitted (the deadline-aware
schedulability test) and the per-tick deadline accounting.

This is real: a real model, real PagedAttention KV, real prefix-cache reuse, and the
real measured per-tick wall-clock latency.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Sequence

import numpy as np

log = logging.getLogger("metronome.vllm")

# A single engine.step() that never makes progress for this long is treated as a stuck
# request rather than spun on forever (the prototype `while pending:` loops could hang
# the whole worker if a request was evicted/aborted without finishing).
_STEP_DEADLINE_S = 120.0


def _cfg_get(cfg, name, default=None):
    """Find ``name`` on an HF config or any of its common sub-configs. Omni/VL/MoE
    checkpoints nest the text-model dims (e.g. Qwen3-Omni puts num_hidden_layers under
    ``thinker_config.text_config``), so a flat getattr returns wrong Llama-ish defaults."""
    seen = []
    stack = [cfg]
    SUBS = ("text_config", "thinker_config", "llm_config", "language_model_config",
            "language_config")
    while stack:
        c = stack.pop(0)
        if c is None or id(c) in seen:
            continue
        seen.append(id(c))
        v = getattr(c, name, None)
        if v is not None:
            return v
        for s in SUBS:
            sub = getattr(c, s, None)
            if sub is not None:
                stack.append(sub)
    return default


class VLLMBackend:
    def __init__(self, model: str, gpu_memory_utilization: float = 0.3,
                 max_model_len: int = 8192, dtype: str = "bfloat16",
                 in_frac: float = 0.5, seed: int = 0, enforce_eager: bool = True,
                 trust_remote_code: bool = False, force_decode: bool = False,
                 **extra_engine_args):
        import os
        os.environ.setdefault("VLLM_LOGGING_LEVEL", "WARNING")
        from vllm import LLMEngine, EngineArgs, SamplingParams
        self._SP = SamplingParams
        # force_decode: ignore EOS + min_tokens=max_tokens so a request generates EXACTLY
        # max_tokens, sustaining a full decode batch -> isolates the decode compute ceiling
        # (real responses EOS early, so they never stress sustained decode).
        self.force_decode = force_decode
        kw = dict(model=model, gpu_memory_utilization=gpu_memory_utilization,
                  max_model_len=max_model_len, dtype=dtype,
                  enforce_eager=enforce_eager, enable_prefix_caching=True,
                  trust_remote_code=trust_remote_code, disable_log_stats=True)
        kw.update(extra_engine_args)
        args = EngineArgs(**kw)
        self.engine = LLMEngine.from_engine_args(args)
        self.model = model
        self.max_model_len = max_model_len
        self.in_frac = in_frac
        self.rng = np.random.default_rng(seed)
        # model facts from the loaded config (traverses nested omni/VL/MoE sub-configs
        # so we get the TEXT model's real dims, not flat Llama-7B defaults)
        cfg = self.engine.model_config.hf_config
        n_heads = int(_cfg_get(cfg, "num_attention_heads", 32))
        hidden = int(_cfg_get(cfg, "hidden_size", n_heads * 128))
        self._layers = int(_cfg_get(cfg, "num_hidden_layers", 32))
        n_kv = int(_cfg_get(cfg, "num_key_value_heads", n_heads))
        head_dim = int(_cfg_get(cfg, "head_dim", hidden // max(1, n_heads)))
        # KV element size: 1 byte if vLLM is running an fp8 KV cache, else 2 (bf16/fp16).
        # cache_config lives in different places across vLLM versions (V0: engine.cache_config;
        # V1: engine.vllm_config.cache_config) — locate it defensively.
        cc = getattr(self.engine, "cache_config", None)
        if cc is None:
            vc = getattr(self.engine, "vllm_config", None)
            cc = getattr(vc, "cache_config", None) if vc is not None else None
        kv_dtype = str(getattr(cc, "cache_dtype", "auto")).lower() if cc is not None else "auto"
        kv_elem = 1 if "fp8" in kv_dtype else 2
        self._kv_bytes_per_token = 2 * n_kv * head_dim * self._layers * kv_elem
        self.vocab = int(_cfg_get(cfg, "vocab_size", 32000))
        log.info("vLLM model facts: layers=%d kv_heads=%d head_dim=%d kv_dtype=%s "
                 "=> %d B/token", self._layers, n_kv, head_dim, kv_dtype,
                 self._kv_bytes_per_token)
        # KV cache size vLLM actually reserved
        n_blocks = (getattr(cc, "num_gpu_blocks", None) or 0) if cc is not None else 0
        if n_blocks and cc is not None:
            self._hbm_kv_bytes = n_blocks * cc.block_size * self._kv_bytes_per_token
        else:
            # engine hasn't profiled blocks yet; estimate from the util fraction
            self._hbm_kv_bytes = gpu_memory_utilization * 90 * 2**30
            log.warning("num_gpu_blocks unavailable; estimating hbm_kv_bytes from util")
        self.contexts: dict[int, list] = {}
        self.last_outputs: dict[int, list] = {}   # {sid: token_ids generated this step}
        # --- real multimodal streaming-generation state (Realtime API path) ---
        self.pending_mm: dict[int, dict] = {}     # sid -> {audio, images, text, max_tokens}
        self.inflight: dict[int, str] = {}        # sid -> in-flight request id
        self._res_tok: dict[str, int] = {}        # resident rid -> tokens decoded so far
        self.gen_seen: dict[int, int] = {}        # sid -> tokens already emitted
        self.just_finished: set = set()           # sids whose response ended this frame
        self._mm_ctr = 0
        # --- STREAMING SESSIONS (incremental, no fixed window) ---
        # Per session we keep the GROWING list of audio chunks. Each frame we append the new chunk
        # and resubmit the whole list; vLLM's mm-processor cache reuses prior chunks' encoder output
        # and prefix caching reuses their LLM KV, so only the NEW chunk is encoded+prefilled. This is
        # the streaming-session primitive (TML-style) — resident minute-level context, flat per-frame
        # cost, no 8s re-encode window. Verified flat 125->150ms over 2s->60s context (30B FP8).
        self.stream_chunks: dict[int, list] = {}  # sid -> [(np.float32 audio, sr), ...] growing
        # The tokenizer is essential — without it the worker cannot detokenize model
        # output into the text/transcript the client receives. Fail loud at construction
        # rather than silently degrade every response to "".
        try:
            self._tokenizer = self.engine.get_tokenizer()
        except Exception as e:
            raise RuntimeError(
                f"VLLMBackend: could not load tokenizer for {model!r}: {e}") from e
        if self._tokenizer is None:
            raise RuntimeError(f"VLLMBackend: tokenizer is None for {model!r}")

    # --- facts ---------------------------------------------------------------
    @property
    def kv_bytes_per_token(self) -> int: return self._kv_bytes_per_token
    @property
    def num_layers(self) -> int: return self._layers
    @property
    def hbm_kv_bytes(self) -> float: return float(self._hbm_kv_bytes)

    # --- sessions ------------------------------------------------------------
    def add_session(self, sid: int, kv_budget_tokens: int) -> None:
        # seed each session with a short distinct context
        self.contexts[sid] = [int(self.rng.integers(0, self.vocab)) for _ in range(8)]

    def set_context(self, sid: int, token_ids) -> None:
        """Seed a session with a real prompt (for correctness traces)."""
        self.contexts[sid] = list(token_ids)

    def tokenize(self, text: str):
        return self._tokenizer.encode(text) if self._tokenizer is not None else []

    def remove_session(self, sid: int) -> None:
        self.contexts.pop(sid, None)
        self.pending_mm.pop(sid, None)
        self.stream_chunks.pop(sid, None)
        rid = self.inflight.pop(sid, None)
        self.gen_seen.pop(sid, None)
        self.just_finished.discard(sid)
        if rid is not None:
            try:
                self.engine.abort_request(rid)
            except Exception:
                pass

    def context_len(self, sid: int) -> int:
        return len(self.contexts.get(sid, []))

    # --- engine drain helper -------------------------------------------------
    def _drain(self, pending: set, collect) -> None:
        """Step the engine until every rid in ``pending`` is consumed by ``collect``
        (which discards finished rids) or the step deadline elapses. The deadline turns
        a never-finishing request (evicted / aborted mid-flight) into a loud, recoverable
        error instead of an infinite spin that wedges the whole worker."""
        deadline = time.perf_counter() + _STEP_DEADLINE_S
        while pending:
            for o in self.engine.step():
                collect(o, pending)
            if pending and time.perf_counter() > deadline:
                stuck = list(pending)
                for rid in stuck:
                    try:
                        self.engine.abort_request(rid)
                    except Exception:
                        log.exception("abort of stuck rid %s failed", rid)
                pending.clear()
                raise TimeoutError(
                    f"vLLM did not finish {len(stuck)} request(s) within "
                    f"{_STEP_DEADLINE_S}s; aborted. rids={stuck[:8]}")

    # --- the frame tick ------------------------------------------------------
    def step(self, due_sids: Sequence[int], n_new: int) -> float:
        """One frame: for each due session, prefill the new input chunk over the
        cached context and decode the output tokens; return measured latency (ms).

        SYNTHETIC timing path (shaped random token streams) — used by the cost-model /
        capacity experiments, not by the production serving worker. See ``step_stream``
        / ``fd_step`` for the real serving path."""
        if not due_sids:
            return 0.0
        in_tok = int(round(n_new * self.in_frac))   # 0 => pure decode (coherent gen)
        out_tok = max(1, n_new - in_tok)
        added = []   # (sid, rid, chunk)
        pending = set()
        t0 = time.perf_counter()
        for sid in due_sids:
            ctx = self.contexts[sid]
            chunk = [int(self.rng.integers(0, self.vocab)) for _ in range(in_tok)]
            prompt_ids = (ctx + chunk)[-(self.max_model_len - out_tok):]
            rid = f"{sid}-{len(ctx)}"
            self.engine.add_request(
                rid, {"prompt_token_ids": prompt_ids},
                self._SP(max_tokens=out_tok, min_tokens=out_tok, temperature=0.0,
                         ignore_eos=True))
            added.append((sid, rid, chunk)); pending.add(rid)
        gen = {}
        def _c(o, pend):
            if o.finished and o.request_id in pend:
                gen[o.request_id] = list(o.outputs[0].token_ids)
                pend.discard(o.request_id)
        self._drain(pending, _c)
        t1 = time.perf_counter()
        # advance each session's resident context: prior + input chunk + decoded
        self.last_outputs = {}
        for sid, rid, chunk in added:
            out = gen.get(rid, [0] * out_tok)
            self.last_outputs[sid] = list(out)
            self.contexts[sid] = self.contexts[sid] + chunk + out
            if len(self.contexts[sid]) > self.max_model_len:
                self.contexts[sid] = self.contexts[sid][-self.max_model_len:]
        return (t1 - t0) * 1000.0

    # --- real multimodal streaming generation (OpenAI Realtime API path) -----
    @property
    def supports_multimodal(self) -> bool:
        return True

    def set_input(self, sid: int, audio=None, images=None, text: str = "",
                  max_tokens: int = 128) -> None:
        """Queue a real multimodal user turn (audio + image(s) + text) for a session.
        Consumed on the next ``step_stream`` as one real vLLM request with
        ``multi_modal_data`` — the model actually sees the audio and the image.

        Validates input shape/type and raises ``ValueError`` on malformed turns so a bad
        client request fails its own session loudly instead of corrupting the batch."""
        if audio is not None:
            # accept (np.ndarray, sample_rate) or a bare 1-D float array
            if isinstance(audio, tuple):
                if len(audio) != 2:
                    raise ValueError(f"sid {sid}: audio tuple must be (samples, sr)")
                samples, sr = audio
                if not isinstance(int(sr), int) or int(sr) <= 0:
                    raise ValueError(f"sid {sid}: bad sample rate {sr!r}")
                samples = np.asarray(samples)
            else:
                samples = np.asarray(audio)
            if samples.ndim != 1 or samples.size == 0:
                raise ValueError(f"sid {sid}: audio must be a non-empty 1-D array, "
                                 f"got shape {samples.shape}")
        imgs = images or []
        if imgs and not isinstance(imgs, (list, tuple)):
            raise ValueError(f"sid {sid}: images must be a list, got {type(imgs)}")
        if int(max_tokens) <= 0 or int(max_tokens) > self.max_model_len:
            raise ValueError(f"sid {sid}: max_tokens {max_tokens} out of (0, "
                             f"{self.max_model_len}]")
        self.pending_mm[sid] = dict(audio=audio, images=list(imgs),
                                    text=text or "", max_tokens=int(max_tokens))

    def _mm_prompt(self, inp: dict):
        """Build the model-specific prompt with the right audio/image placeholders and
        the matching ``multi_modal_data`` dict. Supports Qwen3-Omni, Qwen2.5-Omni, MiniCPM-o."""
        has_a = inp.get("audio") is not None
        imgs = inp.get("images") or []
        has_i = len(imgs) > 0
        text = inp.get("text", "")
        m = (self.model or "").lower()
        mm = {}
        if has_a:
            mm["audio"] = [inp["audio"]]            # (np.ndarray, sample_rate)
        if has_i:
            mm["image"] = list(imgs)
        if "qwen3" in m and "omni" in m:
            # Qwen3-Omni uses different placeholder tokens than Qwen2.5-Omni
            ph = ""
            if has_i:
                ph += "<|vision_start|><|image_pad|><|vision_end|>"
            if has_a:
                ph += "<|audio_start|><|audio_pad|><|audio_end|>"
            prompt = ("<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n"
                      f"<|im_start|>user\n{ph}{text}<|im_end|>\n<|im_start|>assistant\n")
        elif "omni" in m or "qwen2.5-omni" in m or "qwen2_5omni" in m:
            ph = ""
            if has_i:
                ph += "<|vision_bos|><|IMAGE|><|vision_eos|>"
            if has_a:
                ph += "<|audio_bos|><|AUDIO|><|audio_eos|>"
            prompt = ("<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n"
                      f"<|im_start|>user\n{ph}{text}<|im_end|>\n<|im_start|>assistant\n")
        elif "minicpm" in m:
            ph = ""
            if has_i:
                ph += "(<image>./</image>)\n"
            if has_a:
                ph += "(<audio>./</audio>)\n"        # vLLM MiniCPMO audio_pattern
            # MiniCPM-o 4.5 has a Qwen3 backbone with thinking mode; disable it so the
            # answer isn't buried in a <think> block that the token cap truncates.
            prompt = (f"<|im_start|>user\n{ph}{text} /no_think<|im_end|>\n"
                      f"<|im_start|>assistant\n")
        else:  # generic chat fallback (text only)
            prompt = f"<|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant\n"
        return prompt, mm

    def fd_step(self, sid_audio: dict, tpt: int) -> float:
        """CONTINUOUS full-duplex frame: for each session, prefill its (windowed) audio and decode
        `tpt` output tokens as ONE batched pass — the real-audio per-frame cost. Returns ms and
        fills last_outputs. Fresh request per frame (the model re-attends the recent audio window;
        vLLM has no incremental mm-KV, so this re-encodes the window — the honest cost)."""
        import time as _t
        t0 = _t.perf_counter()
        self.last_outputs = {}
        added = {}
        for sid, audsr in sid_audio.items():
            prompt, mm = self._mm_prompt({"audio": audsr, "text": "", "images": []})
            rid = f"fd-{sid}-{self._mm_ctr}"; self._mm_ctr += 1
            req = {"prompt": prompt}
            if mm:
                req["multi_modal_data"] = mm
            self.engine.add_request(rid, req, self._SP(
                max_tokens=int(tpt), min_tokens=int(tpt), ignore_eos=True, temperature=0.0))
            added[rid] = sid
        pending = set(added)
        gen = {}
        def _c(o, pend):
            if o.request_id in pend and o.finished:
                gen[added[o.request_id]] = list(o.outputs[0].token_ids)
                pend.discard(o.request_id)
        self._drain(pending, _c)
        self.last_outputs = gen
        return (_t.perf_counter() - t0) * 1000.0

    def fd_step_stream(self, sid_audio: dict, tpt: int, max_ctx_chunks: int = 0) -> float:
        """STREAMING-SESSION continuous full-duplex frame (incremental, no fixed window).

        For each session, append its NEW audio chunk to a resident growing list and resubmit the
        whole list as one batched request. vLLM's mm-processor cache reuses prior chunks' encoder
        output and prefix caching reuses their LLM KV, so per frame only the NEW chunk is encoded +
        prefilled over the resident minute-level context — flat per-frame cost, unbounded context
        (no 8s re-encode). Returns ms; fills last_outputs.

        max_ctx_chunks>0 caps the resident context (drops oldest chunks) to bound KV memory; 0 = grow
        unbounded up to max_model_len. (Dropping oldest shifts the prefix so the cache re-warms once.)
        """
        import time as _t
        t0 = _t.perf_counter()
        self.last_outputs = {}
        added = {}
        for sid, audsr in sid_audio.items():
            lst = self.stream_chunks.setdefault(sid, [])
            lst.append(audsr)
            if max_ctx_chunks and len(lst) > max_ctx_chunks:
                del lst[: len(lst) - max_ctx_chunks]
            # one audio placeholder per resident chunk; mm_data carries the whole growing list
            m = (self.model or "").lower()
            if "qwen3" in m and "omni" in m:
                ph = "<|audio_start|><|audio_pad|><|audio_end|>"
            elif "omni" in m:
                ph = "<|audio_bos|><|AUDIO|><|audio_eos|>"
            elif "minicpm" in m:
                ph = "(<audio>./</audio>)\n"
            else:
                ph = "<|audio_start|><|audio_pad|><|audio_end|>"
            head = ("<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n"
                    "<|im_start|>user\n")
            prompt = head + ph * len(lst) + "<|im_end|>\n<|im_start|>assistant\n"
            rid = f"st-{sid}-{self._mm_ctr}"; self._mm_ctr += 1
            self.engine.add_request(rid, {"prompt": prompt,
                                          "multi_modal_data": {"audio": list(lst)}},
                                    self._SP(max_tokens=int(tpt), min_tokens=int(tpt),
                                             ignore_eos=True, temperature=0.0))
            added[rid] = sid
        t_add = (_t.perf_counter() - t0) * 1000.0   # re-submission cost (build+add_request, growing list)
        pending = set(added)
        gen = {}
        def _c(o, pend):
            if o.request_id in pend and o.finished:
                gen[added[o.request_id]] = list(o.outputs[0].token_ids)
                pend.discard(o.request_id)
        t1 = _t.perf_counter()
        self._drain(pending, _c)
        t_drain = (_t.perf_counter() - t1) * 1000.0  # compute cost (prefill new + decode)
        self.last_outputs = gen
        if os.environ.get("WK_DEBUG"):
            mx = max((len(v) for v in self.stream_chunks.values()), default=0)
            log.warning("[fdstream] chunks=%d add=%.0fms drain=%.0fms", mx, t_add, t_drain)
        return (_t.perf_counter() - t0) * 1000.0

    def step_stream(self, due_sids: Sequence[int], max_steps: int = 1) -> float:
        """One frame of REAL streaming generation over the due sessions. Enqueues any
        pending multimodal input as a real request, advances decoding ``max_steps``
        tokens, and records the *new* tokens per session in ``last_outputs``. Sessions
        whose generation ended this frame land in ``just_finished``. Returns ms."""
        t0 = time.perf_counter()
        for sid in due_sids:
            if sid in self.pending_mm and sid not in self.inflight:
                inp = self.pending_mm.pop(sid)
                prompt, mm = self._mm_prompt(inp)
                rid = f"mm-{sid}-{self._mm_ctr}"; self._mm_ctr += 1
                req = {"prompt": prompt}
                if mm:
                    req["multi_modal_data"] = mm
                mt = int(inp.get("max_tokens", 128))
                sp = (self._SP(max_tokens=mt, min_tokens=mt, ignore_eos=True, temperature=0.0)
                      if self.force_decode else
                      self._SP(max_tokens=mt, temperature=0.0))
                self.engine.add_request(rid, req, sp)
                self.inflight[sid] = rid
                self.gen_seen[sid] = 0
        self.last_outputs = {}
        self.just_finished = set()
        if self.inflight:
            rid_to_sid = {rid: sid for sid, rid in self.inflight.items()}
            for _ in range(max(1, max_steps)):
                if not rid_to_sid:
                    break
                for o in self.engine.step():
                    sid = rid_to_sid.get(o.request_id)
                    if sid is None:
                        continue
                    toks = list(o.outputs[0].token_ids)
                    seen = self.gen_seen.get(sid, 0)
                    new = toks[seen:]
                    if new:
                        self.last_outputs.setdefault(sid, []).extend(new)
                        self.gen_seen[sid] = len(toks)
                    if o.finished:
                        self.just_finished.add(sid)
                        self.inflight.pop(sid, None)
                        rid_to_sid.pop(o.request_id, None)
        return (time.perf_counter() - t0) * 1000.0

    def is_finished(self, sid: int) -> bool:
        return sid in self.just_finished

    # --- Route A: persistent resident requests (faithful continuous batching) ---
    # A long-lived interaction session is ONE vLLM request: prefilled once at
    # admission, then decoded continuously. engine.step() does pure decode over the
    # resident batch — NO per-frame re-prefill (unlike step(), which re-submits the
    # whole context each tick). This isolates the real batched per-frame decode cost.
    def add_resident(self, sid: int, prompt_ids, max_tokens: int) -> str:
        rid = f"res-{sid}"
        self._res_tok[rid] = 0
        self.inflight[sid] = rid
        self.engine.add_request(
            rid, {"prompt_token_ids": [int(x) for x in prompt_ids]},
            self._SP(max_tokens=int(max_tokens), temperature=0.0, ignore_eos=True))
        return rid

    def _pump(self) -> list:
        """One engine.step(); update resident token counts; return rids that advanced."""
        advanced = []
        for o in self.engine.step():
            rid = o.request_id
            if rid not in self._res_tok:
                continue
            n = len(o.outputs[0].token_ids) if o.outputs else 0
            if n > self._res_tok[rid]:
                self._res_tok[rid] = n
                advanced.append(rid)
        return advanced

    def drain_prefill(self, max_steps: int = 4000) -> int:
        """Step until every resident request has emitted its first token (all prefills
        done → steady-state pure decode). Returns steps taken."""
        for s in range(1, max_steps + 1):
            self._pump()
            if self._res_tok and all(v >= 1 for v in self._res_tok.values()):
                return s
        raise RuntimeError("resident prefill did not complete")

    def tick_resident(self, n_steps: int) -> float:
        """Run n_steps decode steps over the resident batch; return elapsed ms. One frame."""
        t0 = time.perf_counter()
        for _ in range(n_steps):
            self._pump()
        return (time.perf_counter() - t0) * 1000.0

    def resident_tokens(self) -> dict:
        """Snapshot {rid: tokens decoded so far} — for the cumulative pure-decode check."""
        return dict(self._res_tok)

    def num_unfinished(self) -> int:
        """How many requests the engine still has in flight — used to verify all N resident
        sessions stayed live through the measured frames (no early finish/preemption-evict)."""
        try:
            return int(self.engine.get_num_unfinished_requests())
        except Exception:
            return -1

    def measure_ttfa(self, new_sid: int, prompt_ids, max_tokens: int,
                     max_steps: int = 8000) -> float:
        """Inject a fresh session into the running batch; return ms to its FIRST token
        — its prefill is scheduled alongside the running decodes, so this is the real
        time-to-first-audio a new caller sees under load."""
        rid = self.add_resident(new_sid, prompt_ids, max_tokens)
        t0 = time.perf_counter()
        for _ in range(max_steps):
            self._pump()
            if self._res_tok.get(rid, 0) >= 1:
                return (time.perf_counter() - t0) * 1000.0
        return float("nan")

    def reset_resident(self) -> None:
        """Abort all resident requests and clear tracking (between N sweeps). Pump the engine
        until it reports 0 unfinished so aborted requests are actually evicted (otherwise the
        running batch — and KV — accumulates across sweep points and eventually OOMs)."""
        for rid in list(self._res_tok):
            try:
                self.engine.abort_request(rid)
            except Exception:
                pass
        self._res_tok.clear()
        self.inflight.clear()
        for _ in range(50):
            try:
                if self.engine.get_num_unfinished_requests() == 0:
                    break
                self.engine.step()
            except Exception:
                break

    def generate_batch(self, inputs, max_tokens: int = 128):
        """DIRECT (offline) reference for ALL inputs in ONE batched engine pass — the fast,
        scalable version of generate_once for full-dataset parity. inputs: list of dicts
        {audio, images, text}. Returns list of decoded token-id lists, in input order."""
        rids = []
        for inp in inputs:
            prompt, mm = self._mm_prompt(dict(audio=inp.get("audio"),
                                              images=inp.get("images") or [],
                                              text=inp.get("text", "")))
            rid = f"db-{self._mm_ctr}"; self._mm_ctr += 1
            req = {"prompt": prompt}
            if mm:
                req["multi_modal_data"] = mm
            self.engine.add_request(rid, req, self._SP(max_tokens=max_tokens, temperature=0.0))
            rids.append(rid)
        gen, pending = {}, set(rids)
        def _c(o, pend):
            if o.request_id in pend and o.finished:
                gen[o.request_id] = list(o.outputs[0].token_ids)
                pend.discard(o.request_id)
        self._drain(pending, _c)
        return [gen.get(r, []) for r in rids]

    def generate_once(self, audio=None, images=None, text: str = "", max_tokens: int = 128):
        """DIRECT (offline) reference generation: one full prefill + greedy decode to
        completion, NOT through the periodic-session/frame path. Same engine, same prompt,
        so any difference vs step_stream is purely the serving path (batching/streaming).
        Returns the decoded token id list."""
        inp = dict(audio=audio, images=images or [], text=text or "", max_tokens=max_tokens)
        prompt, mm = self._mm_prompt(inp)
        rid = f"direct-{self._mm_ctr}"; self._mm_ctr += 1
        req = {"prompt": prompt}
        if mm:
            req["multi_modal_data"] = mm
        self.engine.add_request(rid, req, self._SP(max_tokens=max_tokens, temperature=0.0))
        out = {}
        def _c(o, pend):
            if o.request_id == rid and o.finished:
                out["toks"] = list(o.outputs[0].token_ids); pend.discard(rid)
        self._drain({rid}, _c)
        return out.get("toks", [])

    def detokenize(self, token_ids) -> str:
        if not token_ids:
            return ""
        try:
            return self._tokenizer.decode(list(token_ids), skip_special_tokens=True)
        except Exception:
            log.exception("detokenize failed for %d ids", len(list(token_ids)))
            return ""

    def abort(self, sid: int) -> None:
        """Abort any in-flight request for this session (cancellation / barge-in)."""
        rid = self.inflight.pop(sid, None)
        self.pending_mm.pop(sid, None)
        self.gen_seen.pop(sid, None)
        for r in (rid, f"{sid}-{len(self.contexts.get(sid, []))}"):
            if r is None:
                continue
            try:
                self.engine.abort_request(r)
            except Exception:
                pass

    def shutdown(self):
        """Abort all in-flight requests, tear down the engine, and free GPU memory."""
        eng = getattr(self, "engine", None)
        if eng is None:
            return
        # abort everything still running so vLLM releases its KV blocks
        for rid in list(self._res_tok) + list(self.inflight.values()):
            try:
                eng.abort_request(rid)
            except Exception:
                pass
        for m in ("shutdown", "stop_remote_worker_execution_loop"):
            fn = getattr(eng, m, None)
            if callable(fn):
                try:
                    fn()
                except Exception:
                    log.exception("engine.%s() during shutdown failed", m)
        try:
            del self.engine
        except Exception:
            pass
        self.engine = None
        try:
            import gc
            import torch
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            log.exception("CUDA cache cleanup during shutdown failed")
