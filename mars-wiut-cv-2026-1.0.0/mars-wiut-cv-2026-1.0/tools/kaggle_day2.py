#!/usr/bin/env python3
"""Day-2 experiment driver (Kaggle T4). Each step can be re-run on its own.

    python tools/kaggle_day2.py setup   # dev set (ACCIDENT), sample links, decode benchmark
    python tools/kaggle_day2.py cache   # detector+tracker once per video -> cache/
    python tools/kaggle_day2.py ablate  # replays: day-1 vs filters vs calibrator, grid on train
    python tools/kaggle_day2.py render  # alarm contact sheets for the organizer samples
    python tools/kaggle_day2.py all

Everything important is appended to /kaggle/working/day2_summary.txt.
Split: ACCIDENT clips by name hash (70% train / 30% test); organizer samples
C3896 + C3897 = train negatives, C3905 (the dark one) = test negative.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
W = Path(os.environ.get("DAY2_WORK", "/kaggle/working"))
DEV = W / "dev2" / "accident"
SAMPLES_SRC = Path(os.environ.get("DAY2_SAMPLES", "/tmp/samples"))
ACC_ROOT = os.environ.get("DAY2_ACCIDENT_ROOT", "/kaggle/input")
SAMPLES = W / "samples"               # clean names -> symlinks
CACHE = W / "cache"
SUMMARY = W / "day2_summary.txt"
TRAIN_NEG = ["C3896.MP4", "C3897.MP4"]
TEST_NEG = ["C3905.MP4"]
N_ACCIDENT = int(os.environ.get("DAY2_N", 240))

DAY1 = {"use_lane_filter": False, "use_queue_filter": False, "min_age": 0.0}


def log(msg: str) -> None:
    print(msg, flush=True)
    with open(SUMMARY, "a") as fh:
        fh.write(msg + "\n")


def run(cmd: list[str]) -> str:
    print("$", " ".join(cmd), flush=True)
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        print(p.stdout[-3000:], p.stderr[-3000:])
        raise SystemExit(f"failed: {' '.join(cmd)}")
    return p.stdout


def py(*args: str) -> str:
    return run([sys.executable, *map(str, args)])


def summary_line(out: str) -> dict:
    line = [x for x in out.splitlines() if x.startswith("SUMMARY ")][-1]
    return json.loads(line[len("SUMMARY "):])


def setup() -> None:
    py(REPO / "tools/accident_to_gt.py", "--root", ACC_ROOT, "--n", N_ACCIDENT, "--out", DEV)
    SAMPLES.mkdir(parents=True, exist_ok=True)
    for p in sorted(SAMPLES_SRC.glob("*.[mM][pP]4")):
        clean = p.name.replace("Copy of ", "").replace(" ", "_")
        link = SAMPLES / clean
        if not link.exists():
            link.symlink_to(p)
    for sub in ("train_neg", "test_neg"):
        (SAMPLES / sub).mkdir(exist_ok=True)
    for n in TRAIN_NEG:
        if (SAMPLES / n).exists() and not (SAMPLES / "train_neg" / n).exists():
            (SAMPLES / "train_neg" / n).symlink_to(SAMPLES / n)
    for n in TEST_NEG:
        if (SAMPLES / n).exists() and not (SAMPLES / "test_neg" / n).exists():
            (SAMPLES / "test_neg" / n).symlink_to(SAMPLES / n)
    # decode benchmark on 20 s of a 4K sample: what Part A can expect
    sys.path.insert(0, str(REPO))
    import cv2
    from src.video import benchmark
    vids = sorted(SAMPLES.glob("*.MP4"))
    if vids:
        v = vids[0]
        cap = cv2.VideoCapture(str(v))
        t0, n = time.perf_counter(), 0
        while n < 600 and cap.read()[0]:
            n += 1
        cv2_x = round(n / cap.get(cv2.CAP_PROP_FPS) / (time.perf_counter() - t0), 2)
        cap.release()
        log(f"DECODE {v.name} (video-seconds per wall-second): cv2 every frame {cv2_x} | "
            f"pyav every frame {benchmark(v, 20)} | pyav 8fps native {benchmark(v, 20, target_fps=8)} | "
            f"pyav 8fps w=1280 {benchmark(v, 20, target_fps=8, width=1280)} | "
            f"pyav 5fps w=960 {benchmark(v, 20, target_fps=5, width=960)}")


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


def replay(split: str, negs: list[str], config: dict, calibrator: str = "", tag: str = "",
           features_out: str = "", frames_out: str = "") -> dict:
    args = [REPO / "tools/replay.py", "--cache", CACHE / "accident", "--gt", DEV / "ground_truth.json",
            "--split", split, "--config", json.dumps(config), "--tag", tag]
    if negs:
        args += ["--negatives-cache", *[CACHE / n for n in negs]]
    if calibrator:
        args += ["--calibrator", calibrator]
    if features_out:
        args += ["--features-out", features_out]
    if frames_out:
        args += ["--frames-out", frames_out]
    return summary_line(py(*args))


def fmt(s: dict) -> str:
    return (f"{s['tag']:<28} {s['split']:<5} B={s['score_b']:.3f} AP={s['ap']:.3f} "
            f"P/R={s['alarm_p']:.2f}/{s['alarm_r']:.2f} F1={s['f1_alarm']:.3f} mTTA={s['mtta']:.1f}s "
            f"alarms={s['alarms']} negFA/min={s['neg_alarms_per_min']}")


def ablate() -> None:
    log("ABLATION (test = 30% ACCIDENT + C3905 as negative)")
    log(fmt(replay("test", ["test_neg"], DAY1, tag="day1 hand, no filters")))
    log(fmt(replay("test", ["test_neg"], {}, tag="hand + lane/queue/age filters")))
    # calibrator: features on train split (+ train negatives)
    feats = str(W / "feats_train.csv")
    replay("train", ["train_neg"], {}, tag="train features", features_out=feats)
    cal = str(REPO / "weights" / "risk_calibrator.json")
    log(py(REPO / "tools/train_calibrator.py", "--features", feats, "--out", cal).strip().splitlines()[-1])
    best = None
    for alarm_on in (0.35, 0.45, 0.55, 0.65, 0.75, 0.85):
        for hold in (2.5, 4.0):
            cfg = {"alarm_on": alarm_on, "alarm_hold": hold}
            s = replay("train", ["train_neg"], cfg, calibrator=cal, tag=f"grid on={alarm_on} hold={hold}")
            log("  " + fmt(s))
            if best is None or s["score_b"] > best[0]["score_b"]:
                best = (s, cfg)
    cfg = best[1]
    py(REPO / "tools/train_calibrator.py", "--features", feats, "--out", cal, "--config", json.dumps(cfg))
    log(f"BEST train config {cfg}")
    log(fmt(replay("test", ["test_neg"], {}, calibrator=cal, tag="calibrated + tuned")))
    log(fmt(replay("all", ["train_neg", "test_neg"], {}, calibrator=cal, tag="calibrated, all (not held out)",
                   frames_out=str(W / "frames_all.jsonl"))))
    replay("all", ["train_neg", "test_neg"], {}, tag="hand filters, all", frames_out=str(W / "frames_hand.jsonl"))


def render() -> None:
    (W / "plots").mkdir(exist_ok=True)
    for sub, names in (("train_neg", TRAIN_NEG), ("test_neg", TEST_NEG)):
        for n in names:
            for which in ("all", "hand"):
                fr = W / f"frames_{which}.jsonl"
                if (SAMPLES / n).exists() and fr.exists():
                    out = py(REPO / "tools/render_alarms.py", "--video", SAMPLES / n, "--cache", CACHE / sub,
                             "--frames", fr, "--out", W / "plots" / f"alarms_{which}_{n}.jpg", "--max", 9)
                    log(f"RENDER {which} {n}: {out.strip()}")


def main() -> int:
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    steps = {"setup": setup, "cache": cache, "ablate": ablate, "render": render}
    for name in (list(steps) if step == "all" else [step]):
        t0 = time.perf_counter()
        steps[name]()
        print(f"[{name}] done in {time.perf_counter() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
