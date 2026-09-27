"""Scene layout of the organizer camera (the fixed CCTV view of the intersection).

The task allows hard-coding the scene ("camera.md facts: lanes, stop lines,
crossings"). We drew these polygons once on a sample frame (1600x900 copy of a
3840x2160 frame) and store them normalised to [0, 1], so they work at any
resolution. `tools/render_scene.py` draws them on a frame for checking.

    road        carriageway (both directions + intersection box)
    parking     kerb-side parking strip on the left (not carriageway)
    median      raised median of the avenue; island = its end + sign island
    c1, c2, c3  zebra crossings (drawn a little wider than the paint)
    t1..t3      pedestrian refuge islands (pink triangles)
    bus_stop    kerb lane in front of the bus stop (far side)
    q1, q2      signal approach lanes where queues form at red
"""
from __future__ import annotations

import numpy as np

_REF_W, _REF_H = 1600.0, 900.0

_ZONES_PX: dict[str, list[tuple[int, int]]] = {
    "road": [(100, 90), (400, 105), (600, 160), (950, 225), (1030, 245), (1380, 378), (1600, 420),
             (1600, 900), (0, 900), (0, 680), (150, 615), (290, 548), (270, 480), (160, 430),
             (60, 300), (60, 140)],
    "parking": [(0, 290), (160, 290), (200, 440), (0, 440)],
    "median": [(100, 92), (880, 375), (880, 405), (100, 108)],
    "island": [(880, 370), (1060, 380), (1100, 440), (1095, 480), (985, 475), (880, 410)],
    "c1": [(250, 470), (1000, 395), (1015, 485), (295, 565)],
    "c2": [(1045, 385), (1450, 345), (1475, 435), (1075, 475)],
    "c3": [(130, 600), (320, 590), (720, 900), (420, 900)],
    "t1": [(429, 640), (550, 552), (633, 619)],
    "t2": [(571, 704), (677, 672), (794, 704), (783, 741), (593, 746)],
    "t3": [(111, 778), (275, 704), (354, 762), (339, 783)],
    "bus_stop": [(480, 95), (960, 190), (960, 240), (480, 150)],
    "q1": [(60, 130), (107, 100), (1000, 427), (1000, 437), (287, 500), (200, 440), (160, 290), (60, 200)],
    "q2": [(1080, 470), (1460, 430), (1600, 420), (1600, 620), (1100, 560)],
}

ZONES: dict[str, np.ndarray] = {
    k: np.array(v, dtype=float) / [_REF_W, _REF_H] for k, v in _ZONES_PX.items()
}
CROSSINGS = ("c1", "c2", "c3")
NOT_CARRIAGEWAY = ("parking", "median", "island", "t1", "t2", "t3")
APPROACHES = ("q1", "q2")


def inside(points: np.ndarray, zone: str) -> np.ndarray:
    """Even-odd ray casting. points: (N, 2) normalised (x, y). Returns (N,) bool."""
    poly = ZONES[zone]
    pts = np.atleast_2d(np.asarray(points, dtype=float))
    x, y = pts[:, 0:1], pts[:, 1:2]
    x1, y1 = poly[:, 0], poly[:, 1]
    x2, y2 = np.roll(x1, -1), np.roll(y1, -1)
    crosses = (y1 > y) != (y2 > y)
    with np.errstate(divide="ignore", invalid="ignore"):
        x_at = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
    return ((crosses & (x < x_at)).sum(1) % 2) == 1


def inside_any(points: np.ndarray, zones) -> np.ndarray:
    pts = np.atleast_2d(np.asarray(points, dtype=float))
    out = np.zeros(len(pts), dtype=bool)
    for z in zones:
        out |= inside(pts, z)
    return out


def on_carriageway(points: np.ndarray) -> np.ndarray:
    """Inside the road and not on a kerb-side strip, median or refuge island."""
    return inside(points, "road") & ~inside_any(points, NOT_CARRIAGEWAY)
