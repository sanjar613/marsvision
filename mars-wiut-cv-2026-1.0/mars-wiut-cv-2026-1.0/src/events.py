"""Part A — rule-based event detection from sparse frame samples + the scene layout.

    sample_frames()   keyframes only when they are ≤ ~1 s apart (cheap), else a 2 fps full decode
    detect()          YOLO11s at imgsz 1280 on 1920-px frames, road users only, no tracker
    stopped_vehicle_segments(), jaywalking_segments()   rules on boxes + src/scene.py polygons

Boxes are normalised to [0, 1] (x1, y1, x2, y2), the same frame as the scene polygons.
The rule functions take plain `Sample`s, so tests can feed them synthetic boxes.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np

from .scene import APPROACHES, CROSSINGS, inside, inside_any, on_carriageway
from .tracking import ROAD_USERS, load_model
from .video import video_info

SAMPLE_WIDTH = 1920
DETECT_IMGSZ = 1280        # pedestrians are small at this distance
DETECT_CONF = 0.35
KEYFRAME_MAX_GAP = 1.05    # s; a 30-frame GOP at 29.97 fps is 1.001 s apart
FULL_DECODE_FPS = 2.0
TIME_GUARD = 0.8           # stop sampling after this fraction of the video duration (wall time)

STOP_CLASSES = ["car", "bus", "truck", "motorcycle"]
STOP_IOU = 0.6
STOP_MAX_GAP = 3.0         # s a stopped vehicle may be missed (occlusion)
STOP_MAX_DRIFT = 0.25      # centre movement, in box heights, that counts as "moved again"
STOP_MIN_SEC = 12.0        # the definition says 10 s; margin for sparse sampling
QUEUE_MIN_SEC = 150.0      # in a signal approach: longer than any red phase

RIDER_CLASSES = ["bicycle", "motorcycle"]
CABIN_CLASSES = ["car", "bus", "truck"]
RIDER_COVER = 0.3          # share of a person box covered by a two-wheeler box -> rider
WALK_MERGE_GAP = 1.5
WALK_MIN_SEC = 1.5
WALK_MIN_HITS = 2
STATIC_PERSON_IOU = 0.5    # a "person" box that keeps this IoU with where it first stood ...
STATIC_PERSON_SEC = 15.0   # ... for this long is not crossing: a pole, a road worker, someone waiting
STATIC_PERSON_GAP = 10.0   # s; such false "persons" flicker (at night), so allow long gaps between hits

# video file name -> wall seconds spent in detect_events. Part B reads it to plan its own
# frame stride (timing only, never Part A's results).
PART_A_WALL: dict[str, float] = {}


@dataclass
class Sample:
    t: float
    boxes: np.ndarray   # (N, 4) normalised x1, y1, x2, y2
    names: np.ndarray   # (N,) class names from ROAD_USERS


# ---------------------------------------------------------------- frames + detection

def keyframe_gap(path: str | Path, probe_sec: float = 30.0) -> float:
    """Largest gap (s) between keyframes in the first `probe_sec`, from packet headers only."""
    import av

    with av.open(str(path)) as c:
        s = c.streams.video[0]
        start = s.start_time or 0
        keys = []
        for pkt in c.demux(s):
            if pkt.pts is None:
                continue
            t = float((pkt.pts - start) * s.time_base)
            if pkt.is_keyframe:
                keys.append(t)
            if t > probe_sec:
                break
    return float(np.diff(sorted(keys)).max()) if len(keys) > 1 else float("inf")


def sample_frames(path: str | Path, width: int = SAMPLE_WIDTH) -> Iterator[tuple[float, np.ndarray]]:
    """Yield (t_sec, BGR frame) about once per second (keyframes) or twice per second (full decode).

    t_sec = frame index / fps, the harness clock; the index comes from pts relative to the
    stream start, so skipped frames do not shift it.
    """
    import av

    keys_only = keyframe_gap(path) <= KEYFRAME_MAX_GAP
    with av.open(str(path)) as c:
        s = c.streams.video[0]
        s.thread_type = "AUTO"
        if keys_only:
            s.codec_context.skip_frame = "NONKEY"
        fps = float(s.average_rate or s.guessed_rate or 25.0)
        stride = max(1, round(fps / FULL_DECODE_FPS))
        start = s.start_time or 0
        w, h = s.codec_context.width, s.codec_context.height
        size = {"width": width, "height": int(round(h * width / w / 2) * 2)} if width < w else {}
        for fr in c.decode(s):
            if fr.pts is None:
                continue
            idx = int(round(float((fr.pts - start) * s.time_base) * fps))
            if keys_only or idx % stride == 0:
                yield idx / fps, fr.to_ndarray(format="bgr24", **size)


def detect(model, frame: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    res = model.predict(frame, imgsz=DETECT_IMGSZ, conf=DETECT_CONF, classes=list(ROAD_USERS),
                        verbose=False)[0]
    b = res.boxes.cpu().numpy()
    h, w = frame.shape[:2]
    names = np.array([ROAD_USERS[int(c)] for c in b.cls], dtype=object)
    return b.xyxy / [w, h, w, h], names


# ---------------------------------------------------------------- box geometry

def foot(boxes: np.ndarray) -> np.ndarray:
    """Bottom-centre point, where a road user touches the ground."""
    return np.stack([(boxes[:, 0] + boxes[:, 2]) / 2, boxes[:, 3]], axis=1)


def _intersection(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    w = np.minimum(a[:, None, 2], b[None, :, 2]) - np.maximum(a[:, None, 0], b[None, :, 0])
    h = np.minimum(a[:, None, 3], b[None, :, 3]) - np.maximum(a[:, None, 1], b[None, :, 1])
    return np.clip(w, 0, None) * np.clip(h, 0, None)


def _area(a: np.ndarray) -> np.ndarray:
    return (a[:, 2] - a[:, 0]) * (a[:, 3] - a[:, 1])


def iou_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    inter = _intersection(a, b)
    return inter / (_area(a)[:, None] + _area(b)[None, :] - inter + 1e-12)


def merge_segments(segs: list[list[float]], gap: float = 0.0) -> list[list[float]]:
    out: list[list[float]] = []
    for s, e in sorted(segs):
        if out and s <= out[-1][1] + gap:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


# ---------------------------------------------------------------- stopped_vehicle

@dataclass
class _Stop:
    anchor: np.ndarray   # box when the vehicle was first seen standing here
    box: np.ndarray      # latest box
    t0: float
    t1: float

    @property
    def min_sec(self) -> float:
        in_queue = inside_any(foot(self.anchor[None]), APPROACHES)[0]
        return QUEUE_MIN_SEC if in_queue else STOP_MIN_SEC


def stopped_vehicle_segments(samples: list[Sample], end: float | None = None) -> list[list[float]]:
    """Vehicles whose box stays put on the carriageway.

    end: the video duration when every sample was processed; a vehicle still standing
    at the last sample then runs to the end of the video (annotation convention).
    """
    active: list[_Stop] = []
    segs: list[list[float]] = []

    def close(c: _Stop) -> None:
        if c.t1 - c.t0 >= c.min_sec:
            segs.append([c.t0, c.t1])

    for s in samples:
        keep = np.isin(s.names, STOP_CLASSES)
        boxes, names = s.boxes[keep], s.names[keep]
        ft = foot(boxes)
        ok = on_carriageway(ft) & ~((names == "bus") & inside(ft, "bus_stop"))
        boxes = boxes[ok]

        for c in active:
            if s.t - c.t1 > STOP_MAX_GAP:
                close(c)
        active = [c for c in active if s.t - c.t1 <= STOP_MAX_GAP]

        iou = iou_matrix(np.array([c.box for c in active]).reshape(-1, 4), boxes)
        used_c, used_b = set(), set()
        for ci, bi in sorted(zip(*np.nonzero(iou >= STOP_IOU)), key=lambda p: -iou[p]):
            if ci in used_c or bi in used_b:
                continue
            used_c.add(ci)
            used_b.add(bi)
            c, b = active[ci], boxes[bi]
            drift = np.linalg.norm((b[:2] + b[2:]) / 2 - (c.anchor[:2] + c.anchor[2:]) / 2)
            if drift > STOP_MAX_DRIFT * (c.anchor[3] - c.anchor[1]):
                close(c)
                active[ci] = _Stop(b, b, s.t, s.t)
            else:
                c.box, c.t1 = b, s.t
        active += [_Stop(b, b, s.t, s.t) for bi, b in enumerate(boxes) if bi not in used_b]

    for c in active:
        if end is not None and end - c.t1 <= STOP_MAX_GAP:
            c.t1 = end
        close(c)
    return merge_segments(segs)


# ---------------------------------------------------------------- jaywalking

def static_people(samples: list[Sample]) -> list[np.ndarray]:
    """Per sample, a mask over its person boxes: True if that "person" stays in one place for
    STATIC_PERSON_SEC or more over the whole video (Part A may look at the future)."""
    anchors: list[list] = []       # [box, t_first, t_last]
    ids: list[np.ndarray] = []     # per sample: anchor index of each person box
    for s in samples:
        people = s.boxes[s.names == "person"]
        live = [k for k, a in enumerate(anchors) if s.t - a[2] <= STATIC_PERSON_GAP]
        iou = iou_matrix(np.array([anchors[k][0] for k in live]).reshape(-1, 4), people)
        cid = np.full(len(people), -1)
        used = set()
        for li, bi in sorted(zip(*np.nonzero(iou >= STATIC_PERSON_IOU)), key=lambda p: -iou[p]):
            if li in used or cid[bi] >= 0:
                continue
            used.add(li)
            cid[bi] = live[li]
            anchors[live[li]][2] = s.t
        for bi in np.nonzero(cid < 0)[0]:
            anchors.append([people[bi], s.t, s.t])
            cid[bi] = len(anchors) - 1
        ids.append(cid)
    lifetime = np.array([a[2] - a[1] for a in anchors])
    return [lifetime[c] >= STATIC_PERSON_SEC if len(c) else np.zeros(0, bool) for c in ids]


def jaywalker_present(s: Sample, static: np.ndarray | None = None) -> bool:
    """A pedestrian on the carriageway outside the zebra crossings and the bus stop kerb."""
    people = s.boxes[s.names == "person"]
    if not len(people):
        return False
    ft = foot(people)
    on_road = on_carriageway(ft) & ~inside_any(ft, CROSSINGS) & ~inside(ft, "bus_stop")
    two_wheel = s.boxes[np.isin(s.names, RIDER_CLASSES)]
    rider = (_intersection(people, two_wheel) / _area(people)[:, None] >= RIDER_COVER).any(1)
    cabins = s.boxes[np.isin(s.names, CABIN_CLASSES)]
    in_cabin = ((ft[:, None, 0] >= cabins[None, :, 0]) & (ft[:, None, 0] <= cabins[None, :, 2])
                & (ft[:, None, 1] >= cabins[None, :, 1]) & (ft[:, None, 1] <= cabins[None, :, 3])).any(1)
    moving = ~static if static is not None else np.ones(len(people), bool)
    return bool((on_road & ~rider & ~in_cabin & moving).any())


def jaywalking_segments(samples: list[Sample]) -> list[list[float]]:
    hits = [s.t for s, st in zip(samples, static_people(samples)) if jaywalker_present(s, st)]
    runs: list[list[float]] = []
    for t in hits:
        if runs and t - runs[-1][-1] <= WALK_MERGE_GAP:
            runs[-1].append(t)
        else:
            runs.append([t])
    return [[r[0], r[-1]] for r in runs if len(r) >= WALK_MIN_HITS and r[-1] - r[0] >= WALK_MIN_SEC]


# ---------------------------------------------------------------- entry point

def detect_events(video_path: str) -> list[list]:
    t_start = time.perf_counter()
    try:
        duration = video_info(video_path)["duration"]
        model = load_model()
        samples, complete = [], True
        for t, frame in sample_frames(video_path):
            if time.perf_counter() - t_start > TIME_GUARD * duration:
                complete = False
                break
            samples.append(Sample(t, *detect(model, frame)))
        events = [[s, e, "stopped_vehicle"]
                  for s, e in stopped_vehicle_segments(samples, duration if complete else None)]
        events += [[s, e, "jaywalking"] for s, e in jaywalking_segments(samples)]
        return sorted(events)
    finally:
        PART_A_WALL[Path(video_path).name] = time.perf_counter() - t_start
