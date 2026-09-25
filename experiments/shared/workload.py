"""Shared offered-load constants for the current measured stack.

The selected model's output budget is a harness-configured upper bound and gateway
consumption limit. It is not a minimum delivery requirement and is not derived
from an audio playback rate: the current runners expose text output
only. ``CONTEXT_GROWTH_TOKENS_PER_PERIOD`` is a measured Qwen input-plus-output
quantity used by capacity models, not by the live client.
"""

PERIOD_MS = 2000
SESSIONS = 8
DURATION_S = 600
CHUNK_MS = 20
OUTPUT_TOKEN_CAPS = {"qwen25_omni": 25, "minicpm_o45": 8}
# Compatibility default for the Qwen-only Metronome entry point.
OUTPUT_TOKEN_CAP = OUTPUT_TOKEN_CAPS["qwen25_omni"]
MAX_AUDIO_CHUNKS = 64
CONTEXT_GROWTH_TOKENS_PER_PERIOD = 78


def output_token_cap(model_preset: str = "qwen25_omni") -> int:
    """Select the same per-period budget for generation and delivery."""
    return OUTPUT_TOKEN_CAPS[model_preset]


def manifest(sessions: int, duration_s: int, *, model_preset: str = "qwen25_omni") -> dict:
    return {
        "period_ms": PERIOD_MS,
        "sessions": sessions,
        "duration_s": duration_s,
        "chunk_ms": CHUNK_MS,
        "output_token_cap": output_token_cap(model_preset),
        "max_audio_chunks": MAX_AUDIO_CHUNKS,
        "context_growth_tokens_per_period": (
            CONTEXT_GROWTH_TOKENS_PER_PERIOD if model_preset == "qwen25_omni" else None
        ),
    }
