"""The duplex voice workload as measured on this stack: hard 2 s ticks,
8 concurrent sessions, 600 s horizon.

GROWTH_TOKENS_PER_TICK = 78 is a measured value (53 audio tokens + ~25
generated per tick); it feeds capacity models, not the live client.
TOKENS_PER_TICK = 25 is the per-segment decode quota passed to the worker
and gateway.
"""

PERIOD_MS = 2000
SESSIONS = 8
DURATION_S = 600
CHUNK_MS = 20
TOKENS_PER_TICK = 25
MAX_AUDIO_CHUNKS = 64
GROWTH_TOKENS_PER_TICK = 78


def manifest(sessions: int, duration_s: int) -> dict:
    return {
        "period_ms": PERIOD_MS,
        "sessions": sessions,
        "duration_s": duration_s,
        "chunk_ms": CHUNK_MS,
        "tokens_per_tick": TOKENS_PER_TICK,
        "max_audio_chunks": MAX_AUDIO_CHUNKS,
        "growth_tokens_per_tick": GROWTH_TOKENS_PER_TICK,
    }
