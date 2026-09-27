"""Part B: causal accident-risk score from tracked road users.

Per processed frame:
    tracks -> pair features: footprint time-to-collision (TTC), closing speed,
              deceleration-rate-to-avoid-crash (DRAC), box-overlap growth;
              filters for adjacent/oncoming lanes, standing queues, young tracks
           -> per-track features: braking, swerving, driving against the usual
              flow of that part of the image (flow map, learned online and
              optionally seeded with a prior from the organizer samples)
           -> 1-s memory (max / rise of the best pair score)
           -> probability: logistic-regression calibrator (weights/risk_calibrator.json)
              or a hand formula when no calibrator is present
           -> smoothing + alarm hysteresis (+ no alarms during tracker warm-up)

Distances are in box heights, so no camera calibration is needed.
Literature note: TTC is the strongest surrogate safety measure but is reliable
only ~2 s ahead; acceleration-based measures are the next best -> we combine both.
"""
from __future__ import annotations

import json
import math
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from .tracking import VEHICLES, Track

WEIGHTS = Path(__file__).resolve().parent.parent / "weights"
CALIBRATOR_PATH = WEIGHTS / "risk_calibrator.json"
FLOW_PRIOR_PATH = WEIGHTS / "flow_prior.json"


@dataclass
class RiskConfig:
    horizon: float = 3.0         # how far ahead we extrapolate (s)
    dt: float = 0.1              # extrapolation step (s)
    ttc_tau: float = 1.2         # pair risk = exp(-ttc / tau)
    min_closing: float = 0.3     # ignore pairs closing slower than this (box heights / s)
    foot_frac: float = 0.35      # bottom part of the box used as ground footprint
    max_pairs_dist: float = 6.0  # only consider pairs closer than this (box heights)
    min_age: float = 0.5         # ignore tracks younger than this (s): ID flicker
    moving_speed: float = 0.3    # a track "moves" above this ground speed (box heights / s)
    lane_cos: float = 0.9        # |cos(heading angle)| above this = parallel or opposite
    lane_sep: float = 0.6        # lateral gap (box widths) that means "different lane"
    touch_rule: bool = False     # count already-overlapping footprints as TTC=0 (off: occlusion in dense traffic)
    brake_drop: float = 0.55     # speed must fall by this fraction ...
    brake_min_speed: float = 0.8  # ... from at least this speed (box heights / s)
    memory: float = 1.0          # temporal features look back this long (s)
    flow_grid: tuple = (16, 9)   # flow-map cells (x, y)
    flow_min_count: float = 15.0  # a cell needs this many observations before it is trusted
    flow_min_coherence: float = 0.6  # ... and this directional agreement (|mean unit vector|)
    warmup: float = 3.0          # no alarms before this time (tracker/velocity warm-up)
    ema_alpha: float = 0.35
    alarm_on: float = 0.55       # smoothed risk needed to fire an alarm
    alarm_frames: int = 3        # ... for this many processed frames in a row
    alarm_hold: float = 2.5      # keep the alarm on this long (s); merge window is 2 s
    idle_cap: float = 0.45       # score cap when no alarm is active (stays below theta=0.5)
    use_lane_filter: bool = True
    use_queue_filter: bool = True

    @classmethod
    def from_dict(cls, d: dict | None) -> "RiskConfig":
        base = asdict(cls())
        base.update({k: (tuple(v) if k == "flow_grid" else v) for k, v in (d or {}).items() if k in base})
        return cls(**base)


FEATURES = ["max_pair", "ttc_score", "closing", "log_drac", "iou_rise", "brake", "brake_conflict",
            "swerve", "flow_anom", "log_conflicts", "pair_max_1s", "pair_rise"]


# --------------------------------------------------------------------------- geometry
def footprint(box: np.ndarray, frac: float) -> np.ndarray:
    x1, y1, x2, y2 = box
    h = y2 - y1
    return np.array([x1, y2 - frac * h, x2, y2])


def overlap(a: np.ndarray, b: np.ndarray) -> bool:
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def iou(a, b) -> float:
    iw = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    ih = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = iw * ih
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / u if u > 0 else 0.0


def centre(b: np.ndarray) -> np.ndarray:
    return np.array([(b[0] + b[2]) / 2, (b[1] + b[3]) / 2])


def ground_point(b) -> np.ndarray:
    return np.array([(b[0] + b[2]) / 2, b[3]])


def box_at(tr: Track, t: float):
    """Most recent box of `tr` at or before time t (None if the track is younger)."""
    for h in reversed(tr.hist):
        if h[0] <= t + 1e-6:
            return np.array(h[1:], dtype=float)
    return None


