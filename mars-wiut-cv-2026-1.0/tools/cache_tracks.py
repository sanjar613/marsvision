#!/usr/bin/env python3
"""Run detector + tracker ONCE per video and cache the rows, so risk tuning is fast.

The frames processed are exactly the ones RiskEstimator sees (every
round(fps / target_fps)-th frame), and tracking is causal, so replaying the
cache through src.risk gives the same result as the live estimator (up to
the small resize difference: we decode at --width and scale boxes back).

    python tools/cache_tracks.py --videos dev/accident/videos --out cache/accident
    python tools/cache_tracks.py --videos /tmp/samples --out cache/samples --width 1280
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.tracking import Detector  # noqa: E402
from src.video import iter_frames, video_info  # noqa: E402

EXTS = {".mp4", ".avi", ".mov", ".mkv"}


def cache_one(path: Path, out: Path, target_fps: float, width: int | None, imgsz: int) -> dict:
    info = video_info(path)
    stride = max(1, int(round(info["fps"] / target_fps)))
    det = Detector(info["fps"], stride, imgsz=imgsz)
    ts, rows, counts = [], [], []
    scale = 1.0
    t0 = time.perf_counter()
    for idx, t, img in iter_frames(path, target_fps=target_fps, width=width):
        if width and img.shape[1] != info["width"]:
            scale = info["width"] / img.shape[1]
        r = det(img)
        if len(r):
            r = r.copy()
            r[:, 2:6] *= scale
        ts.append(t)
        rows.append(r)
        counts.append(len(r))
    wall = time.perf_counter() - t0
    np.savez_compressed(out / f"{path.name}.npz", t=np.array(ts, dtype=np.float64),
                        counts=np.array(counts, dtype=np.int32),
                        rows=np.concatenate(rows) if rows else np.zeros((0, 7), np.float32))
    meta = dict(info, video=path.name, stride=stride, target_fps=target_fps, decode_width=width,
                processed=len(ts), wall_s=round(wall, 1), realtime_x=round(info["duration"] / wall, 2) if wall else None)
    (out / f"{path.name}.json").write_text(json.dumps(meta))
    return meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--target-fps", type=float, default=8.0)
    ap.add_argument("--width", type=int, default=None, help="decode width (None = native)")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    src, out = Path(args.videos), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    vids = sorted(p for p in src.iterdir() if p.suffix.lower() in EXTS)
    if args.limit:
        vids = vids[: args.limit]
    t0 = time.perf_counter()
    for k, p in enumerate(vids):
        if (out / f"{p.name}.npz").exists():
            continue
        m = cache_one(p, out, args.target_fps, args.width, args.imgsz)
        print(f"[{k + 1}/{len(vids)}] {p.name}: {m['duration']:.1f}s video, {m['processed']} frames, "
              f"{m['wall_s']}s wall ({m['realtime_x']}x realtime)", flush=True)
    print(f"cached {len(vids)} videos in {time.perf_counter() - t0:.0f}s -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
