#!/usr/bin/env python3
"""Pack the repo (code only, no weights) into a self-contained Kaggle notebook.

    python tools/build_kaggle_notebook.py --out notebooks/day1_kaggle.ipynb
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import tarfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKIP = {".pt", ".pyc", ".ipynb", ".json", ".png", ".jpg", ".mp4"}


def pack() -> str:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for p in sorted(REPO.rglob("*")):
            rel = p.relative_to(REPO)
            shipped = rel.parts[0] == "weights" and p.suffix == ".json"   # the Part B calibrator
            if p.is_file() and (shipped or p.suffix not in SKIP) and not any(part.startswith((".", "__")) for part in rel.parts):
                tar.add(p, arcname=str(rel))
    return base64.b64encode(buf.getvalue()).decode()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="notebooks/day1_kaggle.ipynb")
    ap.add_argument("--day", type=int, default=1)
    args = ap.parse_args()
    b64 = pack()
    unpack = ("code", "# 1) unpack our repo (embedded, so the notebook is self-contained)\n"
              "import base64, io, tarfile, os\n"
              f"REPO_B64 = \"{b64}\"\n"
              "os.makedirs('/kaggle/working/repo', exist_ok=True)\n"
              "tarfile.open(fileobj=io.BytesIO(base64.b64decode(REPO_B64))).extractall('/kaggle/working/repo')\n"
              "%cd /kaggle/working/repo\n!find . -type f | sort | head -40")
    install = ("code", "# 2) install + weights + GPU check + tests\n"
               "!pip install -q ultralytics==8.4.160 lap gdown pytest av\n!bash weights/download.sh\n"
               "import torch; print(torch.__version__, torch.cuda.is_available(), "
               "torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')\n!python -m pytest -q tests")
    if args.day == 1:
        cells = [
            ("markdown", "# WIUT Hackathon — Part B (accident anticipation)\n"
                         "Settings: **Accelerator = GPU T4**, **Internet = On**, add dataset **picekl/accident**. Then *Run All*."),
            unpack, install,
            ("code", "# 3) Part B dev set from ACCIDENT: build labels, run official harness, evaluate, plot\n"
                     "!python tools/kaggle_day1.py --accident-root /kaggle/input --n 60 --skip-samples"),
            ("code", "from IPython.display import Image, display\ndisplay(Image('/kaggle/working/plots/risk_curves.png'))"),
            ("code", "# 4) organizer sample videos (~6 GB each): download to /tmp, EDA, time one through the harness\n"
                     "!python tools/kaggle_day1.py --skip-dev --n-samples 4 --samples-limit 1\n"
                     "!ls -la /kaggle/working"),
        ]
    elif args.day == 4:
        steps = [("setup", "sample videos"),
                 ("probe", "keyframe interval + sampling mode + decode speed"),
                 ("harness", "clean venv, pip install -r requirements.txt, official harness twice (determinism + timing)"),
                 ("validate", "evaluate.py --validate-only"),
                 ("sheets", "scene pictures + contact sheet of every detected event"),
                 ("videos", "annotated H.264 sample videos for the website")]
        cells = [("markdown", "# WIUT Hackathon — team mars · Day 4: Part A + full submission check\n"
                              "Settings: **GPU T4**, **Internet On**. Runs unattended with *Save & Run All*; "
                              "results in `day4_summary.txt`, `predictions_samples.json`, `plots/`, `videos/`."),
                 unpack, install]
        for i, (name, what) in enumerate(steps, start=3):
            cells.append(("code", f"# {i}) {what}\n!python tools/kaggle_day4.py {name} 2>&1 | grep -v '^\\$' | tail -40"))
        cells.append(("code", "# summary + pictures\nprint(open('/kaggle/working/day4_summary.txt').read())\n"
                              "from IPython.display import Image, display\nimport glob\n"
                              "for f in sorted(glob.glob('/kaggle/working/plots/*_C*.jpg')): print(f); display(Image(f, width=1100))"))
    elif args.day == 5:
        cells = [("markdown", "# WIUT Hackathon — team mars · website pictures\n"
                              "Attach the output of the Day 4 run (**Add Input → Your Work → notebook857991aef6**): "
                              "it has the videos and `predictions_samples.json`. Then *Save & Run All*. "
                              "Download `examples.zip` from the Output tab."),
                 unpack, install,
                 ("code", "# 3) sample videos from the attached output\n"
                          "!python tools/kaggle_day4.py setup 2>&1 | grep -v '^\\$' | tail -5"),
                 ("code", "# 4) 3 pictures per event + timeline per video -> examples.zip\n"
                          "!python tools/kaggle_day4.py examples 2>&1 | grep -v '^\\$' | tail -20"),
                 ("code", "from IPython.display import Image, display\nimport glob\n"
                          "for f in sorted(glob.glob('/kaggle/working/examples/*/timeline.png')): print(f); display(Image(f))")]
    elif args.day == 3:
        steps = [("setup", "sample videos + 240-clip ACCIDENT dev set"),
                 ("nvdec", "GPU hardware-decode benchmark (for Part A)"),
                 ("cache", "detector + tracker once per video (~30 min)"),
                 ("flow", "usual traffic direction per image cell (lane directions)"),
                 ("ablate", "ablation table: day1 -> day2 -> day3, calibrator, threshold under a false-alarm limit"),
                 ("render", "alarm contact sheets + risk curves"),
                 ("harness", "official harness on C3905 with the final weights: timing + format check")]
        cells = [("markdown", "# WIUT Hackathon — Part B · Day 3\n"
                              "Fair dev metric, un-balanced calibrator, new features (DRAC, overlap growth, swerve, "
                              "flow anomaly). Runs unattended with *Save & Run All*; results in `day3_summary.txt`."),
                 unpack, install]
        for i, (name, what) in enumerate(steps, start=3):
            cells.append(("code", f"# {i}) {what}\n!python tools/kaggle_day3.py {name} 2>&1 | grep -v '^\\$' | tail -40"))
        cells.append(("code", "# summary + pictures\nprint(open('/kaggle/working/day3_summary.txt').read())\n"
                              "from IPython.display import Image, display\nimport glob\n"
                              "for f in sorted(glob.glob('/kaggle/working/plots/*.jpg')) + sorted(glob.glob('/kaggle/working/plots/*.png')): "
                              "print(f); display(Image(f, width=1100))"))
    else:
        cells = [
            ("markdown", "# WIUT Hackathon — Part B · Day 2: cache tracks, filters, calibrator, ablations\n"
                         "Needs: GPU T4, Internet On, dataset **picekl/accident**, sample videos in /tmp/samples "
                         "(cell 3 downloads them if missing). Then *Run All*."),
            unpack, install,
            ("code", "# 3) sample videos (team Drive copies) -> /tmp/samples if not there yet\n"
                     "import sys, glob; sys.path.insert(0, 'tools'); import kaggle_day1 as k\n"
                     "from pathlib import Path\n"
                     "if len(glob.glob('/tmp/samples/*.MP4')) < 3: k.download_samples(Path('/tmp/samples'), 3)\n"
                     "print(sorted(glob.glob('/tmp/samples/*')))"),
            ("code", "# 4) dev set (240 ACCIDENT clips) + decode benchmark\n!python tools/kaggle_day2.py setup 2>&1 | tail -3"),
            ("code", "# 5) detector + tracker once per video (slow part, ~20-30 min)\n!python tools/kaggle_day2.py cache 2>&1 | tail -6"),
            ("code", "# 6) ablations + calibrator + threshold grid (fast: replays the cache)\n!python tools/kaggle_day2.py ablate 2>&1 | grep -v '^\\$' | tail -25"),
            ("code", "# 7) what triggers alarms on the organizer camera\n!python tools/kaggle_day2.py render 2>&1 | tail -8"),
            ("code", "# 8) summary + pictures\nprint(open('/kaggle/working/day2_summary.txt').read())\n"
                     "from IPython.display import Image, display\nimport glob\n"
                     "for f in sorted(glob.glob('/kaggle/working/plots/alarms_*.jpg')): print(f); display(Image(f, width=1100))"),
        ]
    nb = {"cells": [], "nbformat": 4, "nbformat_minor": 5,
          "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                       "language_info": {"name": "python"}}}
    for kind, src in cells:
        c = {"cell_type": kind, "metadata": {}, "source": src}
        if kind == "code":
            c.update(outputs=[], execution_count=None)
        nb["cells"].append(c)
    out = REPO / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(nb, indent=1))
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
