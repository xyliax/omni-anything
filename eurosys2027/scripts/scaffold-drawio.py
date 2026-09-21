#!/usr/bin/env python3
"""Generate editable Draw.io starting files for Figure 1 and Figure 3.

The output is a starting point for hand editing in Draw.io, laid out from the
internal coordinates in planning/figure-drawing-guide.md.  It is not a
rendering pipeline: after the author edits the .drawio files, they become the
source of truth and this script should not be re-run over them.

Usage (from repository root):
    python eurosys2027/scripts/scaffold-drawio.py [--force]
"""
from __future__ import annotations

import argparse
import html
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "figures"

# Palette from the drawing guide.
DEEP = "#28769B"
PALE = "#EAF2F7"
HATCH_STROKE = "#B87519"
HATCH_FILL = "#FFF0D9"
INK = "#263642"
GRAY = "#9CA9B2"
PX_PER_IN = 96


class Doc:
    """Minimal mxGraphModel builder."""

    def __init__(self) -> None:
        self.cells: list[str] = []
        self.next_id = 2

    def _id(self) -> str:
        i = f"c{self.next_id}"
        self.next_id += 1
        return i

    def group(self, name: str, x: float, y: float, w: float, h: float) -> str:
        gid = self._id()
        self.cells.append(
            f'<mxCell id="{gid}" value="{html.escape(name)}" style="group" vertex="1" '
            f'connectable="0" parent="1"><mxGeometry x="{x:.1f}" y="{y:.1f}" '
            f'width="{w:.1f}" height="{h:.1f}" as="geometry"/></mxCell>'
        )
        return gid

    def rect(self, x, y, w, h, style, parent="1", value="") -> str:
        cid = self._id()
        self.cells.append(
            f'<mxCell id="{cid}" value="{html.escape(value)}" style="{style}" vertex="1" '
            f'parent="{parent}"><mxGeometry x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" '
            f'height="{h:.1f}" as="geometry"/></mxCell>'
        )
        return cid

    def line(self, x1, y1, x2, y2, style, parent="1") -> str:
        cid = self._id()
        self.cells.append(
            f'<mxCell id="{cid}" style="{style}" edge="1" parent="{parent}">'
            f'<mxGeometry relative="1" as="geometry"><mxPoint x="{x1:.1f}" y="{y1:.1f}" '
            f'as="sourcePoint"/><mxPoint x="{x2:.1f}" y="{y2:.1f}" as="targetPoint"/>'
            f"</mxGeometry></mxCell>"
        )
        return cid

    def text(self, x, y, w, h, value, size=8, align="center", parent="1", color=INK) -> str:
        style = (
            f"text;html=1;align={align};verticalAlign=middle;fontFamily=Helvetica;"
            f"fontSize={size};fontColor={color};strokeColor=none;fillColor=none;"
        )
        return self.rect(x, y, w, h, style, parent, value)

    def to_xml(self, page_w: float, page_h: float) -> str:
        body = "\n".join(self.cells)
        return (
            '<mxfile host="app.diagrams.net" type="device">\n'
            f'<diagram name="figure" id="fig">\n'
            f'<mxGraphModel dx="1000" dy="600" grid="1" gridSize="5" guides="1" '
            f'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
            f'pageWidth="{page_w:.0f}" pageHeight="{page_h:.0f}" math="0" shadow="0">\n'
            "<root>\n<mxCell id=\"0\"/>\n<mxCell id=\"1\" parent=\"0\"/>\n"
            f"{body}\n</root>\n</mxGraphModel>\n</diagram>\n</mxfile>\n"
        )


