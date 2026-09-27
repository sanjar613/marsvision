#!/usr/bin/env python3
"""Replay cached tracker rows through the risk model and score Part B.

Runs the same TrackStore + RiskModel code as RiskEstimator, frame by frame
(causal), then scores with the official evaluate.py functions. Takes seconds,
so it is what we use for tuning, ablations and calibrator training.

    python tools/replay.py --cache cache/accident cache/samples \
        --gt dev/accident/ground_truth.json --split test \
        --config '{"alarm_on": 0.6}' --calibrator weights/risk_calibrator.json \
        --features-out feats.csv --frames-out frames.jsonl

Videos in --negatives-cache are added to the ground truth with no events
(organizer samples: we assume no accident; check visually!).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import evaluate as ev  # noqa: E402
from src.risk import FEATURES, Calibrator, RiskConfig, RiskModel, load_flow_prior  # noqa: E402
from src.tracking import TrackStore  # noqa: E402


def split_of(name: str, test_frac: float = 0.3) -> str:
    h = int(hashlib.md5(name.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return "test" if h < test_frac else "train"


def load_cache(folder: Path):
    for npz in sorted(folder.glob("*.npz")):
        meta = json.loads(npz.with_suffix(".json").read_text())
        d = np.load(npz)
        yield npz.stem, meta, d["t"], np.split(d["rows"], np.cumsum(d["counts"])[:-1]) if len(d["counts"]) else []


def replay_video(meta, ts, rows_per_frame, cfg, cal, prior=None):
    store = TrackStore()
    model = RiskModel(cfg, cal, frame_size=(int(meta["width"]), int(meta["height"])), flow_prior=prior)
    scores, feats = [], []
    for t, rows in zip(ts, rows_per_frame):
        tracks = store.update(rows, float(t))
        s, f = model.step(tracks, float(t))
        scores.append(s)
        feats.append(f)
    # expand to every frame like the harness (skipped frames repeat the last score)
    fps, n = meta["fps"], int(meta["n_frames"]) or int(round(meta["duration"] * meta["fps"]))
    stride = meta["stride"]
    curve = [[round(i / fps, 4), round(scores[min(i // stride, len(scores) - 1)], 4)] for i in range(n)] if scores else []
    return curve, feats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", nargs="+", required=True, help="cache folders with accident clips (labelled)")
    ap.add_argument("--negatives-cache", nargs="*", default=[], help="cache folders of videos with no accident")
    ap.add_argument("--gt", required=True, help="ground_truth.json for the labelled clips")
    ap.add_argument("--split", choices=["all", "train", "test"], default="all")
    ap.add_argument("--config", default="{}", help="JSON overrides for RiskConfig")
    ap.add_argument("--calibrator", default="", help="path to calibrator JSON ('' = hand formula)")
    ap.add_argument("--features-out", default="")
    ap.add_argument("--frames-out", default="")
    ap.add_argument("--pred-out", default="")
    ap.add_argument("--tag", default="")
    ap.add_argument("--flow-prior", default="", help="flow_prior.json (used only for videos of the same size)")
    args = ap.parse_args()

    gt_all = json.loads(Path(args.gt).read_text())
    cal = Calibrator.load(Path(args.calibrator)) if args.calibrator else None
    cfg_d = dict(cal.config) if cal else {}
    cfg_d.update(json.loads(args.config))
    cfg = RiskConfig.from_dict(cfg_d)
    prior = load_flow_prior(Path(args.flow_prior)) if args.flow_prior else None

    gt, pred = {}, {"team": "replay", "videos": {}}
    rows_out, frames_out = [], []
    probs, first_alarm = [], []
    sources = [(Path(c), False) for c in args.cache] + [(Path(c), True) for c in args.negatives_cache]
    for folder, is_neg in sources:
        for name, meta, ts, rows in load_cache(folder):
            if not is_neg:
                if name not in gt_all:
                    continue
                if args.split != "all" and split_of(name) != args.split:
                    continue
                g = gt_all[name]
            else:
                g = {"duration": meta["duration"], "fps": meta["fps"], "events": []}
            curve, feats = replay_video(meta, ts, rows, cfg, cal, prior)
            probs.extend(f["prob"] for f in feats)
            if not is_neg:
                st = ev.alarm_starts(curve)
                if st:
                    first_alarm.append(st[0])
            gt[name] = g
            pred["videos"][name] = {"events": [], "risk": curve}
            acc = sorted(ev.segs(g["events"], "accident"))
            nm = ev.segs(g["events"], "near_miss")
            for f in feats:
                lab = ev.frame_label(f["t"], acc, nm)
                if args.features_out and lab is not None:
                    rows_out.append([name, f["t"], lab, int(is_neg)] + [round(float(f[k]), 5) for k in FEATURES])
                if args.frames_out:
                    frames_out.append({"video": name, "t": f["t"], "score": f["score"], "prob": round(f["prob"], 4),
                                       "best_pair": f["best_pair"], "n_users": f["n_users"],
                                       "min_ttc": round(f["min_ttc"], 2),
                                       "flow_anom": round(f["flow_anom"], 3), "brake": round(f["brake"], 3)})
    rep = ev.evaluate(gt, pred)
    b = rep["part_b"] or {}
    # false alarms per minute on the negative videos
    neg_min, neg_alarms = 0.0, 0
    for folder, is_neg in sources:
        if not is_neg:
            continue
        for name, meta, _ts, _rows in load_cache(folder):
            neg_min += meta["duration"] / 60
            neg_alarms += len(ev.alarm_starts(pred["videos"][name]["risk"]))
    summary = {
        "tag": args.tag, "split": args.split, "videos": len(gt), "accidents": b.get("n_accidents"),
        "score_b": round(b.get("score_b", 0), 4), "ap": round(b.get("ap", 0), 3),
        "alarm_p": round(b.get("alarm_precision", 0), 3), "alarm_r": round(b.get("alarm_recall", 0), 3),
        "f1_alarm": round(b.get("f1_alarm", 0), 3), "mtta": round(b.get("mtta_sec", 0), 2),
        "alarms": b.get("n_alarms"), "neg_alarms_per_min": round(neg_alarms / neg_min, 2) if neg_min else None,
        # sanity checks against "fire at the start of every clip" artefacts
        "prob_std": round(float(np.std(probs)), 4) if probs else None,
        "first_alarm_median_s": round(float(np.median(first_alarm)), 2) if first_alarm else None,
        "first_alarm_lt4s": round(float(np.mean(np.array(first_alarm) < 4)), 3) if first_alarm else None,
    }
    print("SUMMARY", json.dumps(summary))
    if args.features_out:
        with open(args.features_out, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["video", "t", "label", "negative_video"] + FEATURES)
            w.writerows(rows_out)
    if args.frames_out:
        Path(args.frames_out).write_text("\n".join(json.dumps(r) for r in frames_out))
    if args.pred_out:
        Path(args.pred_out).write_text(json.dumps(pred))
    with open(ROOT / "ablations.jsonl", "a") as fh:
        fh.write(json.dumps(dict(summary, config=json.loads(args.config), calibrator=args.calibrator)) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
