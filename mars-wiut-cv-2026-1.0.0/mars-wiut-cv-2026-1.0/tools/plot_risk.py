#!/usr/bin/env python3
"""Plot risk curves from predictions.json with ground-truth accidents marked.

    python tools/plot_risk.py --pred pred.json --gt dev/accident/ground_truth.json --out plots/ --max 24
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

H, W, THETA = 5.0, 10.0, 0.5


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", required=True)
    ap.add_argument("--gt")
    ap.add_argument("--out", default="plots")
    ap.add_argument("--max", type=int, default=24)
    args = ap.parse_args()

    pred = json.loads(Path(args.pred).read_text())["videos"]
    gt = json.loads(Path(args.gt).read_text()) if args.gt else {}
    names = sorted(pred)[: args.max]
    cols = 3
    rows = math.ceil(len(names) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 2.2 * rows), squeeze=False)
    for ax, name in zip(axes.flat, names):
        risk = pred[name].get("risk", [])
        if risk:
            t, s = zip(*risk)
            ax.plot(t, s, lw=1.2, color="#3b6fd4")
        ax.axhline(THETA, color="#999", lw=0.8, ls="--")
        for s0, e0, lab in gt.get(name, {}).get("events", []):
            if lab == "accident":
                ax.axvspan(s0 - H, s0, color="#f2b233", alpha=0.35, lw=0)   # positive frames
                ax.axvspan(s0, e0, color="#d9534f", alpha=0.35, lw=0)      # accident (ignored)
        ax.set_ylim(-0.02, 1.02)
        ax.set_title(name, fontsize=8)
        ax.tick_params(labelsize=7)
    for ax in list(axes.flat)[len(names):]:
        ax.axis("off")
    fig.suptitle("Risk score (blue) · 5 s before impact (amber) · accident (red) · alarm threshold (dashed)",
                 fontsize=10)
    fig.tight_layout()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "risk_curves.png", dpi=110)
    print(f"wrote {out / 'risk_curves.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
