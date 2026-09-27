#!/usr/bin/env python3
"""Contact sheet of what the risk model sees at its alarm moments.

For one video: take the replayed per-frame log (tools/replay.py --frames-out),
find alarm starts (score crosses 0.5), and draw every tracked box at that
moment, the flagged pair in red, plus time / score / min TTC.

    python tools/render_alarms.py --video /tmp/samples/C3905.MP4 --cache cache/samples \
        --frames frames.jsonl --out plots/alarms_C3905.jpg --max 12
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--frames", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max", type=int, default=12)
    ap.add_argument("--times", default="", help="comma-separated times instead of alarm starts")
    args = ap.parse_args()

    vid = Path(args.video)
    name = vid.name
    d = np.load(Path(args.cache) / f"{name}.npz")
    ts = d["t"]
    rows = np.split(d["rows"], np.cumsum(d["counts"])[:-1])
    log = [json.loads(line) for line in Path(args.frames).read_text().splitlines() if line.strip()]
    log = [r for r in log if r["video"] == name]
    if args.times:
        picks = [float(x) for x in args.times.split(",")]
    else:
        picks = [log[i]["t"] for i in range(1, len(log)) if log[i]["score"] >= 0.5 > log[i - 1]["score"]]
    picks = picks[: args.max]
    by_t = {round(r["t"], 3): r for r in log}

    cap = cv2.VideoCapture(str(vid))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    tiles = []
    for t in picks:
        k = int(np.argmin(np.abs(ts - t)))
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(ts[k] * fps)))
        ok, img = cap.read()
        if not ok:
            continue
        info = by_t.get(round(float(ts[k]), 3), {})
        pair = set(info.get("best_pair") or [])
        lw = max(2, img.shape[1] // 640)
        for tid, _cls, x1, y1, x2, y2, _c in rows[k]:
            col = (0, 0, 255) if int(tid) in pair else (0, 220, 0)
            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), col, lw * (2 if int(tid) in pair else 1))
        label = f"t={ts[k]:.1f}s score={info.get('score', 0):.2f} ttc={info.get('min_ttc', 0):.1f}s n={info.get('n_users', 0)}"
        small = cv2.resize(img, (960, int(960 * img.shape[0] / img.shape[1])))
        cv2.rectangle(small, (0, 0), (960, 34), (0, 0, 0), -1)
        cv2.putText(small, label, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        tiles.append(small)
    cap.release()
    if not tiles:
        print("no alarm frames to render")
        return 0
    cols = 3
    rows_n = math.ceil(len(tiles) / cols)
    h, w = tiles[0].shape[:2]
    sheet = np.zeros((rows_n * h, cols * w, 3), np.uint8)
    for i, tile in enumerate(tiles):
        r, c = divmod(i, cols)
        sheet[r * h:(r + 1) * h, c * w:(c + 1) * w] = tile[:h, :w]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(args.out, sheet, [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(f"wrote {args.out} ({len(tiles)} frames)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