@dataclass
class State:
    """Per-frame kinematics of one track, computed once (not once per pair)."""
    tr: Track
    box: np.ndarray
    vel: np.ndarray       # corner velocities (px/s)
    gvel: np.ndarray      # ground-point velocity (px/s)
    h: float
    w: float

    @property
    def speed(self) -> float:  # box heights / s
        return float(np.linalg.norm(self.gvel)) / self.h


def make_state(tr: Track) -> State:
    b = tr.box
    v = tr.velocity()
    return State(tr, b, v, np.array([(v[0] + v[2]) / 2, v[3]]), max(1.0, b[3] - b[1]), max(1.0, b[2] - b[0]))


def separate_lanes(a: State, b: State, cfg: RiskConfig, scale_w: float) -> bool:
    """True if the two road users drive parallel (or head-on) in different lanes."""
    na, nb = np.linalg.norm(a.gvel), np.linalg.norm(b.gvel)
    if na < 1e-6 or nb < 1e-6:
        return False
    ua, ub = a.gvel / na, b.gvel / nb
    if abs(float(ua @ ub)) < cfg.lane_cos:
        return False  # crossing paths: keep
    d = ground_point(b.box) - ground_point(a.box)
    lateral = abs(d[0] * ua[1] - d[1] * ua[0])  # distance perpendicular to a's heading
    return lateral > cfg.lane_sep * scale_w


def pair_ttc(a: State | Track, b: State | Track, cfg: RiskConfig) -> tuple[float, float, float] | None:
    """(ttc_sec, closing_speed, gap) if the two footprints are on a collision
    course within cfg.horizon, else None. Speeds/gaps in box heights."""
    if isinstance(a, Track):
        a = make_state(a)
    if isinstance(b, Track):
        b = make_state(b)
    ba, bb = a.box, b.box
    scale = 0.5 * (a.h + b.h)
    scale_w = 0.5 * (a.w + b.w)
    ca, cb = centre(ba), centre(bb)
    dist = float(np.linalg.norm(ca - cb)) / scale
    if dist > cfg.max_pairs_dist:
        return None
    if cfg.use_queue_filter and max(a.speed, b.speed) < cfg.moving_speed:
        return None  # both standing (queue / parked)
    rel_pos = cb - ca
    rel_vel = centre(b.vel) - centre(a.vel)
    closing = -float(rel_pos @ rel_vel) / (np.linalg.norm(rel_pos) + 1e-6) / scale
    if closing < cfg.min_closing:
        return None
    if cfg.use_lane_filter and separate_lanes(a, b, cfg, scale_w):
        return None
    fa, fb = footprint(ba, cfg.foot_frac), footprint(bb, cfg.foot_frac)
    gap = max(0.0, max(fa[0], fb[0]) - min(fa[2], fb[2]), max(fa[1], fb[1]) - min(fa[3], fb[3])) / scale
    if overlap(fa, fb):
        # already overlapping in the image: usually occlusion in dense traffic
        return (0.0, closing, 0.0) if cfg.touch_rule and closing > 2 * cfg.min_closing else None
    va, vb = a.vel, b.vel
    fva = np.array([va[0], va[3], va[2], va[3]])
    fvb = np.array([vb[0], vb[3], vb[2], vb[3]])
    tt = np.arange(1, int(cfg.horizon / cfg.dt) + 1)[:, None] * cfg.dt
    A, B = fa + fva * tt, fb + fvb * tt
    hit = (np.minimum(A[:, 2], B[:, 2]) > np.maximum(A[:, 0], B[:, 0])) & \
          (np.minimum(A[:, 3], B[:, 3]) > np.maximum(A[:, 1], B[:, 1]))
    if hit.any():
        return (float(tt[int(np.argmax(hit)), 0]), closing, gap)
    return None


def braking_score(tr: Track, cfg: RiskConfig) -> float:
    b = tr.box
    h = max(1.0, b[3] - b[1])
    sp = [s / h for s in tr.speed_history()]
    if len(sp) < 3:
        return 0.0
    peak, now = max(sp[:-1]), sp[-1]
    if peak < cfg.brake_min_speed:
        return 0.0
    drop = (peak - now) / peak
    return float(np.clip((drop - cfg.brake_drop) / (1 - cfg.brake_drop), 0, 1))


