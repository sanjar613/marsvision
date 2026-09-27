#!/usr/bin/env python3
"""Build a Part B dev set from the public ACCIDENT benchmark (CCTV clips).

ACCIDENT's metadata-real.csv gives, per clip, `path`, `accident_time` (impact
onset, seconds) and `duration`. We turn a random, seeded subset into the
organizers' ground_truth.json shape so evaluate.py can score Part B:

    {"clip.mp4": {"duration": 30.0, "fps": 25.0, "events": [[onset, onset+3, "accident"]]}}

and symlink the chosen clips into one folder for run_submission.py.

    python tools/accident_to_gt.py --root /kaggle/input/accident --n 150 --out dev/accident
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import cv2
import pandas as pd

ACCIDENT_LEN = 3.0  # we only know the onset; Part B only uses the start (+ ignore window)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="folder with metadata-real.csv and real_videos/")
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--out", default="dev/accident")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--min-lead", type=float, default=6.0,
                    help="skip clips whose accident starts earlier than this (no time to anticipate)")
    args = ap.parse_args()

    root = Path(args.root)
    meta = pd.read_csv(next(root.rglob("metadata-real.csv")))
    vids = {p.name: p for p in root.rglob("*") if p.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"}}
    meta["file"] = meta["path"].map(lambda p: Path(str(p)).name)
    meta = meta[meta["file"].isin(vids) & (meta["accident_time"] >= args.min_lead)]
    sub = meta.sample(n=min(args.n, len(meta)), random_state=args.seed)

    out = Path(args.out)
    (out / "videos").mkdir(parents=True, exist_ok=True)
    gt = {}
    for _, row in sub.iterrows():
        src = vids[row["file"]]
        name = src.stem + ".mp4" if src.suffix.lower() == ".mp4" else src.name
        dst = out / "videos" / name
        if not dst.exists():
            os.symlink(src.resolve(), dst)
        cap = cv2.VideoCapture(str(src))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        dur = n / fps if n else float(row["duration"])
        s = float(row["accident_time"])
        gt[name] = {"duration": round(dur, 3), "fps": round(fps, 3),
                    "events": [[round(s, 3), round(min(dur, s + ACCIDENT_LEN), 3), "accident"]]}
    (out / "ground_truth.json").write_text(json.dumps(gt, indent=1))
    print(f"{len(gt)} clips -> {out}/videos, labels -> {out}/ground_truth.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
