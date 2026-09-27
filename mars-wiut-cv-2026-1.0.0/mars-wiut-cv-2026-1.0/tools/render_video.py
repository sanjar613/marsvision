#!/usr/bin/env python3
"""Annotated H.264 copy of one video for the website: zones, detector boxes, active events,
and a strip under the frame with the event timeline and the Part B risk curve.

    python tools/render_video.py --video samples/C3896.MP4 --pred predictions_samples.json \
        --out videos/C3896_annotated.mp4

Needs the `ffmpeg` binary (libx264). Frames are sampled at --fps and shrunk to --width.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.events import detect  # noqa: E402
from src.tracking import load_model  # noqa: E402
from src.video import iter_frames, video_info  # noqa: E402
from tools.render_scene import draw_boxes, draw_zones  # noqa: E402

STRIP_H = 140
THETA = 0.5
EVENT_COLORS = {"stopped_vehicle": (0, 200, 255), "jaywalking": (0, 140, 255)}   # BGR, others grey


def draw_strip(w: int, duration: float, events: list, risk: list) -> np.ndarray:
    """Static part of the strip: one timeline row per event class + the risk curve."""
    strip = np.full((STRIP_H, w, 3), 24, np.uint8)
    x = lambda t: int(round(t / duration * (w - 1)))  # noqa: E731
    labels = sorted({lab for _s, _e, lab in events})
    for row, lab in enumerate(labels):
        y = 6 + row * 16
        cv2.putText(strip, lab, (4, y + 11), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (220, 220, 220), 1)
        for s, e, l2 in events:
            if l2 == lab:
                cv2.rectangle(strip, (x(s), y), (max(x(e), x(s) + 1), y + 12), EVENT_COLORS.get(lab, (160, 160, 160)), -1)
    top, bot = 8 + 16 * len(labels), STRIP_H - 6
    y_of = lambda s: int(round(bot - s * (bot - top)))  # noqa: E731
    cv2.line(strip, (0, y_of(THETA)), (w, y_of(THETA)), (110, 110, 110), 1)
    if risk:
        pts = np.array([[x(t), y_of(s)] for t, s in risk], np.int32)
        cv2.polylines(strip, [pts], False, (255, 160, 60), 1)
    cv2.putText(strip, "risk", (4, bot - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 160, 60), 1)
    return strip


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--pred", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fps", type=float, default=10.0)
    ap.add_argument("--width", type=int, default=1280)
    args = ap.parse_args()

    name = Path(args.video).name
    entry = json.loads(Path(args.pred).read_text())["videos"][name]
    events, risk = entry["events"], entry["risk"]
    info = video_info(args.video)
    duration = info["duration"]
    h = int(round(info["height"] * args.width / info["width"] / 2) * 2)
    out_fps = info["fps"] / max(1, round(info["fps"] / args.fps))
    strip = draw_strip(args.width, duration, events, risk)
    risk_t = np.array([t for t, _s in risk]) if risk else np.zeros(0)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
         "-s", f"{args.width}x{h + STRIP_H}", "-r", f"{out_fps:.3f}", "-i", "-",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", args.out], stdin=subprocess.PIPE)
    model = load_model()
    for _idx, t, img in iter_frames(args.video, target_fps=args.fps, width=args.width):
        frame = draw_zones(img, alpha=0.15)
        draw_boxes(frame, *detect(model, img))
        active = [lab for s, e, lab in events if s <= t <= e]
        score = risk[int(np.searchsorted(risk_t, t, side="right")) - 1][1] if len(risk_t) and t >= risk_t[0] else 0.0
        banner = f"{t:6.1f}s  risk {score:.2f}  " + "  ".join(active)
        cv2.rectangle(frame, (0, 0), (args.width, 30), (0, 0, 0), -1)
        cv2.putText(frame, banner, (8, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (0, 0, 255) if score >= THETA else (255, 255, 255), 2)
        s = strip.copy()
        cx = int(round(t / duration * (args.width - 1)))
        cv2.line(s, (cx, 0), (cx, STRIP_H), (255, 255, 255), 1)
        enc.stdin.write(np.vstack([frame[:h], s]).tobytes())
    enc.stdin.close()
    if enc.wait():
        print("ffmpeg failed", file=sys.stderr)
        return 1
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