def swerve_score(s: State, cfg: RiskConfig) -> float:
    """Heading change (0..1 = 0..90 deg) over the last second for a moving vehicle."""
    if s.speed < 2 * cfg.moving_speed:
        return 0.0
    tr = s.tr
    t_now = tr.hist[-1][0]
    pts = np.array([h for h in tr.hist if t_now - 1.6 <= h[0] <= t_now - 1.0], dtype=float)
    if len(pts) < 2:
        return 0.0
    g0 = np.array([(pts[0, 1] + pts[0, 3]) / 2, pts[0, 4]])
    g1 = np.array([(pts[-1, 1] + pts[-1, 3]) / 2, pts[-1, 4]])
    v_old = (g1 - g0) / max(1e-3, pts[-1, 0] - pts[0, 0])
    n0, n1 = np.linalg.norm(v_old), np.linalg.norm(s.gvel)
    if n0 < 1e-6 or n1 < 1e-6:
        return 0.0
    ang = math.acos(float(np.clip(v_old @ s.gvel / (n0 * n1), -1, 1)))
    return float(min(1.0, ang / (math.pi / 2)))


class FlowMap:
    """Usual direction of motion per image cell. Updated online (causal); can
    be seeded with a prior learned from normal traffic of the same camera."""

    def __init__(self, width: int, height: int, cfg: RiskConfig, prior: dict | None = None):
        self.w, self.h = max(1, int(width)), max(1, int(height))
        self.gx, self.gy = cfg.flow_grid
        self.cfg = cfg
        self.sum = np.zeros((self.gy, self.gx, 2))
        self.cnt = np.zeros((self.gy, self.gx))
        if prior and prior.get("width") == self.w and prior.get("height") == self.h \
                and tuple(prior.get("grid", ())) == (self.gx, self.gy):
            self.sum += np.array(prior["sum"], dtype=float)
            self.cnt += np.array(prior["count"], dtype=float)

    def cell(self, p) -> tuple[int, int]:
        cx = int(np.clip(p[0] / self.w * self.gx, 0, self.gx - 1))
        cy = int(np.clip(p[1] / self.h * self.gy, 0, self.gy - 1))
        return cy, cx

    def anomaly(self, s: State) -> float:
        """0 = moving with the usual flow, 1 = moving exactly against it."""
        if s.speed < 2 * self.cfg.moving_speed:
            return 0.0
        cy, cx = self.cell(ground_point(s.box))
        n = self.cnt[cy, cx]
        if n < self.cfg.flow_min_count:
            return 0.0
        mean = self.sum[cy, cx] / n
        if np.linalg.norm(mean) < self.cfg.flow_min_coherence:
            return 0.0  # cell with mixed directions (intersection centre): no opinion
        u = s.gvel / (np.linalg.norm(s.gvel) + 1e-9)
        return float((1.0 - u @ (mean / np.linalg.norm(mean))) / 2.0)

    def update(self, states: list[State]) -> None:
        for s in states:
            if s.tr.cls in VEHICLES and s.speed >= 2 * self.cfg.moving_speed:
                cy, cx = self.cell(ground_point(s.box))
                self.sum[cy, cx] += s.gvel / (np.linalg.norm(s.gvel) + 1e-9)
                self.cnt[cy, cx] += 1


# --------------------------------------------------------------------------- per-frame
def frame_features(tracks: list[Track], cfg: RiskConfig, flow: FlowMap | None = None) -> dict:
    """Instantaneous summary of all pairs / tracks in this frame."""
    users = [make_state(t) for t in tracks if len(t.hist) >= 3 and t.age >= cfg.min_age]
    min_ttc, max_pair, max_closing, max_drac, max_iou_rise, n_conflicts = cfg.horizon, 0.0, 0.0, 0.0, 0.0, 0
    best_pair, in_conflict = None, set()
    if len(users) >= 2:
        C = np.array([centre(u.box) for u in users])
        H = np.array([u.h for u in users])
        D = np.linalg.norm(C[:, None] - C[None], axis=-1) / (0.5 * (H[:, None] + H[None]))
        veh = np.array([u.tr.cls in VEHICLES for u in users])
        ii, jj = np.nonzero(np.triu(D <= cfg.max_pairs_dist, 1) & (veh[:, None] | veh[None]))
        t_now = max(u.tr.last_t for u in users)
        for i, j in zip(ii.tolist(), jj.tolist()):
            a, b = users[i], users[j]
            if D[i, j] <= 2.0 and veh[i] and veh[j]:
                pa, pb = box_at(a.tr, t_now - 0.5), box_at(b.tr, t_now - 0.5)
                if pa is not None and pb is not None:
                    max_iou_rise = max(max_iou_rise, iou(a.box, b.box) - iou(pa, pb))
            r = pair_ttc(a, b, cfg)
            if r is None:
                continue
            ttc, closing, gap = r
            n_conflicts += 1
            in_conflict.update((a.tr.tid, b.tr.tid))
            pr = math.exp(-ttc / cfg.ttc_tau) * min(1.0, closing / 1.5)
            if pr > max_pair:
                max_pair, best_pair = pr, (a.tr.tid, b.tr.tid)
            min_ttc = min(min_ttc, ttc)
            max_closing = max(max_closing, closing)
            max_drac = max(max_drac, closing ** 2 / (2 * max(gap, 0.2)))
    vehicles = [u for u in users if u.tr.cls in VEHICLES]
    brakes = {u.tr.tid: braking_score(u.tr, cfg) for u in vehicles}
    brake = max(brakes.values(), default=0.0)
    brake_conflict = max((v for k, v in brakes.items() if k in in_conflict), default=0.0)
    swerve = max((swerve_score(u, cfg) for u in vehicles), default=0.0)
    flow_anom = max((flow.anomaly(u) for u in vehicles), default=0.0) if flow is not None else 0.0
    if flow is not None:
        flow.update(vehicles)
    return {
        "n_users": len(users), "n_conflicts": n_conflicts, "min_ttc": min_ttc,
        "max_pair": max_pair, "max_closing": max_closing, "drac": max_drac, "iou_rise": max(0.0, max_iou_rise),
        "brake": brake, "brake_conflict": brake_conflict, "swerve": swerve, "flow_anom": flow_anom,
        "best_pair": best_pair,
    }


