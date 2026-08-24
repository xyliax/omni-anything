"""Shared offered-load constants for the current measured stack.

``OUTPUT_TOKEN_CAP`` is a harness-configured upper bound and gateway
consumption limit. It is not a minimum delivery requirement and is not derived
from an audio playback rate: the current runner exposes Thinker text output
only. ``CONTEXT_GROWTH_TOKENS_PER_PERIOD`` is a measured input-plus-output
quantity used by capacity models, not by the live client.
"""

PERIOD_MS = 2000
SESSIONS = 8
DURATION_S = 600
CHUNK_MS = 20
OUTPUT_TOKEN_CAP = 25
MAX_AUDIO_CHUNKS = 64
CONTEXT_GROWTH_TOKENS_PER_PERIOD = 78


def manifest(sessions: int, duration_s: int) -> dict:
    return {
        "period_ms": PERIOD_MS,
        "sessions": sessions,
        "duration_s": duration_s,
        "chunk_ms": CHUNK_MS,
        "output_token_cap": OUTPUT_TOKEN_CAP,
        "max_audio_chunks": MAX_AUDIO_CHUNKS,
        "context_growth_tokens_per_period": CONTEXT_GROWTH_TOKENS_PER_PERIOD,
    }