# Shared styles.
S_DEEP = f"rounded=0;whiteSpace=wrap;html=1;fillColor={DEEP};strokeColor={DEEP};strokeWidth=0.5;"
S_PALE = f"rounded=0;whiteSpace=wrap;html=1;fillColor={PALE};strokeColor={GRAY};strokeWidth=0.5;"
S_HATCH = (
    f"rounded=0;whiteSpace=wrap;html=1;fillColor={HATCH_FILL};strokeColor={HATCH_STROKE};"
    f"strokeWidth=0.75;fillStyle=hachure;sketch=1;curveFitting=1;jiggle=0;hachureGap=3;"
)
S_DIAMOND = f"rhombus;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={INK};strokeWidth=1;"
S_AXIS = f"endArrow=none;html=1;strokeColor={INK};strokeWidth=1;"
S_REF = f"endArrow=none;html=1;strokeColor={GRAY};strokeWidth=0.75;dashed=1;dashPattern=2 2;"
S_CAP = f"endArrow=none;html=1;strokeColor={HATCH_STROKE};strokeWidth=1;dashed=1;dashPattern=4 3;"
S_CAP_INK = f"endArrow=none;html=1;strokeColor={INK};strokeWidth=1;dashed=1;dashPattern=4 3;"
S_STEP = f"endArrow=none;html=1;strokeColor={INK};strokeWidth=1.25;"
S_STEP_GRAY = f"endArrow=none;html=1;strokeColor={GRAY};strokeWidth=1;dashed=1;dashPattern=3 3;"
S_TICK = f"endArrow=none;html=1;strokeColor={INK};strokeWidth=0.75;"
S_CIRCLE = (
    f"ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#FFFFFF;strokeColor={INK};"
    f"strokeWidth=1;fontSize=7;fontFamily=Helvetica;fontColor={INK};"
)
S_DOT = f"ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor={INK};strokeColor={INK};"


def staircase(doc: Doc, pts: list[tuple[float, float]], x_of, y_of, style, parent) -> None:
    """Draw a step function through (t, value) points using horizontal+vertical edges."""
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        doc.line(x_of(t0), y_of(v0), x_of(t1), y_of(v0), style, parent)
        if v1 != v0:
            doc.line(x_of(t1), y_of(v0), x_of(t1), y_of(v1), style, parent)


# ----------------------------------------------------------------------------
# Figure 1
# ----------------------------------------------------------------------------

