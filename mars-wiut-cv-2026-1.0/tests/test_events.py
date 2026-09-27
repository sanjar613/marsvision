"""Part A rules on synthetic boxes placed in the real scene polygons (no video needed)."""
import numpy as np

from src.events import Sample, jaywalking_segments, stopped_vehicle_segments
from src.scene import APPROACHES, CROSSINGS, inside_any, on_carriageway

# foot points in the 1600x900 reference frame of src/scene.py, normalised
MID_ROAD = (800 / 1600, 800 / 900)     # intersection box, no queue zone, no crossing
QUEUE_Q1 = (500 / 1600, 350 / 900)     # near-side approach where cars wait at red
ZEBRA_C1 = (640 / 1600, 480 / 900)
BUS_STOP = (800 / 1600, 204 / 900)     # far kerb where people wait for the bus


def box_at(fx, fy, w=0.04, h=0.04):
    return [fx - w / 2, fy - h, fx + w / 2, fy]


def samples(objects_at, t_end, dt=1.0):
    """objects_at(t) -> [(name, box), ...]; one Sample every dt seconds from 0 to t_end."""
    out = []
    for t in np.arange(0, t_end + 1e-9, dt):
        objs = objects_at(t)
        out.append(Sample(float(t), np.array([b for _, b in objs], dtype=float).reshape(-1, 4),
                          np.array([n for n, _ in objs], dtype=object)))
    return out


def test_scene_points_are_where_the_tests_assume():
    pts = np.array([MID_ROAD, QUEUE_Q1, ZEBRA_C1])
    assert on_carriageway(pts).tolist() == [True, True, True]
    assert inside_any(pts, APPROACHES).tolist() == [False, True, False]
    assert inside_any(pts, CROSSINGS).tolist() == [False, False, True]


def test_parked_car_gives_one_segment():
    s = samples(lambda t: [("car", box_at(*MID_ROAD))], t_end=20)
    assert stopped_vehicle_segments(s) == [[0.0, 20.0]]


def test_short_stop_is_ignored():
    s = samples(lambda t: [("car", box_at(*MID_ROAD))] if t <= 8 else [], t_end=20)
    assert stopped_vehicle_segments(s) == []


def test_signal_queue_in_q1_is_ignored():
    s = samples(lambda t: [("car", box_at(*QUEUE_Q1))], t_end=60)
    assert stopped_vehicle_segments(s) == []


def test_moving_car_is_not_stopped():
    s = samples(lambda t: [("car", box_at(MID_ROAD[0] + 0.004 * t, MID_ROAD[1]))], t_end=30)
    assert stopped_vehicle_segments(s) == []


def test_short_occlusion_is_bridged_and_open_stop_runs_to_the_end():
    s = samples(lambda t: [] if 5 <= t <= 6 else [("car", box_at(*MID_ROAD))], t_end=20)
    assert stopped_vehicle_segments(s, end=21.5) == [[0.0, 21.5]]


def test_pedestrian_on_zebra_is_ignored():
    s = samples(lambda t: [("person", box_at(*ZEBRA_C1, w=0.01, h=0.03))], t_end=5)
    assert jaywalking_segments(s) == []


def test_pedestrian_mid_road_gives_segment():
    s = samples(lambda t: [("person", box_at(*MID_ROAD, w=0.01, h=0.03))] if 2 <= t <= 6 else [], t_end=10)
    assert jaywalking_segments(s) == [[2.0, 6.0]]


def test_rider_is_not_a_pedestrian():
    s = samples(lambda t: [("person", box_at(*MID_ROAD, w=0.01, h=0.03)),
                           ("motorcycle", box_at(*MID_ROAD, w=0.02, h=0.02))], t_end=5)
    assert jaywalking_segments(s) == []


def test_person_standing_still_is_not_jaywalking():
    s = samples(lambda t: [("person", box_at(*MID_ROAD, w=0.01, h=0.03))], t_end=40)
    assert jaywalking_segments(s) == []


def test_person_at_bus_stop_is_not_jaywalking():
    assert on_carriageway(np.array([BUS_STOP]))[0]
    s = samples(lambda t: [("person", box_at(BUS_STOP[0] + 0.003 * t, BUS_STOP[1], w=0.01, h=0.03))], t_end=6)
    assert jaywalking_segments(s) == []


def test_flickering_static_person_is_not_jaywalking():
    # seen for 3 s, missed for 4 s, again and again at the same spot (a night-time false detection)
    s = samples(lambda t: [("person", box_at(*MID_ROAD, w=0.01, h=0.03))] if t % 7 < 3 else [], t_end=40)
    assert jaywalking_segments(s) == []
