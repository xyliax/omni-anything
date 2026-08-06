"""Confirmed model facts for the interaction-model eval set.

Every number here traces to a primary source (the model papers / configs) as
catalogued in ``docs/RESEARCH_PLAN.md`` §6.1 and ``docs/RELATED_WORK.md`` Axis 6.
Where a number is assumed (e.g. video fps) it is flagged ``assumed=True`` and is
meant to be *swept*, not trusted.

The serving layer only needs a model's *attention shape* (which sets KV
bytes/token and the per-tick attention-read cost) and its *tick cadence* (period,
token rate). It does not need the multimodal front-end. This module is the single
source of truth for those facts, consumed by the cost model, the kernel
microbenchmark, the simulator and the admission test.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass(frozen=True)
class ModelFacts:
    """Serving-relevant facts about an interaction model.

    Attributes
    ----------
    name : str
        Short identifier.
    num_layers : int
        Transformer (temporal/backbone) layer count — each layer holds a KV slab.
    num_q_heads : int
        Query heads (sets attention compute width).
    num_kv_heads : int
        Key/value heads (sets KV size; == num_q_heads for MHA, < for GQA/MQA).
    head_dim : int
        Per-head dimension.
    hidden_dim : int
        Model hidden size (FFN/MoE input width).
    ffn_dim : int
        FFN intermediate width (per expert, for MoE).
    num_experts : int
        Total experts (1 == dense).
    active_experts : int
        Experts routed per token (== num_experts for dense).
    kv_dtype_bytes : int
        Bytes per KV element (2 == fp16/bf16, 1 == fp8).
    period_s : float
        Tick interval / frame budget in seconds (the recurring wall-clock deadline).
    tokens_per_tick : float
        New input+output tokens appended to KV per tick (drives KV growth rate).
    context_ceiling_tokens : int
        Max resident tokens the model architecture supports (KV saturation point).
    self_windowing : bool
        True if the model bounds its own context (sliding window) — the KV manager
        is then *complementary*; False (e.g. Moshi full MHA) means it is *essential*.
    attention : str
        "MHA" | "GQA" | "MQA" — descriptive.
    notes : str
        Provenance / caveats.
    assumed_fields : tuple
        Names of fields whose values are assumptions to be swept, not measured.
    """

    name: str
    num_layers: int
    num_q_heads: int
    num_kv_heads: int
    head_dim: int
    hidden_dim: int
    ffn_dim: int
    num_experts: int
    active_experts: int
    kv_dtype_bytes: int
    period_s: float
    tokens_per_tick: float
    context_ceiling_tokens: int
    self_windowing: bool
    attention: str
    notes: str = ""
    assumed_fields: tuple = ()

    # ---- derived quantities -------------------------------------------------
    @property
    def kv_bytes_per_token(self) -> int:
        """Resident KV bytes added per appended token (K and V, all layers)."""
        return 2 * self.num_kv_heads * self.head_dim * self.num_layers * self.kv_dtype_bytes

    @property
    def kv_bytes_per_token_kib(self) -> float:
        return self.kv_bytes_per_token / 1024.0

    @property
    def context_ceiling_bytes(self) -> int:
        return self.context_ceiling_tokens * self.kv_bytes_per_token

    @property
    def fill_time_s(self) -> float:
        """Wall-clock seconds to fill the context window from empty at the model's
        token rate — the time to reach the WCET plateau (§1.5)."""
        rate = self.tokens_per_tick / self.period_s
        return self.context_ceiling_tokens / rate if rate > 0 else float("inf")

    @property
    def active_params_per_token(self) -> int:
        """Rough active FFN/MoE params touched per token (sets C_fixed compute)."""
        # 2 matmuls of hidden->ffn and ffn->hidden, per active expert, per layer.
        return 2 * self.hidden_dim * self.ffn_dim * self.active_experts * self.num_layers

    def summary(self) -> dict:
        d = asdict(self)
        d.update(
            kv_bytes_per_token=self.kv_bytes_per_token,
            kv_kib_per_token=round(self.kv_bytes_per_token_kib, 2),
            context_ceiling_gib=round(self.context_ceiling_bytes / 2**30, 3),
            fill_time_min=round(self.fill_time_s / 60.0, 2),
        )
        return d


# --- The eval set (confirmed numbers; see RESEARCH_PLAN.md §6.1) -------------

MOSHI = ModelFacts(
    name="moshi",
    num_layers=32,
    num_q_heads=32,
    num_kv_heads=32,          # full MHA — no GQA grouping
    head_dim=128,
    hidden_dim=4096,
    ffn_dim=14336,            # 7B dense Llama-style FFN
    num_experts=1,
    active_experts=1,
    kv_dtype_bytes=2,         # bf16
    period_s=0.080,           # 80 ms / 12.5 Hz
    tokens_per_tick=2.0,      # text monologue + audio (fat frame ~1 MiB => ~2 tok of KV)
    context_ceiling_tokens=4096,   # 4096 frames ~= 5.46 min
    self_windowing=False,     # ESSENTIAL case: no model-level KV bounding
    attention="MHA",
    notes="Kyutai Moshi 7B temporal transformer, 32L MHA d=128, 12.5Hz, 4096-frame "
          "ceiling ~5.46min, no windowing. KV ~512KiB/token (~1MiB/frame). arXiv:2410.00037",
)

MINICPM_O = ModelFacts(
    name="minicpm-o",
    num_layers=36,
    num_q_heads=32,
    num_kv_heads=8,           # GQA (Qwen3-8B backbone)
    head_dim=128,
    hidden_dim=4096,
    ffn_dim=12288,
    num_experts=1,
    active_experts=1,
    kv_dtype_bytes=2,
    period_s=1.0,             # 1 s speak/no-speak decision
    tokens_per_tick=64.0,     # video-driven: 64 tok/frame dominates (assumed fps=1)
    context_ceiling_tokens=32768,  # Qwen3 native 32K
    self_windowing=False,     # context cap undocumented; treat as unbounded -> manager needed
    attention="GQA",
    notes="MiniCPM-o 4.5 ~9B, Qwen3-8B GQA backbone (36L, 8 KV heads, d=128). "
          "144 KiB/token. video 64tok/frame, audio 10tok/s, speech 25tok/s. arXiv:2604.27393",
    assumed_fields=("tokens_per_tick", "context_ceiling_tokens"),
)

QWEN_OMNI = ModelFacts(
    name="qwen3-omni",
    num_layers=48,
    num_q_heads=32,
    num_kv_heads=4,           # MoE GQA
    head_dim=128,
    hidden_dim=2048,
    ffn_dim=768,              # per-expert (A3B)
    num_experts=128,
    active_experts=8,
    kv_dtype_bytes=2,
    period_s=2.0,             # audio encoder = 2 s temporal blocks (seconds_per_chunk=2.0, arXiv:2503.20215)
    tokens_per_tick=50.0,     # ~25 tok/s text over a 2 s frame
    context_ceiling_tokens=8192,   # sliding window (self-bounding) — the COMPLEMENTARY case
    self_windowing=True,      # COMPLEMENTARY case: model windows itself
    attention="GQA",
    notes="Qwen3-Omni 30B-A3B MoE, Thinker-Talker, block-wise streaming + sliding-window. "
          "Self-windowing => KV manager complementary not essential. arXiv:2503.20215",
    assumed_fields=("num_layers", "num_kv_heads", "context_ceiling_tokens", "period_s"),
)

EVAL_SET = {m.name: m for m in (MOSHI, MINICPM_O, QWEN_OMNI)}


def get(name: str) -> ModelFacts:
    if name not in EVAL_SET:
        raise KeyError(f"unknown model {name!r}; known: {sorted(EVAL_SET)}")
    return EVAL_SET[name]
