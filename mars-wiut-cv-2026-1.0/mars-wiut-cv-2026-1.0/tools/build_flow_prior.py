#!/usr/bin/env python3
"""Learn the usual direction of traffic per image cell from normal videos.

Allowed by the rules ("hard-coding facts about the scene ... lane directions
is allowed and expected"): we learn them from the organizer sample videos
instead of writing them by hand. The same code path (FlowMap.update) runs
online inside RiskEstimator, so a video from another camera still works.

    python tools/build_flow_prior.py --cache cache/train_neg --out weights/flow_prior.json \
        --video samples/C3896.MP4 --plot plots/flow_map.jpg
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.risk import FlowMap, RiskConfig, make_state  # noqa: E402
from src.tracking import TrackStore  # noqa: E402
from tools.replay import load_cache  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", nargs="+", required=True)
    ap.add_argument("--out", default="weights/flow_prior.json")
    ap.add_argument("--video", default="", help="a video of the same camera to draw the map on")
    ap.add_argument("--plot", default="")
    args = ap.parse_args()

    cfg = RiskConfig()
    flow, size = None, None
    for folder in args.cache:
        for name, meta, ts, rows in load_cache(Path(folder)):
            s = (int(meta["width"]), int(meta["height"]))
            if flow is None:
                flow, size = FlowMap(*s, cfg), s
            if s != size:
                print(f"skip {name}: size {s} != {size}")
                continue
            store = TrackStore()
            for t, r in zip(ts, rows):
                tracks = store.update(r, float(t))
                flow.update([make_state(tr) for tr in tracks if len(tr.hist) >= 3 and tr.age >= cfg.min_age])
    if flow is None:
        print("no cached videos")
        return 1
    out = {"width": size[0], "height": size[1], "grid": list(cfg.flow_grid),
           "sum": flow.sum.round(2).tolist(), "count": flow.cnt.round(1).tolist()}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out))
    mean = flow.sum / np.maximum(flow.cnt, 1)[..., None]
    coh = np.linalg.norm(mean, axis=-1)
    trusted = (flow.cnt >= cfg.flow_min_count) & (coh >= cfg.flow_min_coherence)
    print(f"FLOW wrote {args.out}: {int(trusted.sum())}/{trusted.size} cells with a clear direction, "
          f"{int(flow.cnt.sum())} observations")

    if args.plot and args.video:
        import cv2
        cap = cv2.VideoCapture(args.video)
        ok, img = cap.read()
        cap.release()
        if ok:
            gx, gy = cfg.flow_grid
            cw, ch = size[0] / gx, size[1] / gy
            for cy in range(gy):
                for cx in range(gx):
                    if flow.cnt[cy, cx] < 3:
                        continue
                    c = np.array([(cx + 0.5) * cw, (cy + 0.5) * ch])
                    d = mean[cy, cx] / (np.linalg.norm(mean[cy, cx]) + 1e-9)
                    col = (0, 220, 255) if trusted[cy, cx] else (160, 160, 160)
                    tip = c + d * 0.42 * min(cw, ch)
                    cv2.arrowedLine(img, tuple(int(v) for v in c), tuple(int(v) for v in tip), col,
                                    max(3, size[0] // 600), tipLength=0.35)
            small = cv2.resize(img, (1600, int(1600 * size[1] / size[0])))
            Path(args.plot).parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(args.plot, small, [cv2.IMWRITE_JPEG_QUALITY, 85])
            print(f"FLOW plot {args.plot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
