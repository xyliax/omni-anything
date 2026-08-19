"""Model under test: Qwen2.5-Omni-7B pinned to the exact snapshot used by
every formal run."""

ID = "Qwen/Qwen2.5-Omni-7B"
REVISION = "ae9e1690543ffd5c0221dc27f79834d0294cba00"

# KV geometry is the thinker's: K+V x 28 layers x 4 KV heads (GQA) x head_dim
# 128 x bf16 = 57344 bytes/token (56 KiB). Cross-checked against the engine's
# own pool report in worker logs.
NUM_LAYERS = 28
NUM_KV_HEADS = 4
HEAD_DIM = 128
DTYPE_BYTES = 2
KV_BYTES_PER_TOKEN = 2 * NUM_LAYERS * NUM_KV_HEADS * HEAD_DIM * DTYPE_BYTES


def manifest() -> dict:
    return {
        "id": ID,
        "revision": REVISION,
        "kv_geometry": {
            "num_layers": NUM_LAYERS,
            "num_kv_heads": NUM_KV_HEADS,
            "head_dim": HEAD_DIM,
            "dtype_bytes": DTYPE_BYTES,
            "bytes_per_token": KV_BYTES_PER_TOKEN,
        },
    }
