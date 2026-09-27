#!/usr/bin/env python3
"""Day-4 driver (Kaggle T4): check Part A + the whole submission the way the organizers run it.

    python tools/kaggle_day4.py all      # or one step: setup | probe | harness | validate | sheets | videos

  probe     keyframe interval, sampling mode and decode speed per sample video
  harness   clean venv + `pip install -r requirements.txt`, then run_submission.py twice:
            determinism diff + per-video timing against the 3x budget
  validate  evaluate.py --validate-only
  sheets    scene picture + one contact sheet of all detected events per video
  videos    annotated H.264 sample videos for the website

Everything important goes to /kaggle/working/day4_summary.txt.
"""
from __future__ import annotations

import json
import re
import os
import sys
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
from kaggle_day3 import SAMPLE_IDS, SAMPLES, W, run  # noqa: E402

# downloaded videos are kept in the notebook output, so the next run can attach that output as an
# input (Add Input -> this notebook) instead of downloading from Google Drive again
SAMPLES_SRC = Path(os.environ.get("DAY4_SAMPLES", "/kaggle/working/sample_videos"))

SUMMARY = W / "day4_summary.txt"
KAGGLE_INPUT = Path("/kaggle/input")
# Google Drive blocks a big file for up to 24 h after too many downloads, so try every source:
# the organizers' links (Videos.pdf, all 4 samples) first, then the team's copies
DRIVE_IDS = ["1kR9jODA2Wotw4gwkvpRKdqFADNJNc1nS", "1hp8DYeqtYHSwfM6qAo9FPSRHlpMFrIN_",
             "10cHEReCWzO3u-Vk1CnNgHAx6egGy5MwJ", "1aJ-QsAZVYJtLKHiRvKKeBq1D3GWNobRd", *SAMPLE_IDS]
N_SAMPLES = 4
VENV = Path(os.environ.get("DAY4_VENV", "/tmp/venv_clean"))
PRED = W / "predictions_samples.json"
PRED_2 = W / "predictions_run2.json"


def log(msg: str) -> None:
    print(msg, flush=True)
    with open(SUMMARY, "a") as fh:
        fh.write(msg + "\n")


def clean_name(p: Path) -> str:
    """'Copy of C3905.MP4', 'c3905.mp4' (a Kaggle dataset upload) -> 'C3905.MP4', the organizers' name."""
    m = re.search(r"(c\d{4})\.mp4$", p.name, re.I)
    return f"{m.group(1).upper()}.MP4" if m else p.name.replace(" ", "_")


def downloaded() -> set[str]:
    return {clean_name(p) for p in SAMPLES_SRC.glob("*.[mM][pP]4")}


def videos() -> list[Path]:
    found = sorted(SAMPLES.glob("*.[mM][pP]4"))
    if not found:
        raise SystemExit("no sample videos: see the setup step (attach them as a Kaggle input if Drive blocks them)")
    return found


# --------------------------------------------------------------------------- steps
def setup() -> None:
    """Sample videos from an attached Kaggle input, else from Google Drive; a blocked link is skipped."""
    import gdown

    SAMPLES_SRC.mkdir(parents=True, exist_ok=True)
    SAMPLES.mkdir(parents=True, exist_ok=True)
    for p in sorted(KAGGLE_INPUT.rglob("*")):   # an attached dataset with the videos, any name case
        if re.search(r"c\d{4}\.mp4$", p.name, re.I) and not (SAMPLES_SRC / clean_name(p)).exists():
            (SAMPLES_SRC / clean_name(p)).symlink_to(p)
    for fid in DRIVE_IDS:
        if len(downloaded()) >= N_SAMPLES:
            break
        try:
            gdown.download(id=fid, output=str(SAMPLES_SRC) + "/", quiet=True)
        except Exception as e:  # noqa: BLE001 - one blocked file must not stop the others
            log(f"DOWNLOAD {fid} failed: {type(e).__name__}: {' '.join(str(e).split())[:160]}")
    for p in sorted(SAMPLES_SRC.glob("*.[mM][pP]4")):
        if not (SAMPLES / clean_name(p)).exists():
            (SAMPLES / clean_name(p)).symlink_to(p)
    log(f"SETUP samples: {[v.name for v in videos()]}")


def probe() -> None:
    from src.events import KEYFRAME_MAX_GAP, keyframe_gap, sample_frames
    from src.video import video_info

    for v in videos():
        gap = keyframe_gap(v)
        mode = "keyframes only" if gap <= KEYFRAME_MAX_GAP else "full decode @2 fps"
        t0, n, last = time.perf_counter(), 0, 0.0
        for t, _img in sample_frames(v):
            n, last = n + 1, t
            if t >= 60:
                break
        dt = time.perf_counter() - t0
        info = video_info(v)
        log(f"PROBE {v.name}: {info['width']}x{info['height']} @ {info['fps']:.2f} fps, {info['duration']:.1f}s | "
            f"keyframe gap {gap:.2f}s -> {mode} | {n} samples in {last:.0f}s of video, "
            f"{dt:.1f}s wall ({last / dt:.1f}x realtime)")


def clean_env() -> dict:
    """Environment of a fresh machine: Kaggle's PYTHONPATH, pip config and user site must not leak in."""
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("PYTHON", "PIP_", "VIRTUAL_ENV", "CONDA"))}
    env.update(PIP_CONFIG_FILE=os.devnull, PYTHONNOUSERSITE="1",
               VIRTUAL_ENV=str(VENV), PATH=f"{VENV / 'bin'}:{env.get('PATH', '')}")
    return env