def build_figure1() -> str:
    W, H = 7.0 * PX_PER_IN, 2.6 * PX_PER_IN
    doc = Doc()
    T = 1000.0

    # ---- Panel (a) ---------------------------------------------------------
    ax0, ax1 = 34.0, W * 0.60 - 12.0  # x range for the plot area
    top, lane_h, gap = 26.0, 24.0, 4.0
    block_px = 3.2  # pixels per KV block for lane bands
    x_of = lambda t: ax0 + (ax1 - ax0) * t / (3 * T)

    ga = doc.group("panel-a", 0, 0, W * 0.6, H)
    doc.text(ax0, 4, ax1 - ax0, 14, "(a) KV binds before compute", 9, "left", ga)

    sessions = [("S1", 4), ("S2", 4), ("S3", 5), ("S4", 5)]
    lane_groups = []
    for i, (name, h0) in enumerate(sessions):
        lane_y = top + i * (lane_h + gap)
        base = lane_y + lane_h
        lg = doc.group(f"lane-{name}", ax0 - 30, lane_y, ax1 - ax0 + 30, lane_h)
        lane_groups.append(lg)
        doc.text(ax0 - 30, lane_y + lane_h / 2 - 7, 26, 14, name, 9, "right", lg)
        blocks = h0
        for k in range(3):
            t_rel = k * T
            # compute burst
            hpx = blocks * block_px
            doc.rect(x_of(t_rel), base - hpx, x_of(t_rel + 0.35 * T) - x_of(t_rel), hpx, S_DEEP, lg)
            blocks += 1
            hpx = blocks * block_px
            doc.rect(x_of(t_rel + 0.35 * T), base - hpx, x_of(t_rel + T) - x_of(t_rel + 0.35 * T), hpx, S_PALE, lg)
            # release diamond
            doc.rect(x_of(t_rel) - 3.5, lane_y - 2, 7, 7, S_DIAMOND, lg)
    # reference lines at releases
    plot_bottom = top + 4 * (lane_h + gap) - gap
    for k in range(3):
        doc.line(x_of(k * T), top - 4, x_of(k * T), plot_bottom + 50, S_REF, ga)
    # T dimension line and shared idle bracket
    doc.line(x_of(0), top - 8, x_of(T), top - 8, f"endArrow=open;startArrow=open;endFill=0;startFill=0;html=1;strokeColor={INK};strokeWidth=0.75;endSize=4;startSize=4;", ga)
    doc.text(x_of(0.5 * T) - 10, top - 20, 20, 12, "T", 8, "center", ga)
    doc.line(x_of(0.35 * T), plot_bottom + 4, x_of(T), plot_bottom + 4, f"endArrow=none;html=1;strokeColor={GRAY};strokeWidth=0.75;", ga)
    doc.text(x_of(0.35 * T), plot_bottom + 5, x_of(T) - x_of(0.35 * T), 12, "shared idle", 8, "center", ga, GRAY)

    # aggregate subplot
    agg_top = plot_bottom + 20
    agg_h = 34.0
    cap_blocks = 26.0  # sum 18 at t=0 ~ 0.7 * 26
    y_of = lambda v: agg_top + agg_h - agg_h * v / (cap_blocks * 1.1)
    gs = doc.group("aggregate", ax0 - 30, agg_top, ax1 - ax0 + 30, agg_h + 14)
    doc.text(ax0 - 30, agg_top + agg_h / 2 - 7, 26, 14, "Σ", 9, "right", gs)
    pts = [(0, 18), (0.35 * T, 22), (1.35 * T, 26), (2.35 * T, 30), (3 * T, 30)]
    staircase(doc, pts, x_of, y_of, S_STEP, gs)
    doc.line(x_of(0), y_of(cap_blocks), x_of(3 * T), y_of(cap_blocks), S_CAP, gs)
    doc.text(x_of(3 * T) - 44, y_of(cap_blocks) - 12, 44, 11, "capacity", 8, "right", gs, HATCH_STROKE)
    # crossing marker (at second-round growth, inside idle window)
    doc.rect(x_of(1.35 * T) - 2.5, y_of(26) - 2.5, 5, 5, S_DOT, gs)
    doc.text(x_of(1.35 * T) + 4, y_of(26) - 14, 40, 11, "exceeds", 8, "left", gs)
    # axis
    doc.line(x_of(0), agg_top + agg_h, x_of(3 * T), agg_top + agg_h, S_AXIS, gs)
    for k, lab in enumerate(["0", "T", "2T", "3T"]):
        doc.line(x_of(k * T), agg_top + agg_h, x_of(k * T), agg_top + agg_h + 3, S_TICK, gs)
        doc.text(x_of(k * T) - 10, agg_top + agg_h + 3, 20, 11, lab, 8, "center", gs)

    # ---- Panel (b) ---------------------------------------------------------
    bx0, bx1 = W * 0.60 + 44.0, W - 8.0
    xb = lambda t: bx0 + (bx1 - bx0) * t / (2 * T)
    gb = doc.group("panel-b", W * 0.6, 0, W * 0.4, H)
    doc.text(bx0, 4, bx1 - bx0, 14, "(b) Restoration timing", 9, "left", gb)
    row_h, row_gap, row_top = 52.0, 10.0, 30.0
    bpx = row_h / 10.0  # px per block, history 9 blocks
    rows = [("Reactive", 0.0, 1), ("Pilarius", 0.16 * T, 2)]
    for r, (label, lead, num) in enumerate(rows):
        ry = row_top + r * (row_h + row_gap)
        base = ry + row_h
        rg = doc.group(f"row-{label}", bx0 - 44, ry, bx1 - bx0 + 44, row_h)
        doc.text(bx0 - 44, ry + row_h / 2 - 7, 40, 14, label, 9, "right", rg)
        for k in range(2):
            rel = 0.5 * T + k * T
            seg_start = k * T
            # idle before restore
            rs = rel - lead
            doc.rect(xb(seg_start), base - 3 * bpx, xb(rs) - xb(seg_start), 3 * bpx, S_PALE, rg)
            # restore hatch (0.06T), height rises to 9
            doc.rect(xb(rs), base - 9 * bpx, xb(rs + 0.06 * T) - xb(rs), 9 * bpx, S_HATCH, rg)
            if lead > 0:
                # ready wait until release
                doc.rect(xb(rs + 0.06 * T), base - 9 * bpx, xb(rel) - xb(rs + 0.06 * T), 9 * bpx, S_PALE, rg)
                cs = rel
            else:
                cs = rs + 0.06 * T
            doc.rect(xb(cs), base - 9 * bpx, xb(cs + 0.35 * T) - xb(cs), 9 * bpx, S_DEEP, rg)
            # after compute: drop to 3 blocks until end of period
            doc.rect(xb(cs + 0.35 * T), base - 3 * bpx, xb(seg_start + T) - xb(cs + 0.35 * T), 3 * bpx, S_PALE, rg)
            doc.rect(xb(rel) - 3.5, ry - 2, 7, 7, S_DIAMOND, rg)
            if k == 0:
                doc.rect(xb(rs) + 2, ry - 12, 10, 10, S_CIRCLE, rg, str(num))
                if lead > 0:
                    doc.text(xb(rs + 0.06 * T), ry + 2, xb(rel) - xb(rs + 0.06 * T), 10, "ready", 7, "center", rg, GRAY)
                    doc.text(xb(cs + 0.35 * T) + 1, base - 3 * bpx - 12, 26, 10, "evict", 7, "left", rg, GRAY)
    b_bottom = row_top + 2 * (row_h + row_gap) - row_gap
    for k in range(2):
        rel = 0.5 * T + k * T
        doc.line(xb(rel), row_top - 6, xb(rel), b_bottom + 4, S_REF, gb)
    doc.line(xb(0), b_bottom + 4, xb(2 * T), b_bottom + 4, S_AXIS, gb)
    for k, lab in enumerate(["0", "T", "2T"]):
        doc.line(xb(k * T), b_bottom + 4, xb(k * T), b_bottom + 7, S_TICK, gb)
        doc.text(xb(k * T) - 10, b_bottom + 7, 20, 11, lab, 8, "center", gb)

    # legend
    lg = doc.group("legend", W - 170, H - 22, 165, 16)
    doc.rect(W - 170, H - 18, 10, 8, S_DEEP, lg); doc.text(W - 158, H - 21, 40, 14, "compute", 7, "left", lg)
    doc.rect(W - 118, H - 18, 10, 8, S_PALE, lg); doc.text(W - 106, H - 21, 40, 14, "idle KV", 7, "left", lg)
    doc.rect(W - 66, H - 18, 10, 8, S_HATCH, lg); doc.text(W - 54, H - 21, 50, 14, "in flight", 7, "left", lg)
    return doc.to_xml(W, H)


