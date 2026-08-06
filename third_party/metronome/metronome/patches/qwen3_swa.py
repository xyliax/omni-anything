"""Runtime patch: force a sliding-window on Qwen3 TEXT attention in vLLM.

vLLM accepts the model config's `sliding_window` but Qwen3 attention never passes it to its
`Attention(...)`, so the LLM always runs full attention (verified: forcing the config does
nothing — latency keeps climbing with context, no plateau). This patch subclasses the `Attention`
symbol *as seen by* the model module so the text-LLM attention is built with
`per_layer_sliding_window=W` — bounding per-frame attention to the last W tokens.

Covers two backbones:
  * qwen3_moe.Attention — Qwen3-(Omni-)MoE text backbone.
  * qwen3.Attention     — dense Qwen3ForCausalLM used as the Qwen3-ASR *thinker*
                          (streaming-vad-asr endpoint model).
Audio/vision use their own attention classes (MMEncoderAttention / Qwen2_5_VisionAttention),
so they are untouched.

ISOLATION: this monkeypatches the in-memory class only (the installed vLLM files are NOT modified)
and is opt-in via the worker `--sliding-window-tokens` flag. vLLM forks the EngineCore subprocess,
so applying this in the worker parent BEFORE engine creation propagates to the model build.
For the spawned-subprocess case the installed general-plugin (metronome_vllm_plugin) applies the
same patch inside EngineCore via METRONOME_SWA_TOKENS.
"""
import logging

log = logging.getLogger("metronome.swa")

_MODULES = (
    "vllm.model_executor.models.qwen3_moe",
    "vllm.model_executor.models.qwen3",
)


def _patch_one(modpath: str, W: int) -> str | None:
    import importlib
    try:
        mod = importlib.import_module(modpath)
    except Exception:  # noqa: BLE001
        return None
    Orig = getattr(mod, "Attention", None)
    if Orig is None:
        return None
    if getattr(Orig, "_metronome_swa", None) == W:
        return modpath.rsplit(".", 1)[-1]

    class _SWAAttention(Orig):
        _metronome_swa = W

        def __init__(self, *args, **kwargs):
            kwargs.setdefault("per_layer_sliding_window", W)
            super().__init__(*args, **kwargs)

    mod.Attention = _SWAAttention
    return modpath.rsplit(".", 1)[-1]


def apply_qwen3_swa(window_tokens: int) -> bool:
    """Patch Qwen3 (MoE + dense) Attention to use a per-layer sliding window. Idempotent."""
    W = int(window_tokens)
    if W <= 0:
        return False
    patched = [t for m in _MODULES if (t := _patch_one(m, W))]
    if patched:
        log.info("Qwen3 text-attention patched (%s): per_layer_sliding_window=%d tokens",
                 "+".join(patched), W)
    return bool(patched)
