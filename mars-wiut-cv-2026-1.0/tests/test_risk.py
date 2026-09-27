"""Sanity checks for the TTC / filters / alarm logic with synthetic tracks (no video needed)."""
import numpy as np

from src.risk import AlarmSmoother, Calibrator, FEATURES, RiskConfig, RiskModel, frame_features, pair_ttc, raw_risk
from src.tracking import Track, TrackStore


def make_track(tid, x0, y0, vx, vy, t_end=1.0, fps=8, w=60, h=40):
    tr = Track(tid, "car", first_t=0.0)
    n = int(t_end * fps)
    for k in range(n + 1):
        t = k / fps
        x, y = x0 + vx * t, y0 + vy * t
        tr.hist.append((t, x, y, x + w, y + h))
    tr.last_t = n / fps
    return tr


def test_head_on_has_small_ttc():
    cfg = RiskConfig()
    a = make_track(1, 0, 100, 100, 0)      # moving right at 100 px/s
    b = make_track(2, 400, 100, -100, 0)   # moving left at 100 px/s
    r = pair_ttc(a, b, cfg)
    assert r is not None
    ttc, closing, _gap = r
    # after 1 s: a spans 100..160, b spans 300..360 -> gap 140 px, closing 200 px/s -> 0.7 s
    assert 0.6 <= ttc <= 0.8, ttc


def test_parallel_lanes_no_conflict():
    cfg = RiskConfig()
    a = make_track(1, 0, 100, 100, 0)
    b = make_track(2, 0, 300, 100, 0)      # same speed, other lane
    assert pair_ttc(a, b, cfg) is None


def test_oncoming_lane_detected_same_lane_not():
    from src.risk import make_state, separate_lanes
    cfg = RiskConfig()
    a = make_track(1, 0, 100, 100, 0)
    other_lane = make_track(2, 400, 160, -100, 0)   # oncoming, 60 px lateral > 0.6 * 60 px width
    same_lane = make_track(3, 400, 105, -100, 0)    # oncoming in a's lane
    assert separate_lanes(make_state(a), make_state(other_lane), cfg, 60)
    assert not separate_lanes(make_state(a), make_state(same_lane), cfg, 60)
    assert pair_ttc(a, same_lane, cfg) is not None


def test_queue_filtered():
    cfg = RiskConfig()
    a = make_track(1, 0, 100, 5, 0)        # creeping
    b = make_track(2, 70, 100, 0, 0)       # standing just ahead
    assert pair_ttc(a, b, cfg) is None


def test_crossing_paths_kept():
    cfg = RiskConfig()
    a = make_track(1, 0, 200, 150, 0)      # going right
    b = make_track(2, 250, 0, 0, 150)      # going down, will cross a's path
    assert pair_ttc(a, b, cfg) is not None


def test_alarm_is_one_block():
    cfg = RiskConfig()
    sm = AlarmSmoother(cfg)
    scores = [sm(1.0 if 2.0 <= k / 8 < 3.0 else 0.0, k / 8) for k in range(80)]
    runs, on = 0, False
    for s in scores:
        if s >= 0.5 and not on:
            runs += 1
        on = s >= 0.5
    assert runs == 1
    assert max(scores[:10]) < 0.5


def test_frame_features_head_on():
    cfg = RiskConfig()
    f = frame_features([make_track(1, 0, 100, 100, 0), make_track(2, 400, 100, -100, 0)], cfg)
    assert f["n_conflicts"] == 1 and raw_risk(f) > 0.4


def test_young_tracks_ignored():
    cfg = RiskConfig()
    f = frame_features([make_track(1, 0, 100, 100, 0, t_end=0.3), make_track(2, 400, 100, -100, 0, t_end=0.3)], cfg)
    assert f["n_conflicts"] == 0


def test_replay_matches_live_path_and_calibrator_runs():
    """TrackStore + RiskModel on rows == what RiskEstimator.step computes after detection."""
    rows_a = [np.array([[1, 2, 100 * t, 100, 100 * t + 60, 140, 0.9],
                        [2, 2, 400 - 100 * t, 100, 460 - 100 * t, 140, 0.9]], dtype=np.float32)
              for t in np.arange(0, 2, 0.125)]
    cal = Calibrator({"features": FEATURES, "mean": [0] * len(FEATURES), "std": [1] * len(FEATURES),
                      "w": [3.0] + [0.0] * (len(FEATURES) - 1), "b": -1.0})
    for c in (None, cal):
        store, model = TrackStore(), RiskModel(RiskConfig(warmup=0.0), c)
        scores = [model.step(store.update(r, float(t)), float(t))[0] for t, r in zip(np.arange(0, 2, 0.125), rows_a)]
        assert max(scores) >= 0.5 and all(0 <= s <= 1 for s in scores)


def test_touch_rule_off_by_default():
    cfg = RiskConfig()
    a = make_track(1, 0, 100, 100, 0)
    b = make_track(2, 250, 100, -100, 0)   # footprints overlap by 10 px at the end, still closing
    assert pair_ttc(a, b, cfg) is None
    assert pair_ttc(a, b, RiskConfig(touch_rule=True)) is not None


def test_no_alarm_during_warmup():
    sm = AlarmSmoother(RiskConfig(warmup=3.0))
    scores = [sm(1.0, k / 8) for k in range(40)]
    assert max(scores[:23]) < 0.5 and max(scores) >= 0.5


def test_flow_map_flags_wrong_way():
    from src.risk import FlowMap, make_state
    cfg = RiskConfig(flow_min_count=5)
    fm = FlowMap(1000, 500, cfg)
    for k in range(10):
        fm.update([make_state(make_track(k, 100, 200, 100, 0))])   # traffic goes right
    right = make_state(make_track(50, 100, 200, 100, 0))
    wrong = make_state(make_track(51, 300, 200, -100, 0))  # ends in the same cell, driving left
    assert fm.anomaly(right) < 0.1 and fm.anomaly(wrong) > 0.9