def raw_risk(f: dict) -> float:
    """Hand-tuned combination (used when no calibrator is present)."""
    r = 1.0 - (1.0 - f["max_pair"]) * (1.0 - 0.5 * f["brake_conflict"])
    return float(np.clip(r, 0.0, 1.0))


class Calibrator:
    """Logistic regression over FEATURES, weights in a small JSON file."""

    def __init__(self, d: dict):
        self.features = d["features"]
        self.mean = np.array(d["mean"], dtype=float)
        self.std = np.array(d["std"], dtype=float)
        self.w = np.array(d["w"], dtype=float)
        self.b = float(d["b"])
        self.config = d.get("config", {})

    @classmethod
    def load(cls, path: Path = CALIBRATOR_PATH) -> "Calibrator | None":
        return cls(json.loads(Path(path).read_text())) if Path(path).is_file() else None

    def __call__(self, x: dict) -> float:
        v = (np.array([x[k] for k in self.features], dtype=float) - self.mean) / self.std
        z = float(v @ self.w + self.b)
        return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))


class AlarmSmoother:
    """EMA + hysteresis so we fire one long alarm instead of many short ones."""

    def __init__(self, cfg: RiskConfig):
        self.cfg = cfg
        self.ema, self.above, self.alarm_until = 0.0, 0, -1.0

    def __call__(self, r: float, t: float) -> float:
        c = self.cfg
        self.ema = c.ema_alpha * r + (1 - c.ema_alpha) * self.ema
        self.above = self.above + 1 if self.ema >= c.alarm_on else 0
        if self.above >= c.alarm_frames and t >= c.warmup:
            self.alarm_until = t + c.alarm_hold
        if t <= self.alarm_until:
            return float(max(0.5, min(1.0, 0.5 + 0.5 * self.ema)))
        # below the alarm: keep the ranking information but stay under 0.5
        return float(min(c.idle_cap, c.idle_cap * self.ema / max(c.alarm_on, 1e-6)))


def load_flow_prior(path: Path = FLOW_PRIOR_PATH) -> dict | None:
    return json.loads(Path(path).read_text()) if Path(path).is_file() else None


class RiskModel:
    """Everything after tracking. Used by RiskEstimator (live) and tools/replay.py."""

    def __init__(self, cfg: RiskConfig | None = None, calibrator: Calibrator | None = None,
                 frame_size: tuple[int, int] | None = None, flow_prior: dict | None = None):
        self.cfg = cfg or RiskConfig()
        self.cal = calibrator
        self.smoother = AlarmSmoother(self.cfg)
        self.flow = FlowMap(*frame_size, self.cfg, flow_prior) if frame_size else None
        self.past: deque = deque()  # (t, max_pair)

    def features(self, tracks: list[Track], t: float) -> dict:
        f = frame_features(tracks, self.cfg, self.flow)
        self.past.append((t, f["max_pair"]))
        while self.past and t - self.past[0][0] > self.cfg.memory:
            self.past.popleft()
        vals = [p for _, p in self.past]
        f.update(
            ttc_score=1.0 - f["min_ttc"] / self.cfg.horizon,
            closing=min(f["max_closing"], 5.0) / 5.0,
            log_drac=math.log1p(min(f["drac"], 50.0)),
            log_conflicts=math.log1p(f["n_conflicts"]),
            pair_max_1s=float(np.max(vals)),
            pair_rise=float(vals[-1] - vals[0]),
        )
        return f

    def step(self, tracks: list[Track], t: float) -> tuple[float, dict]:
        f = self.features(tracks, t)
        p = self.cal(f) if self.cal is not None else raw_risk(f)
        score = self.smoother(p, t)
        f.update(t=round(t, 3), prob=p, score=score)
        return score, f
