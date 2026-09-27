#!/usr/bin/env python3
"""Draw the scene polygons (src/scene.py) on a frame, and optionally one tile per Part A event.

    python tools/render_scene.py --video samples/C3896.MP4 --out plots/scene.jpg
    python tools/render_scene.py --video samples/C3896.MP4 --pred predictions_samples.json \
        --out plots/events_C3896.jpg

Event tiles show the frame in the middle of the event with the zones and the detector boxes
(people orange, vehicles cyan), so each event can be checked by eye.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.scene import ZONES  # noqa: E402

# BGR
ZONE_COLORS = {"road": (90, 90, 90), "parking": (160, 160, 160), "median": (40, 160, 40),
               "island": (40, 160, 40), "c1": (255, 255, 255), "c2": (255, 255, 255), "c3": (255, 255, 255),
               "t1": (203, 102, 255), "t2": (203, 102, 255), "t3": (203, 102, 255),
               "bus_stop": (0, 200, 255), "q1": (255, 120, 0), "q2": (255, 120, 0)}
TILE_W = 960


def draw_zones(img: np.ndarray, alpha: float = 0.25) -> np.ndarray:
    """Filled, labelled scene polygons on a copy of `img`."""
    h, w = img.shape[:2]
    fill, out = img.copy(), img.copy()
    lw = max(1, w // 800)
    for name, poly in ZONES.items():
        pts = np.round(poly * [w, h]).astype(np.int32)
        if name != "road":
            cv2.fillPoly(fill, [pts], ZONE_COLORS[name])
        cv2.polylines(out, [pts], True, ZONE_COLORS[name], lw * (2 if name == "road" else 1))
    out = cv2.addWeighted(fill, alpha, out, 1 - alpha, 0)
    for name, poly in ZONES.items():
        cx, cy = (poly.mean(0) * [w, h]).astype(int)
        cv2.putText(out, name, (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5 * lw, (255, 255, 255), lw)
    return out


def draw_boxes(img: np.ndarray, boxes: np.ndarray, names: np.ndarray) -> None:
    """Normalised boxes from src.events.detect, drawn in place."""
    h, w = img.shape[:2]
    lw = max(1, w // 640)
    for (x1, y1, x2, y2), n in zip(boxes * [w, h, w, h], names):
        col = (0, 140, 255) if n == "person" else (255, 220, 0)
        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), col, lw)


def read_frame(cap: cv2.VideoCapture, t: float) -> np.ndarray | None:
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(t * (cap.get(cv2.CAP_PROP_FPS) or 25.0))))
    ok, img = cap.read()
    return img if ok else None


def tile(img: np.ndarray, label: str) -> np.ndarray:
    small = cv2.resize(img, (TILE_W, int(TILE_W * img.shape[0] / img.shape[1])))
    cv2.rectangle(small, (0, 0), (TILE_W, 34), (0, 0, 0), -1)
    cv2.putText(small, label, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    return small


def contact_sheet(tiles: list[np.ndarray], cols: int = 3) -> np.ndarray:
    h, w = tiles[0].shape[:2]
    sheet = np.zeros((math.ceil(len(tiles) / cols) * h, cols * w, 3), np.uint8)
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        sheet[r * h:(r + 1) * h, c * w:(c + 1) * w] = t[:h, :w]
    return sheet


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--t", type=float, default=5.0, help="frame time for the plain scene picture")
    ap.add_argument("--pred", help="predictions.json: render one tile per event of this video")
    args = ap.parse_args()

    cap = cv2.VideoCapture(args.video)
    if args.pred:
        from src.events import detect
        from src.tracking import load_model

        events = json.loads(Path(args.pred).read_text())["videos"][Path(args.video).name]["events"]
        model, tiles = load_model(), []
        for s, e, label in events:
            img = read_frame(cap, (s + e) / 2)
            if img is None:
                continue
            out = draw_zones(img)
            draw_boxes(out, *detect(model, img))
            tiles.append(tile(out, f"{label}  {s:.1f}-{e:.1f}s"))
        if not tiles:
            print("no events to render")
            return 0
        result = contact_sheet(tiles)
    else:
        img = read_frame(cap, args.t)
        if img is None:
            print(f"cannot read a frame at t={args.t}s", file=sys.stderr)
            return 1
        result = draw_zones(img)
    cap.release()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(args.out, result, [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