def run_clean(cmd: list) -> str:
    cmd = [str(c) for c in cmd]
    print("$", " ".join(cmd), flush=True)
    p = subprocess.run(cmd, capture_output=True, text=True, env=clean_env())
    if p.returncode:
        print(p.stdout[-3000:], p.stderr[-3000:], flush=True)
        raise RuntimeError(f"failed: {' '.join(cmd)}")
    return p.stdout


def harness() -> None:
    videos()
    # a fresh venv, like the organizers' clean machine. Kaggle's python has no ensurepip, so we use
    # virtualenv; clean_env() keeps Kaggle's packages and pip config out of it.
    py = VENV / "bin" / "python"
    run([sys.executable, "-m", "pip", "install", "-q", "virtualenv"])
    try:
        run_clean([sys.executable, "-m", "virtualenv", "-q", "--clear", VENV])
        run_clean([py, "-m", "pip", "install", "-r", REPO / "requirements.txt"])
        log("CLEAN VENV " + run_clean([py, "-c", "import cv2, av, torch, ultralytics; "
                                          "print(cv2.__version__, av.__version__, torch.__version__, "
                                          "torch.cuda.is_available(), ultralytics.__version__)"]).strip())
        runner = run_clean
    except RuntimeError as e:   # still produce predictions, and say so in the summary
        log(f"CLEAN VENV FAILED ({e}); running the harness with Kaggle's python instead")
        run([sys.executable, "-m", "pip", "install", "-q", "-r", REPO / "requirements.txt"])
        py, runner = Path(sys.executable), run
    for out in (PRED, PRED_2):
        runner([py, REPO / "run_submission.py", "--videos", SAMPLES, "--out", out, "--team", "mars"])
    a, b = json.loads(PRED.read_text()), json.loads(PRED_2.read_text())
    for name, ea in a["videos"].items():
        eb = b["videos"][name]
        ra = [s for _t, s in ea["risk"]]
        rb = [s for _t, s in eb["risk"]]
        risk_diff = max((abs(x - y) for x, y in zip(ra, rb)), default=0.0) if len(ra) == len(rb) else float("inf")
        lg = a["log"][name]
        total = lg.get("total_sec", 0.0)
        log(f"RUN {name}: events {'identical' if ea['events'] == eb['events'] else 'DIFFERENT'}, "
            f"max risk diff {risk_diff:.4f} | part A {lg.get('part_a_sec')}s, part B {lg.get('part_b_sec')}s, "
            f"total {total}s = {total / lg['duration']:.2f}x duration (budget {lg['budget_sec']}s) | "
            f"errors {len(lg['errors'])}")
        for err in lg["errors"]:
            log("   ! " + err.splitlines()[0])
        counts: dict[str, int] = {}
        for _s, _e, lab in ea["events"]:
            counts[lab] = counts.get(lab, 0) + 1
        log(f"EVENTS {name}: {counts} {ea['events'][:20]}")


def validate() -> None:
    log("VALIDATE " + run([sys.executable, REPO / "evaluate.py", "--pred", PRED, "--validate-only"])
        .strip().splitlines()[-1])


def sheets() -> None:
    plots = W / "plots"
    for v in videos():
        out = run([sys.executable, REPO / "tools/render_scene.py", "--video", v, "--out", plots / f"scene_{v.stem}.jpg"])
        log(f"SHEET {out.strip()}")
        out = run([sys.executable, REPO / "tools/render_scene.py", "--video", v, "--pred", PRED,
                   "--out", plots / f"events_{v.stem}.jpg"])
        log(f"SHEET {out.strip()}")


def videos_step() -> None:
    for v in videos():
        t0 = time.perf_counter()
        out = run([sys.executable, REPO / "tools/render_video.py", "--video", v, "--pred", PRED,
                   "--out", W / "videos" / f"{v.stem}_annotated.mp4"])
        log(f"VIDEO {out.strip()} ({time.perf_counter() - t0:.0f}s)")


def examples() -> None:
    """Website pictures: 3 annotated frames per event + a timeline per video, zipped for download."""
    import shutil

    pred = PRED if PRED.exists() else next(iter(sorted(KAGGLE_INPUT.rglob("predictions_samples.json"))), None)
    if pred is None:
        raise SystemExit("no predictions_samples.json: run the harness step, or attach the last run's output")
    out = W / "examples"
    predicted = json.loads(Path(pred).read_text())["videos"]
    for v in videos():
        if v.name in predicted:
            log("EXAMPLES " + run([sys.executable, REPO / "tools/export_examples.py", "--video", v,
                                   "--pred", pred, "--out", out]).strip())
    if pred != PRED:
        shutil.copy(pred, PRED)
    log(f"EXAMPLES zipped: {shutil.make_archive(str(W / 'examples'), 'zip', out)}")


def main() -> int:
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    steps = {"setup": setup, "probe": probe, "harness": harness, "validate": validate,
             "sheets": sheets, "videos": videos_step, "examples": examples}
    for name in (list(steps) if step == "all" else [step]):
        t0 = time.perf_counter()
        steps[name]()
        print(f"[{name}] done in {time.perf_counter() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
