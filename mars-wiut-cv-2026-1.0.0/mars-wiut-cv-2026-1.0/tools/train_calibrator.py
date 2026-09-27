#!/usr/bin/env python3
"""Fit the logistic-regression risk calibrator on replayed frame features.

Input: CSV from tools/replay.py --features-out (train split only!), with the
frame labels the official metric uses (1 = within 5 s before an accident,
0 = normal; ignored frames are already dropped).

    python tools/train_calibrator.py --features feats_train.csv --out weights/risk_calibrator.json \
        --config '{"alarm_on": 0.6}'

Plain numpy (no sklearn needed at inference): standardise, class-balanced
log-loss + L2, full-batch gradient descent with a fixed seed -> deterministic.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.risk import FEATURES  # noqa: E402


def fit(X: np.ndarray, y: np.ndarray, l2: float = 1e-2, lr: float = 0.5, steps: int = 3000,
        sample_w: np.ndarray | None = None, balance: bool = False):
    """Log-loss + L2. balance=False keeps probabilities calibrated (a balanced
    fit pushes every score towards 0.5, which is what broke Day 2)."""
    mean, std = X.mean(0), X.std(0) + 1e-6
    Z = (X - mean) / std
    wts = np.ones(len(y)) if sample_w is None else sample_w.astype(float)
    if balance:
        pos = y.mean()
        wts = wts * np.where(y == 1, 0.5 / max(pos, 1e-6), 0.5 / max(1 - pos, 1e-6))
    wts = wts / wts.mean()
    w, b = np.zeros(X.shape[1]), 0.0
    for _ in range(steps):
        p = 1 / (1 + np.exp(-(Z @ w + b)))
        g = wts * (p - y)
        w -= lr * ((Z.T @ g) / len(y) + l2 * w)
        b -= lr * g.mean()
    return mean, std, w, b


def auc(scores: np.ndarray, y: np.ndarray) -> float:
    order = np.argsort(scores)
    ranks = np.empty(len(scores))
    ranks[order] = np.arange(1, len(scores) + 1)
    n1 = y.sum()
    n0 = len(y) - n1
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)) if n1 and n0 else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--out", default="weights/risk_calibrator.json")
    ap.add_argument("--config", default="{}", help="RiskConfig overrides stored with the model")
    ap.add_argument("--l2", type=float, default=1e-2)
    ap.add_argument("--balance", action="store_true", help="class-balanced loss (not recommended)")
    ap.add_argument("--neg-weight", type=float, default=3.0,
                    help="weight of frames from the organizer negative videos (same camera as the test set)")
    args = ap.parse_args()

    with open(args.features) as fh:
        rows = list(csv.DictReader(fh))
    X = np.array([[float(r[k]) for k in FEATURES] for r in rows])
    y = np.array([int(r["label"]) for r in rows], dtype=float)
    sw = np.array([args.neg_weight if r.get("negative_video") == "1" else 1.0 for r in rows])
    mean, std, w, b = fit(X, y, l2=args.l2, sample_w=sw, balance=args.balance)
    p = 1 / (1 + np.exp(-(((X - mean) / std) @ w + b)))
    out = {"features": FEATURES, "mean": mean.round(6).tolist(), "std": std.round(6).tolist(),
           "w": w.round(6).tolist(), "b": round(float(b), 6), "config": json.loads(args.config),
           "train": {"frames": len(y), "positives": int(y.sum()), "auc": round(auc(p, y), 4),
                     "prob_mean": round(float(p.mean()), 4), "prob_std": round(float(p.std()), 4),
                     "balance": args.balance, "neg_weight": args.neg_weight}}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1))
    print("CALIBRATOR", json.dumps(out["train"]), "weights:",
          {k: round(float(v), 3) for k, v in zip(FEATURES, w)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
