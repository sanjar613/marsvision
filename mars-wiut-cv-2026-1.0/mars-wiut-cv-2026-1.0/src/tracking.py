"""Causal detection + tracking shared by Part A and Part B.

Two layers:
  * `Detector`   – YOLO + ByteTrack on one frame -> rows (tid, cls, x1, y1, x2, y2, conf)
  * `TrackStore` – turns rows into per-track histories (velocity, speeds, ...)

`CausalTracker` = Detector + TrackStore, fed one frame at a time, so all it
produces depends only on the past (safe inside RiskEstimator.step()).
Because the two layers are separate, detector rows can be cached once and
replayed through TrackStore + risk code in seconds (tools/replay.py) — the
replay runs the exact same code path as the live estimator.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import numpy as np

# COCO ids we care about -> short names
ROAD_USERS = {0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
VEHICLES = {"car", "motorcycle", "bus", "truck", "bicycle"}

WEIGHTS_DIR = Path(__file__).resolve().parent.parent / "weights"
DEFAULT_WEIGHTS = WEIGHTS_DIR / "yolo11s.pt"

_MODEL_CACHE: dict[str, object] = {}


def load_model(weights: Path = DEFAULT_WEIGHTS):
    """Load YOLO once per process (the harness creates many estimators)."""
    key = str(weights)
    if key not in _MODEL_CACHE:
        import torch
        from ultralytics import YOLO

        torch.manual_seed(0)
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
        _MODEL_CACHE[key] = YOLO(str(weights))
    return _MODEL_CACHE[key]


@dataclass
class Track:
    tid: int
    cls: str
    hist: deque = field(default_factory=lambda: deque(maxlen=40))  # (t, x1, y1, x2, y2)
    last_t: float = 0.0
    first_t: float = 0.0

    @property
    def box(self) -> np.ndarray:
        return np.array(self.hist[-1][1:], dtype=float)

    @property
    def age(self) -> float:
        return self.last_t - self.first_t

    def velocity(self, window: float = 0.8) -> np.ndarray:
        """Least-squares velocity of the box corners over the last `window` s (px/s)."""
        t_now = self.hist[-1][0]
        pts = np.array([h for h in self.hist if t_now - h[0] <= window], dtype=float)
        if len(pts) < 3:
            return np.zeros(4)
        t = pts[:, 0] - pts[:, 0].mean()
        denom = (t ** 2).sum()
        if denom <= 1e-9:
            return np.zeros(4)
        return (t[:, None] * (pts[:, 1:] - pts[:, 1:].mean(0))).sum(0) / denom

    def ground_velocity(self, window: float = 0.8) -> np.ndarray:
        """Velocity of the bottom-centre point (where the vehicle touches the road)."""
        v = self.velocity(window)
        return np.array([(v[0] + v[2]) / 2, v[3]])

    def speed_history(self, window: float = 2.0, sub: float = 0.4) -> list[float]:
        """Centre speeds (px/s) over short sub-windows, oldest first."""
        t_now = self.hist[-1][0]
        pts = [h for h in self.hist if t_now - h[0] <= window]
        out = []
        i = 0
        while i < len(pts):
            j = i
            while j + 1 < len(pts) and pts[j + 1][0] - pts[i][0] < sub:
                j += 1
            if j > i:
                a, b = np.array(pts[i][1:]), np.array(pts[j][1:])
                ca, cb = (a[:2] + a[2:]) / 2, (b[:2] + b[2:]) / 2
                out.append(float(np.linalg.norm(cb - ca) / (pts[j][0] - pts[i][0])))
            i = j + 1
        return out


class Detector:
    """YOLO + ByteTrack. `__call__(frame)` -> array of rows [tid, cls_id, x1, y1, x2, y2, conf]."""

    def __init__(self, fps: float, stride: int, imgsz: int = 640, conf: float = 0.25,
                 weights: Path = DEFAULT_WEIGHTS, device: str | None = None):
        from ultralytics.trackers.byte_tracker import BYTETracker

        self.model = load_model(weights)
        self.imgsz, self.conf, self.device = imgsz, conf, device
        eff_fps = fps / stride
        args = SimpleNamespace(
            tracker_type="bytetrack", track_high_thresh=0.25, track_low_thresh=0.1,
            new_track_thresh=0.25, track_buffer=int(round(1.5 * eff_fps)),
            match_thresh=0.8, fuse_score=True,
        )
        self.tracker = BYTETracker(args)

    def __call__(self, frame: np.ndarray) -> np.ndarray:
        res = self.model.predict(frame, imgsz=self.imgsz, conf=self.conf, classes=list(ROAD_USERS),
                                 verbose=False, device=self.device)[0]
        det = res.boxes.cpu().numpy()
        out = self.tracker.update(det, frame)
        if not len(out):
            return np.zeros((0, 7), dtype=np.float32)
        # BYTETracker rows: x1, y1, x2, y2, id, score, cls, idx
        return np.stack([out[:, 4], out[:, 6], out[:, 0], out[:, 1], out[:, 2], out[:, 3], out[:, 5]],
                        axis=1).astype(np.float32)


class TrackStore:
    """Keeps short histories for the currently tracked road users."""

    def __init__(self, forget_after: float = 3.0):
        self.tracks: dict[int, Track] = {}
        self.forget_after = forget_after

    def update(self, rows: np.ndarray, t: float) -> list[Track]:
        alive = []
        for tid, cls, x1, y1, x2, y2, _conf in rows:
            tid = int(tid)
            tr = self.tracks.get(tid)
            if tr is None:
                tr = self.tracks[tid] = Track(tid, ROAD_USERS.get(int(cls), "other"), first_t=t)
            tr.hist.append((t, float(x1), float(y1), float(x2), float(y2)))
            tr.last_t = t
            alive.append(tr)
        for tid in [k for k, v in self.tracks.items() if t - v.last_t > self.forget_after]:
            del self.tracks[tid]
        return alive


class CausalTracker:
    """Detector + TrackStore, fed one frame at a time."""

    def __init__(self, fps: float, stride: int, **kw):
        self.detector = Detector(fps, stride, **kw)
        self.store = TrackStore()
        self.last_rows = np.zeros((0, 7), dtype=np.float32)

    @property
    def tracks(self) -> dict[int, Track]:
        return self.store.tracks

    def update(self, frame: np.ndarray, t: float) -> list[Track]:
        self.last_rows = self.detector(frame)
        return self.store.update(self.last_rows, t)
