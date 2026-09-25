"""Pinned model inputs and KV geometry; the default preserves the Qwen path."""

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


PRESETS = {
    'qwen25_omni': dict(id=ID, revision=REVISION, family='qwen25_omni',
                       num_layers=NUM_LAYERS, num_kv_heads=NUM_KV_HEADS, head_dim=HEAD_DIM),
    'minicpm_o45': dict(id='openbmb/MiniCPM-o-4_5',
                       revision='503e754207c94da6bb26850b4469f367c9ea3582', family='minicpm_o45',
                       num_layers=36, num_kv_heads=8, head_dim=128),
}


def manifest(preset='qwen25_omni') -> dict:
    selected = PRESETS[preset]
    return {
        'preset': preset,
        "id": selected['id'],
        "revision": selected['revision'],
        'input_adapter': selected['family'],
        'output_path': 'audio_input_text_output',
        "kv_geometry": {
            "num_layers": selected['num_layers'],
            "num_kv_heads": selected['num_kv_heads'],
            "head_dim": selected['head_dim'],
            "dtype_bytes": DTYPE_BYTES,
            "bytes_per_token": 2 * selected['num_layers'] * selected['num_kv_heads'] * selected['head_dim'] * DTYPE_BYTES,
        },
    }