# ----------------------------------------------------------------------------
# Figure 3 (file basename figure2-design-overview)
# ----------------------------------------------------------------------------

def build_figure3() -> str:
    W, H = 7.0 * PX_PER_IN, 3.2 * PX_PER_IN
    doc = Doc()
    T = 1000.0
    ax0, ax1 = 40.0, W - 10.0
    x_of = lambda t: ax0 + (ax1 - ax0) * t / (1.16 * T)
    top, lane_h, gap = 22.0, 30.0, 4.0
    bpx = lane_h / 10.0

    # phase reference lines and labels
    for k in range(4):
        doc.line(x_of(k * T / 4), top - 2, x_of(k * T / 4), H - 30, S_REF)
        doc.text(x_of(k * T / 4) - 10, top - 16, 20, 12, f"φ{k + 1}", 8, "center")

    # Per-session band segments: (t0, t1, blocks, style)
    def band(lg, base, t0, t1, blocks, style):
        t0c, t1c = max(t0, 0.0), min(t1, 1.16 * T)
        if t1c <= t0c:
            return
        doc.rect(x_of(t0c), base - blocks * bpx, x_of(t1c) - x_of(t0c), blocks * bpx, style, lg)

    lanes = {
        # name: (release offset, segments)
        "S1": (0, [
            (0, 30, 8, S_PALE), (30, 140, 8, S_DEEP), (140, 380, 9, S_DEEP), (380, 900, 3, S_PALE),
            (900, 960, 9, S_HATCH), (960, 1030, 9, S_PALE), (1030, 1160, 9, S_DEEP)]),
        "S2": (250, [
            (0, 160, 3, S_PALE), (160, 220, 8, S_HATCH), (220, 280, 8, S_PALE), (280, 420, 8, S_DEEP),
            (420, 620, 9, S_DEEP), (620, 1160, 3, S_PALE)]),
        "S3": (500, [
            (0, 380, 3, S_PALE), (380, 440, 8, S_HATCH), (440, 530, 8, S_PALE), (530, 600, 8, S_DEEP),
            (600, 850, 9, S_DEEP), (850, 1160, 3, S_PALE)]),
        "S4": (750, [
            (0, 120, 9, S_DEEP), (120, 650, 3, S_PALE), (650, 710, 9, S_HATCH), (710, 780, 9, S_PALE),
            (780, 900, 9, S_DEEP), (900, 1120, 10, S_DEEP), (1120, 1160, 3, S_PALE)]),
    }
    plus_at = {"S1": 140, "S2": 420, "S3": 600, "S4": 900}
    for i, (name, (rel, segs)) in enumerate(lanes.items()):
        lane_y = top + i * (lane_h + gap)
        base = lane_y + lane_h
        lg = doc.group(f"lane-{name}", ax0 - 34, lane_y, ax1 - ax0 + 34, lane_h)
        doc.text(ax0 - 34, lane_y + lane_h / 2 - 7, 30, 14, name, 9, "right", lg)
        for t0, t1, blocks, style in segs:
            band(lg, base, t0, t1, blocks, style)
        for r in (rel, rel + T):
            if 0 <= r <= 1.16 * T:
                doc.rect(x_of(r) - 3.5, lane_y - 3, 7, 7, S_DIAMOND, lg)
        pt = plus_at[name]
        doc.text(x_of(pt) - 5, lane_y - 6, 10, 10, "+", 8, "center", lg)
    lanes_bottom = top + 4 * (lane_h + gap) - gap

    # circled numbers with anchor dots
    def circled(num, t, lane_idx, dy):
        lane_y = top + lane_idx * (lane_h + gap)
        doc.rect(x_of(t) - 1.5, lane_y + dy - 1.5, 3, 3, S_DOT)
        doc.rect(x_of(t) + 3, lane_y + dy - 12, 10, 10, S_CIRCLE, "1", str(num))
    circled(1, 300, 2, lane_h - 3 * bpx)
    circled(2, 380, 0, lane_h - 3 * bpx)
    circled(3, 410, 2, lane_h - 8 * bpx)
    circled(4, 470, 2, lane_h - 8 * bpx)

    # pool subplot
    pool_top = lanes_bottom + 14
    pool_h = 0.6 * PX_PER_IN
    cap = 25.0
    y_of = lambda v: pool_top + pool_h - pool_h * v / 34.0
    gp = doc.group("pool", ax0 - 34, pool_top, ax1 - ax0 + 34, pool_h)
    doc.text(ax0 - 34, pool_top + pool_h / 2 - 7, 30, 14, "Pool", 9, "right", gp)
    actual = [(0, 23), (180, 23), (300, 23), (380, 22), (500, 23), (620, 18), (750, 24), (920, 25), (1100, 25), (1160, 25)]
    staircase(doc, actual, x_of, lambda v: y_of(v) + (1.5 if v == cap else 0), S_STEP, gp)
    aligned = [(0, 30), (120, 33), (380, 33), (450, 14), (900, 14), (1000, 30), (1120, 33), (1160, 33)]
    staircase(doc, aligned, x_of, y_of, S_STEP_GRAY, gp)
    doc.line(x_of(0), y_of(cap), x_of(1.16 * T), y_of(cap), S_CAP_INK, gp)
    doc.text(x_of(1.16 * T) - 44, y_of(cap) - 12, 44, 11, "capacity", 8, "right", gp)
    doc.text(x_of(450) + 2, y_of(14) - 2, 40, 11, "aligned", 8, "left", gp, GRAY)

    # link tracks
    link_top = pool_top + pool_h + 12
    track_h = 12.0
    gl = doc.group("link", ax0 - 34, link_top, ax1 - ax0 + 34, 2 * track_h + 6)
    h2d = [("S2", 160, 220), ("S3", 380, 440), ("S4", 650, 710), ("S1", 900, 960)]
    d2h = [("S4", 0, 20), ("S1", 160, 210), ("S2", 450, 490), ("S3", 615, 665), ("S4", 915, 965)]
    for r, (label, windows) in enumerate((("H2D", h2d), ("D2H", d2h))):
        ty = link_top + r * (track_h + 6)
        doc.text(ax0 - 34, ty - 1, 30, 14, label, 9, "right", gl)
        doc.line(x_of(0), ty + track_h, x_of(1.16 * T), ty + track_h, f"endArrow=none;html=1;strokeColor={GRAY};strokeWidth=0.5;", gl)
        for name, t0, t1 in windows:
            doc.rect(x_of(t0), ty, x_of(t1) - x_of(t0), track_h, S_HATCH + "fontSize=6;fontFamily=Helvetica;", gl, name)

    # axis
    ay = link_top + 2 * track_h + 10
    doc.line(x_of(0), ay, x_of(1.16 * T), ay, S_AXIS)
    for k, lab in enumerate(["0", "T/4", "T/2", "3T/4", "T"]):
        doc.line(x_of(k * T / 4), ay, x_of(k * T / 4), ay + 3, S_TICK)
        doc.text(x_of(k * T / 4) - 14, ay + 3, 28, 11, lab, 8, "center")
    return doc.to_xml(W, H)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="overwrite existing .drawio files")
    args = ap.parse_args()
    outputs = {
        FIG_DIR / "figure1-motivated-example.drawio": build_figure1,
        FIG_DIR / "figure2-design-overview.drawio": build_figure3,
    }
    for path, builder in outputs.items():
        if path.exists() and not args.force:
            print(f"skip (exists): {path.relative_to(ROOT.parent)}", file=sys.stderr)
            continue
        path.write_text(builder(), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
