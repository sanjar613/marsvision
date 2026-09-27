#!/usr/bin/env python3
"""Day-1 run on a Kaggle T4 notebook (internet ON, ACCIDENT dataset attached).

Steps (each can be skipped with a flag):
  1. download the 4 organizer sample videos from Google Drive (gdown)
  2. quick EDA of the samples: resolution, fps, duration, bitrate, brightness
  3. build a Part B dev set from ACCIDENT (tools/accident_to_gt.py)
  4. run the official harness on the dev set (Part B only) and on the samples
  5. evaluate + plot risk curves + print timing vs the 3x budget

    python tools/kaggle_day1.py --accident-root /kaggle/input/accident --n 60
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parent.parent
SAMPLE_IDS = [  # team copies (the organizer originals hit Drive's download quota)
    "1k5OP1SO9Ogquf8SpxLjIfGsKjuL_UqnP",
    "1nR7vn6dGiUA9QqAuLBujfCBAm9VuD7Iq",
    "1Am7Yeeu3yn9hIFOxo-6ZuQdn9ds4W93B",
    "1aJ-QsAZVYJtLKHiRvKKeBq1D3GWNobRd",  # organizer original, not copied yet (may hit the quota)
]


def sh(cmd: list[str]) -> None:
    print("$", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def download_samples(dst: Path, n: int) -> None:
    """Videos are ~6 GB each: keep them in /tmp (Kaggle /kaggle/working is capped at 20 GB)."""
    dst.mkdir(parents=True, exist_ok=True)
    import gdown
    done = dst / ".done"
    have = set(done.read_text().split()) if done.exists() else set()
    for fid in SAMPLE_IDS[:n]:
        if fid in have:
            continue
        gdown.download(id=fid, output=str(dst) + "/", quiet=False)
        have.add(fid)
        done.write_text("\n".join(sorted(have)))
    # the harness only picks up .mp4 / .MP4
    for p in dst.iterdir():
        print(p.name, round(p.stat().st_size / 1e9, 2), "GB")


def eda(folder: Path) -> list[dict]:
    rows = []
    for p in sorted(folder.iterdir()):
        if p.suffix.lower() != ".mp4":
            continue
        cap = cv2.VideoCapture(str(p))
        fps = cap.get(cv2.CAP_PROP_FPS)
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        bright = []
        t0 = time.perf_counter()
        for k in range(0, n, max(1, n // 30)):
            cap.set(cv2.CAP_PROP_POS_FRAMES, k)
            ok, f = cap.read()
            if ok:
                bright.append(float(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).mean()))
                if k == 0:
                    cv2.imwrite(f"/kaggle/working/{p.stem}_first.jpg", f)
        # sequential decode speed (what the harness pays for every frame)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        t1, m = time.perf_counter(), 0
        while m < 250 and cap.read()[0]:
            m += 1
        dec_fps = m / (time.perf_counter() - t1 + 1e-9)
        cap.release()
        row = {"video": p.name, "w": w, "h": h, "fps": round(fps, 2), "frames": n,
               "duration_s": round(n / fps, 1) if fps else None,
               "size_gb": round(p.stat().st_size / 1e9, 2),
               "brightness_mean": round(float(np.mean(bright)), 1) if bright else None,
               "brightness_min": round(float(np.min(bright)), 1) if bright else None,
               "decode_fps": round(dec_fps, 1), "seek_s": round(t1 - t0, 1)}
        rows.append(row)
        print(row, flush=True)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--accident-root", default="/kaggle/input/accident")
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--work", default="/kaggle/working")
    ap.add_argument("--skip-samples", action="store_true")
    ap.add_argument("--samples-dir", default="/tmp/samples")
    ap.add_argument("--n-samples", type=int, default=4, help="how many sample videos to download")
    ap.add_argument("--skip-dev", action="store_true")
    ap.add_argument("--samples-limit", type=int, default=1, help="how many sample videos to run the harness on")
    args = ap.parse_args()
    work = Path(args.work)
    samples = Path(args.samples_dir)
    report: dict = {}

    if not args.skip_samples:
        download_samples(samples, args.n_samples)
        report["eda"] = eda(samples)

    if not args.skip_dev:
        dev = work / "dev" / "accident"
        sh([sys.executable, str(REPO / "tools/accident_to_gt.py"), "--root", args.accident_root,
            "--n", str(args.n), "--out", str(dev)])
        pred = work / "pred_dev.json"
        t0 = time.perf_counter()
        sh([sys.executable, str(REPO / "run_submission.py"), "--videos", str(dev / "videos"),
            "--out", str(pred), "--team", "dev", "--solution", str(REPO / "solution.py")])
        report["dev_wall_s"] = round(time.perf_counter() - t0, 1)
        sh([sys.executable, str(REPO / "evaluate.py"), "--pred", str(pred), "--gt", str(dev / "ground_truth.json"),
            "--json", str(work / "report_dev.json")])
        sh([sys.executable, str(REPO / "tools/plot_risk.py"), "--pred", str(pred),
            "--gt", str(dev / "ground_truth.json"), "--out", str(work / "plots")])

    if not args.skip_samples and args.samples_limit > 0:
        one = work / "samples_subset"
        one.mkdir(exist_ok=True)
        for p in sorted(samples.glob("*.[mM][pP]4"))[: args.samples_limit]:
            link = one / p.name
            if not link.exists():
                link.symlink_to(p)
        sh([sys.executable, str(REPO / "run_submission.py"), "--videos", str(one),
            "--out", str(work / "pred_samples.json"), "--team", "dev", "--solution", str(REPO / "solution.py")])
        log = json.loads((work / "pred_samples.json").read_text())["log"]
        report["samples_timing"] = log

    (work / "day1_report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
