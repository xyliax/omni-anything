"""Compute weight + KV-cache footprint for candidate models.

Purpose: decide which model the T1-T4 grid is physically feasible on, given
that we share the box and only ~9 GiB of one 3090 is free.
"""
import json
import urllib.request

MODELS = ["Qwen/Qwen3-8B", "Qwen/Qwen3-4B", "Qwen/Qwen3-1.7B"]
# T1 grid asks for these; product B*ctx is what KV must hold.
GRID_B = [1, 2, 4, 8, 16, 32]
GRID_CTX = [1024, 4096, 8192, 16384]


def cfg(mid: str) -> dict:
    url = f"https://huggingface.co/{mid}/resolve/main/config.json"
    for _ in range(4):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except Exception:
            continue
    raise RuntimeError(f"could not fetch {mid}")


def params_b(c: dict) -> float:
    """Rough param count from config (embed + layers)."""
    h, nl, vocab = c["hidden_size"], c["num_hidden_layers"], c["vocab_size"]
    inter = c["intermediate_size"]
    nkv, nq = c["num_key_value_heads"], c["num_attention_heads"]
    hd = c.get("head_dim") or h // nq
    attn = h * nq * hd + 2 * h * nkv * hd + nq * hd * h  # q,k,v,o
    mlp = 3 * h * inter
    tied = c.get("tie_word_embeddings", False)
    emb = vocab * h * (1 if tied else 2)
    return (nl * (attn + mlp) + emb) / 1e9


rows = []
for mid in MODELS:
    c = cfg(mid)
    nl, nkv = c["num_hidden_layers"], c["num_key_value_heads"]
    hd = c.get("head_dim") or c["hidden_size"] // c["num_attention_heads"]
    kv_kb = 2 * nl * nkv * hd * 2 / 1024  # K and V, fp16
    p = params_b(c)
    rows.append({"id": mid, "params_B": p, "w_GiB": p * 2 / 1.024**3,
                 "kv_KB_tok": kv_kb, "layers": nl, "n_kv": nkv, "head_dim": hd})

print(f"{'model':<18}{'params':>8}{'weights':>10}{'KV/token':>11}  geometry")
for r in rows:
    print(f"{r['id']:<18}{r['params_B']:>7.1f}B{r['w_GiB']:>9.1f}G"
          f"{r['kv_KB_tok']:>9.0f}KB  L={r['layers']} n_kv={r['n_kv']} hd={r['head_dim']}")

for budget, label in [(9.0, "9 GiB free (actual, shared box)"),
                      (23.5, "23.5 GiB (whole 3090, hypothetical)")]:
    print(f"\n=== KV token capacity @ {label} ===")
    print(f"{'model':<18}{'KV budget':>11}{'max tokens':>12}   largest feasible T1 cells")
    for r in rows:
        kv_gib = budget - r["w_GiB"] - 1.0  # 1 GiB activations/workspace
        if kv_gib <= 0:
            print(f"{r['id']:<18}{'--':>11}{'WEIGHTS DO NOT FIT':>12}")
            continue
        max_tok = int(kv_gib * 1024**2 / r["kv_KB_tok"])
        feas = [f"B{b}x{c//1024}k" for b in GRID_B for c in GRID_CTX if b * c <= max_tok]
        n_tot = len(GRID_B) * len(GRID_CTX)
        print(f"{r['id']:<18}{kv_gib:>10.1f}G{max_tok:>12,}   "
              f"{len(feas)}/{n_tot} cells; max={feas[-1] if feas else 'none'}")

print("\nNOTE: T1's largest cell B=32 x ctx=16k needs 512k tokens of KV.")
for r in rows:
    print(f"  {r['id']}: 512k tokens = {512*1024*r['kv_KB_tok']/1024**2:.1f} GiB of KV alone")
