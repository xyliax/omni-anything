"""Show (a) decode step time vs context from T1, and (b) the internal
composition of mixed steps: which request contributes prefill tokens vs decode
tokens, with the calibration pricing decomposed."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from calib_model import load_default, _interp1
from engine import Engine, BEAT_MS

ROOT = Path(__file__).parent.parent
cal = load_default(ROOT / "calibration" / "data", "Qwen3-1.7B")

print("== (a) T1 实测: 一步 decode 的时间 vs 上下文长度 ==")
t1 = {}
for r in csv.DictReader(open(ROOT / "calibration/data/T1_decode_Qwen3-1.7B.csv")):
    if r.get("p50_ms") and r.get("feasible") != "0":
        t1[(int(r["B"]), int(r["ctx"]))] = float(r["p50_ms"])
for B in (1, 8):
    xs = sorted(c for (b, c) in t1 if b == B)
    print(f"  B={B}: " + "  ".join(f"ctx={c//1024}k:{t1[(B,c)]:.2f}ms" for c in xs))

# ---------------------------------------------------------------- trace
steps = []
orig_admit, orig_step = Engine._admit, Engine._one_step

def admit(self, force_idle=False):
    dec, pre, dt_, pt_ = orig_admit(self, force_idle)
    comp = [(q.sid, "D", 1, self.sessions[q.sid].ctx, False) for q in dec]
    comp += [(q.sid, "P", n, self.sessions[q.sid].ctx, q.is_tool)
             for q, n in pre]
    self._comp = comp
    return dec, pre, dt_, pt_

def one_step(self, force_idle=False):
    t0 = self.now
    if orig_step(self, force_idle):
        steps.append((t0, self.now - t0, self._comp))
        return True
    return False

Engine._admit, Engine._one_step = admit, one_step
e = Engine(cal, n_sessions=12, seed=1, sim_ms=3000, tool_rate_per_min=0,
           phase="random", fixed_tools=[(999.0, 3, 8192, 1.0)])
e.run()

def price(comp):
    dec = [c for c in comp if c[1] == "D"]
    pre = [c for c in comp if c[1] == "P"]
    ptok = sum(c[2] for c in pre)
    if dec:
        avg_ctx = sum(c[3] for c in dec) / len(dec)
        base = cal.decode_ms(max(len(dec), 1), avg_ctx)
        if not ptok:
            return f"decode基线(B={len(dec)},ctx~{avg_ctx:.0f}) {base:.1f}"
        cs = sorted(cal.toll_fused)
        toll = _interp1(avg_ctx, cs, [cal.toll_fused[c] for c in cs])
        comp_ms = cal._compute_ms(ptok, sum(c[3] for c in pre) / len(pre))
        return (f"decode基线(B={len(dec)},ctx~{avg_ctx:.0f}) {base:.1f} "
                f"+ eager过路费 {toll:.1f} + prefill计算({ptok}tok) {comp_ms:.1f}")
    pctx = sum(c[3] for c in pre) / len(pre)
    cs = sorted(cal.toll_solo)
    toll = _interp1(pctx, cs, [cal.toll_solo[c] for c in cs])
    return (f"纯prefill步: 过路费 {toll:.1f} "
            f"+ 计算({ptok}tok@ctx{pctx:.0f}) {cal._compute_ms(ptok, pctx):.1f}")

def show(label, t0, dt, comp):
    print(f"\n  [{label}]  t={t0:.1f}ms  步时 {dt:.1f}ms")
    lay = " | ".join(f"s{sid}:{n}{role}{'(tool)' if tool else ''}"
                     for sid, role, n, _c, tool in comp)
    print(f"    token 布局(共 {sum(c[2] for c in comp)} tok 进同一次 forward): [ {lay} ]")
    for sid, role, n, ctx, tool in comp:
        tag = "工具结果 prefill" if tool else (
            "micro-prefill(新到的音频片)" if role == "P" else "decode(生成 1 token)")
        print(f"      s{sid:<2} {role} {n:>4} tok  ctx={ctx:<5} {tag}")
    print(f"    计价: {price(comp)} => {dt:.1f}ms")

picked = {}
for (t0, dt, comp) in steps:
    roles = {c[1] for c in comp}
    if len(comp) == 1 and roles == {"P"} and not comp[0][4]:
        picked.setdefault("A 单路唤醒: 独自的 micro-prefill 步", (t0, dt, comp))
    if len(comp) >= 2 and roles == {"P", "D"} and not any(c[4] for c in comp):
        picked.setdefault("B 混合步: 一路的 prefill + 另一路的 decode", (t0, dt, comp))
    if len(comp) >= 2 and roles == {"D"}:
        picked.setdefault("C 共批纯 decode 步", (t0, dt, comp))
    if any(c[4] for c in comp):
        picked.setdefault("D 工具注入步 (整段拼回)", (t0, dt, comp))
    if len(comp) >= 6 and "P" in roles:
        picked.setdefault("E 注入后放行: 多路 micro-prefill 挤进一步", (t0, dt, comp))

print("\n== (b) 一步之内不同请求的不同阶段怎么排 ==")
for k in sorted(picked):
    show(k, *picked[k])
