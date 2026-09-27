#!/usr/bin/env python3
"""Day-3 experiment driver (Kaggle T4, runs unattended with "Save & Run All").

    python tools/kaggle_day3.py all      # or one step: setup | cache | flow | ablate | render | harness | nvdec

Changes vs Day 2 (see README.md, Part B results):
  * fair dev metric: no alarms in the first 3 s (warm-up) + sanity checks
    (probability spread, time of first alarm) + false alarms/min on the
    organizer camera as a hard constraint when choosing the threshold
  * un-balanced calibrator, organizer negatives up-weighted
  * "already overlapping = collision" rule removed (occlusion in dense traffic)
  * new features: DRAC, box-overlap growth, swerve, driving against the usual flow

Everything important goes to /kaggle/working/day3_summary.txt.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
W = Path(os.environ.get("DAY3_WORK", "/kaggle/working"))
ACC_ROOT = os.environ.get("DAY3_ACCIDENT_ROOT", "/kaggle/input")
SAMPLES_SRC = Path(os.environ.get("DAY3_SAMPLES", "/tmp/samples"))
N_ACCIDENT = int(os.environ.get("DAY3_N", 240))
DEV = W / "dev" / "accident"
SAMPLES = W / "samples"
CACHE = W / "cache"
OUT = W / "out"
SUMMARY = W / "day3_summary.txt"
TRAIN_NEG, TEST_NEG = ["C3896.MP4", "C3897.MP4"], ["C3905.MP4"]
SAMPLE_IDS = ["1k5OP1SO9Ogquf8SpxLjIfGsKjuL_UqnP", "1nR7vn6dGiUA9QqAuLBujfCBAm9VuD7Iq",
              "1Am7Yeeu3yn9hIFOxo-6ZuQdn9ds4W93B"]
MAX_NEG_FA_PER_MIN = 0.3
OLD = {"touch_rule": True, "warmup": 0.0}                         # Day-2 behaviour
DAY1 = dict(OLD, use_lane_filter=False, use_queue_filter=False, min_age=0.0)


def log(msg: str) -> None:
    print(msg, flush=True)
    with open(SUMMARY, "a") as fh:
        fh.write(msg + "\n")


def run(cmd: list) -> str:
    cmd = [str(c) for c in cmd]
    print("$", " ".join(cmd), flush=True)
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        print(p.stdout[-3000:], p.stderr[-3000:], flush=True)
        raise SystemExit(f"failed: {' '.join(cmd)}")
    return p.stdout


def py(*args) -> str:
    return run([sys.executable, *args])


# --------------------------------------------------------------------------- steps
def setup() -> None:
    SAMPLES_SRC.mkdir(parents=True, exist_ok=True)
    if len(list(SAMPLES_SRC.glob("*.[mM][pP]4"))) < 3:
        import gdown
        for fid in SAMPLE_IDS:
            gdown.download(id=fid, output=str(SAMPLES_SRC) + "/", quiet=True)
    for sub in ("train_neg", "test_neg"):
        (SAMPLES / sub).mkdir(parents=True, exist_ok=True)
    for p in sorted(SAMPLES_SRC.glob("*.[mM][pP]4")):
        clean = p.name.replace("Copy of ", "").replace(" ", "_")
        for sub, names in (("train_neg", TRAIN_NEG), ("test_neg", TEST_NEG)):
            if clean in names and not (SAMPLES / sub / clean).exists():
                (SAMPLES / sub / clean).symlink_to(p)
        if not (SAMPLES / clean).exists():
            (SAMPLES / clean).symlink_to(p)
    py(REPO / "tools/accident_to_gt.py", "--root", ACC_ROOT, "--n", N_ACCIDENT, "--out", DEV)
    log(f"SETUP samples: {sorted(p.name for p in SAMPLES.glob('*.MP4'))}")


def cache() -> None:
    t0 = time.perf_counter()
    py(REPO / "tools/cache_tracks.py", "--videos", DEV / "videos", "--out", CACHE / "accident")
    t1 = time.perf_counter()
    for sub in ("train_neg", "test_neg"):
        out = py(REPO / "tools/cache_tracks.py", "--videos", SAMPLES / sub, "--out", CACHE / sub, "--width", 1280)
        for line in out.splitlines():
            if "realtime" in line:
                log("CACHE " + line)
    log(f"CACHE accident {t1 - t0:.0f}s, samples {time.perf_counter() - t1:.0f}s")


def flow() -> None:
    (W / "plots").mkdir(exist_ok=True)
    out = py(REPO / "tools/build_flow_prior.py", "--cache", CACHE / "train_neg", "--out", REPO / "weights/flow_prior.json",
             "--video", SAMPLES / TRAIN_NEG[0], "--plot", W / "plots/flow_map.jpg")
    for line in out.splitlines():
        if line.startswith("FLOW"):
            log(line)


def replay(split, negs, config, calibrator="", tag="", flow_prior=True, **extra) -> dict:
    args = [REPO / "tools/replay.py", "--cache", CACHE / "accident", "--gt", DEV / "ground_truth.json",
            "--split", split, "--config", json.dumps(config), "--tag", tag]
    if negs:
        args += ["--negatives-cache", *[CACHE / n for n in negs]]
    if calibrator:
        args += ["--calibrator", calibrator]
    if flow_prior and (REPO / "weights/flow_prior.json").exists():
        args += ["--flow-prior", REPO / "weights/flow_prior.json"]
    for k, v in extra.items():
        args += [f"--{k.replace('_', '-')}", v]
    line = [x for x in py(*args).splitlines() if x.startswith("SUMMARY ")][-1]
    return json.loads(line[len("SUMMARY "):])


def fmt(s: dict) -> str:
    return (f"{s['tag']:<34} {s['split']:<5} B={s['score_b']:.3f} AP={s['ap']:.3f} "
            f"P/R={s['alarm_p']:.2f}/{s['alarm_r']:.2f} F1={s['f1_alarm']:.3f} mTTA={s['mtta']:.1f}s "
            f"negFA/min={s['neg_alarms_per_min']} | prob_std={s['prob_std']} "
            f"first_alarm_med={s['first_alarm_median_s']}s first<4s={s['first_alarm_lt4s']}")


def train_and_tune(tag: str, cal_path: Path, extra_cfg: dict, train_flags: list, flow_prior: bool = True):
    feats = W / f"feats_{tag}.csv"
    replay("train", ["train_neg"], extra_cfg, tag=f"{tag} features", features_out=feats, flow_prior=flow_prior)
    out = py(REPO / "tools/train_calibrator.py", "--features", feats, "--out", cal_path, *train_flags)
    log(f"  {tag}: " + [x for x in out.splitlines() if x.startswith("CALIBRATOR")][-1])
    best, fallback = None, None
    for on in (0.08, 0.12, 0.16, 0.2, 0.25, 0.3, 0.4, 0.5):
        for hold in (2.5, 4.0):
            cfg = dict(extra_cfg, alarm_on=on, alarm_hold=hold)
            s = replay("train", ["train_neg"], cfg, calibrator=str(cal_path), tag=f"  grid on={on} hold={hold}",
                       flow_prior=flow_prior)
            log("    " + fmt(s))
            ok = s["neg_alarms_per_min"] is not None and s["neg_alarms_per_min"] <= MAX_NEG_FA_PER_MIN
            if ok and (best is None or s["score_b"] > best[0]["score_b"]):
                best = (s, cfg)
            if fallback is None or (s["neg_alarms_per_min"] or 0) < (fallback[0]["neg_alarms_per_min"] or 0):
                fallback = (s, cfg)
    chosen = (best or fallback)[1]
    py(REPO / "tools/train_calibrator.py", "--features", feats, "--out", cal_path, *train_flags,
       "--config", json.dumps(chosen))
    log(f"  {tag}: chosen config {chosen}" + ("" if best else " (no config met the false-alarm limit)"))
    return chosen


def ablate() -> None:
    OUT.mkdir(exist_ok=True)
    log(f"ABLATION  test = 30% ACCIDENT clips + C3905 (organizer camera, normal traffic); "
        f"threshold chosen on train with <= {MAX_NEG_FA_PER_MIN} false alarms/min on C3896+C3897")
    log(fmt(replay("test", ["test_neg"], DAY1, tag="A day1 hand formula", flow_prior=False)))
    log(fmt(replay("test", ["test_neg"], OLD, tag="B day2 hand + filters", flow_prior=False)))
    log(fmt(replay("test", ["test_neg"], {}, tag="C day3 hand (no touch rule, warm-up)")))
    # D: Day-2 style balanced calibrator, now caught by the sanity checks
    cal_bal = OUT / "cal_balanced.json"
    cfg = train_and_tune("balanced", cal_bal, {}, ["--balance", "--neg-weight", "1"])
    log(fmt(replay("test", ["test_neg"], {}, calibrator=str(cal_bal), tag="D calibrated, class-balanced")))
    # E: un-balanced calibrator without the flow prior
    cal_nf = OUT / "cal_noflow.json"
    train_and_tune("noflow", cal_nf, {}, [], flow_prior=False)
    log(fmt(replay("test", ["test_neg"], {}, calibrator=str(cal_nf), tag="E calibrated, no flow prior", flow_prior=False)))
    # F: final = un-balanced calibrator + flow prior
    cal = REPO / "weights/risk_calibrator.json"
    train_and_tune("final", cal, {}, [])
    final = replay("test", ["test_neg"], {}, calibrator=str(cal), tag="F FINAL calibrated + flow prior",
                   pred_out=W / "pred_test.json")
    log(fmt(final))
    replay("all", ["train_neg", "test_neg"], {}, calibrator=str(cal), tag="final all", frames_out=W / "frames_final.jsonl",
           pred_out=W / "pred_all.json")
    shutil.copy(cal, OUT / "risk_calibrator.json")
    if (REPO / "weights/flow_prior.json").exists():
        shutil.copy(REPO / "weights/flow_prior.json", OUT / "flow_prior.json")
    log("CALIBRATOR_JSON " + json.dumps(json.loads(cal.read_text())))


def render() -> None:
    (W / "plots").mkdir(exist_ok=True)
    for sub, names in (("train_neg", TRAIN_NEG), ("test_neg", TEST_NEG)):
        for n in names:
            if (SAMPLES / n).exists():
                out = py(REPO / "tools/render_alarms.py", "--video", SAMPLES / n, "--cache", CACHE / sub,
                         "--frames", W / "frames_final.jsonl", "--out", W / "plots" / f"alarms_final_{n}.jpg", "--max", 9)
                log(f"RENDER {n}: {out.strip()}")
    py(REPO / "tools/plot_risk.py", "--pred", W / "pred_test.json", "--gt", DEV / "ground_truth.json",
       "--out", W / "plots", "--max", 24)


def harness() -> None:
    """Official harness on the dark sample with the final weights: timing + format check."""
    one = W / "harness_in"
    one.mkdir(exist_ok=True)
    if not (one / "C3905.MP4").exists():
        (one / "C3905.MP4").symlink_to(SAMPLES / "C3905.MP4")
    pred = W / "pred_harness_C3905.json"
    py(REPO / "run_submission.py", "--videos", one, "--out", pred, "--team", "dev", "--solution", REPO / "solution.py")
    d = json.loads(pred.read_text())
    lg = d["log"]["C3905.MP4"]
    risk = [s for _t, s in d["videos"]["C3905.MP4"]["risk"]]
    import evaluate as ev
    starts = ev.alarm_starts(d["videos"]["C3905.MP4"]["risk"])
    log(f"HARNESS C3905: {lg} | alarms {len(starts)} at {[round(x, 1) for x in starts[:10]]} | "
        f"max score {max(risk):.2f}")
    log("VALIDATE " + run([sys.executable, REPO / "evaluate.py", "--pred", pred, "--validate-only"]).strip().splitlines()[-1])


def nvdec() -> None:
    """GPU hardware decoding benchmark for Part A (PyNvVideoCodec)."""
    try:
        run([sys.executable, "-m", "pip", "install", "-q", "PyNvVideoCodec"])
        import PyNvVideoCodec as nvc
        v = str(SAMPLES / TRAIN_NEG[0])
        dec = nvc.SimpleDecoder(v, gpu_id=0, use_device_memory=True, output_color_type=nvc.OutputColorType.RGB)
        t0 = time.perf_counter()
        n = 0
        while n < 600:
            n += len(dec.get_batch_frames(30))
        seq = n / (time.perf_counter() - t0)
        t0 = time.perf_counter()
        idx = list(range(600, 3000, 4))
        for k in range(0, len(idx), 32):
            dec.get_batch_frames_by_index(idx[k:k + 32])
        every4 = len(idx) / (time.perf_counter() - t0)
        log(f"NVDEC {TRAIN_NEG[0]}: sequential {seq:.0f} frames/s ({seq / 29.97:.1f}x realtime) | "
            f"every 4th frame {every4:.0f} kept-frames/s ({every4 * 4 / 29.97:.1f}x realtime)")
    except Exception as e:  # noqa: BLE001 - report, do not fail the run
        log(f"NVDEC failed: {type(e).__name__}: {str(e).splitlines()[0][:200]}")


def main() -> int:
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    steps = {"setup": setup, "nvdec": nvdec, "cache": cache, "flow": flow, "ablate": ablate,
             "render": render, "harness": harness}
    for name in (list(steps) if step == "all" else [step]):
        t0 = time.perf_counter()
        steps[name]()
        print(f"[{name}] done in {time.perf_counter() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
