#!/usr/bin/env python3
"""Website material: one picture per moment of every Part A event, and a timeline per video.

    python tools/export_examples.py --video samples/C3896.MP4 --pred predictions_samples.json --out examples/

For each event it saves three annotated frames (just after the start, the middle, just before
the end) as examples/<video>/<label>_<start>-<end>_<a|b|c>.jpg. The road users that make the
event are drawn thick and red; all other detections are thin (people orange, vehicles cyan).
It also saves examples/<video>/timeline.png: the event bars and the Part B risk curve.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.events import (CABIN_CLASSES, RIDER_CLASSES, RIDER_COVER, STOP_CLASSES, STOP_IOU,  # noqa: E402
                        _area, _intersection, detect, foot, iou_matrix)
from src.scene import CROSSINGS, inside, inside_any, on_carriageway  # noqa: E402
from src.tracking import load_model  # noqa: E402
from tools.render_scene import draw_boxes, draw_zones, read_frame  # noqa: E402

OUT_W = 1280
RED = (40, 40, 230)


def jaywalkers(boxes: np.ndarray, names: np.ndarray) -> np.ndarray:
    """Mask of person boxes that match the jaywalking rule in this single frame."""
    mask = np.zeros(len(boxes), bool)
    people = names == "person"
    if not people.any():
        return mask
    p = boxes[people]
    ft = foot(p)
    ok = on_carriageway(ft) & ~inside_any(ft, CROSSINGS) & ~inside(ft, "bus_stop")
    two = boxes[np.isin(names, RIDER_CLASSES)]
    ok &= ~((_intersection(p, two) / _area(p)[:, None] >= RIDER_COVER).any(1))
    cab = boxes[np.isin(names, CABIN_CLASSES)]
    ok &= ~(((ft[:, None, 0] >= cab[None, :, 0]) & (ft[:, None, 0] <= cab[None, :, 2])
             & (ft[:, None, 1] >= cab[None, :, 1]) & (ft[:, None, 1] <= cab[None, :, 3])).any(1))
    mask[np.nonzero(people)[0][ok]] = True
    return mask


def standing(boxes: np.ndarray, names: np.ndarray, other: np.ndarray, other_names: np.ndarray) -> np.ndarray:
    """Mask of vehicle boxes on the carriageway that are still in the same place in `other`."""
    veh = np.isin(names, STOP_CLASSES) & on_carriageway(foot(boxes))
    ov = other[np.isin(other_names, STOP_CLASSES)]
    if not veh.any() or not len(ov):
        return np.zeros(len(boxes), bool)
    same = (iou_matrix(boxes, ov) >= STOP_IOU).any(1)
    return veh & same


def annotate(img, boxes, names, hot, title):
    out = draw_zones(img)
    draw_boxes(out, boxes, names)
    h, w = out.shape[:2]
    lw = max(3, w // 500)
    for (x1, y1, x2, y2) in boxes[hot] * [w, h, w, h]:
        cv2.rectangle(out, (int(x1), int(y1)), (int(x2), int(y2)), RED, lw)
    out = cv2.resize(out, (OUT_W, int(OUT_W * h / w)))
    cv2.rectangle(out, (0, 0), (OUT_W, 40), (0, 0, 0), -1)
    cv2.putText(out, title, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return out


def timeline(name: str, duration: float, events: list, risk: list, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"stopped_vehicle": "#2a78d6", "jaywalking": "#eb6834"}
    labels = [lab for lab in colors if any(e[2] == lab for e in events)]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 3.6), sharex=True,
                                   gridspec_kw={"height_ratios": [max(1, len(labels)), 1.4]})
    for row, lab in enumerate(labels):
        for s, e, l2 in events:
            if l2 == lab:
                ax1.barh(row, e - s, left=s, height=0.6, color=colors[lab])
    ax1.set_yticks(range(len(labels)))
    ax1.set_yticklabels(labels)
    ax1.invert_yaxis()
    ax1.set_title(f"{name}: Part A events and Part B risk", loc="left")
    if risk:
        t, r = zip(*risk)
        ax2.plot(t, r, color="#4a3aa7", lw=1.2)
    ax2.axhline(0.5, color="#888", ls="--", lw=0.8)
    ax2.set_ylim(0, 1)
    ax2.set_ylabel("risk")
    ax2.set_xlabel("time (s)")
    ax2.set_xlim(0, duration)
    for ax in (ax1, ax2):
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--pred", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    video = Path(args.video)
    entry = json.loads(Path(args.pred).read_text())["videos"][video.name]
    out = Path(args.out) / video.stem
    out.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video))
    duration = (cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) / (cap.get(cv2.CAP_PROP_FPS) or 25.0)
    model, n = load_model(), 0
    for s, e, label in entry["events"]:
        times = [min(s + 0.5, e), (s + e) / 2, max(e - 0.5, s)]
        dets = []
        for t in times:
            img = read_frame(cap, t)
            dets.append((img, *detect(model, img)) if img is not None else None)
        for k, (d, t) in enumerate(zip(dets, times)):
            if d is None:
                continue
            img, boxes, names = d
            if label == "jaywalking":
                hot = jaywalkers(boxes, names)
            else:   # the vehicle that is in the same place at the other end of the event
                ref = dets[2 if k < 2 else 0] or d
                hot = standing(boxes, names, ref[1], ref[2])
            title = f"{video.name}  {label}  {s:.1f}-{e:.1f}s   frame at {t:.1f}s"
            cv2.imwrite(str(out / f"{label}_{s:06.1f}-{e:06.1f}_{'abc'[k]}.jpg"),
                        annotate(img, boxes, names, hot, title), [cv2.IMWRITE_JPEG_QUALITY, 80])
            n += 1
    cap.release()
    timeline(video.name, duration, entry["events"], entry.get("risk", []), out / "timeline.png")
    print(f"wrote {n} pictures + timeline.png to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
