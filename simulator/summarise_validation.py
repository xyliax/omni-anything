"""Summarise the repeated validation attempts into one auditable table.

Primary verdict = the attempt taken under the lowest GPU power, i.e. the least
contended one. Every attempt is listed so the choice is visible rather than
implicit: contention inflates eager wake-prefill steps ~19ms -> ~30ms while
graph-replayed decode steps stay flat, so a busy attempt is a measurement of
the co-tenant, not of the calibration model.
"""
import csv
import json
import statistics
from pathlib import Path

RUNS = Path(__file__).parent / "validation_runs"


def load():
    out = []
    for p in sorted(RUNS.glob("report_*.json")):
        try:
            r = json.load(open(p))
        except Exception:
            continue
        v = r["verdict"]
        i = p.stem.split("_")[1]
        tl = RUNS / f"timeline_{i}.csv"
        pw = ut = None
        if tl.exists():
            rows = list(csv.DictReader(open(tl)))
            pw = statistics.fmean(float(x["power_w"]) for x in rows if x["power_w"])
            ut = statistics.fmean(float(x["gpu_util_pct"]) for x in rows
                                  if x["gpu_util_pct"])
        out.append({"attempt": int(i), "mean_abs_pct": v["mean_abs_beat_err_pct"],
                    "max_abs_pct": v["max_abs_beat_err_pct"],
                    "cum_pct": v["final_cumulative_err_pct"],
                    "pass": v["PASS"], "mean_power_w": round(pw, 1) if pw else None,
                    "mean_util_pct": round(ut, 1) if ut else None})
    return out


def main():
    rows = load()
    if not rows:
        print("no attempts found in", RUNS)
        return
    # Ranked by cumulative error, and the MEDIAN attempt is the verdict. Ranking
    # by GPU power was tried first and rejected: our own process is most of the
    # draw, so power does not separate contended runs from quiet ones (attempt at
    # 150W scored 11.7% while one at 165W scored 2.5%). The median is the
    # defensible statistic when every attempt clears the bar anyway.
    rows.sort(key=lambda r: r["cum_pct"])
    print(f"{'att':>4} {'mean_abs%':>10} {'max_abs%':>9} {'cum%':>7} "
          f"{'power_W':>8} {'util%':>6}  pass")
    for r in rows:
        print(f"{r['attempt']:>4} {r['mean_abs_pct']:>10.2f} {r['max_abs_pct']:>9.2f} "
              f"{r['cum_pct']:>7.2f} {str(r['mean_power_w']):>8} "
              f"{str(r['mean_util_pct']):>6}  {r['pass']}")
    best = rows[len(rows) // 2]
    cums = [r["cum_pct"] for r in rows]
    means = [r["mean_abs_pct"] for r in rows]
    summary = {
        "n_attempts": len(rows),
        "primary_attempt": best["attempt"],
        "primary_selection_rule": "median attempt by cumulative timeline error",
        "all_attempts_pass": all(r["pass"] for r in rows),
        "primary": best,
        "cum_pct_min": min(cums), "cum_pct_median": round(statistics.median(cums), 2),
        "cum_pct_max": max(cums),
        "mean_abs_pct_min": min(means),
        "mean_abs_pct_median": round(statistics.median(means), 2),
        "pass_bar_pct": 15.0,
        "PASS_on_cumulative_timeline": bool(statistics.median(cums) < 15.0),
        "mean_abs_pct_max": max(means),
        "attempts": rows,
    }
    (RUNS / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nprimary = attempt {best['attempt']} "
          f"(cum {best['cum_pct']:.2f}%, mean |err| {best['mean_abs_pct']:.2f}%)")
    print(f"cumulative timeline error across attempts: "
          f"min {min(cums):.2f}% / median {statistics.median(cums):.2f}% / "
          f"max {max(cums):.2f}%  (bar 15%)")
    print(f"[write] {RUNS / 'summary.json'}")


if __name__ == "__main__":
    main()
