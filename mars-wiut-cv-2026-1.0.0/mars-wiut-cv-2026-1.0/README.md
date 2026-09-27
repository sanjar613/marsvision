# Team mars — WIUT Hackathon 2026, Computer Vision track

We watch a fixed CCTV camera at a signalised intersection in Tashkent and do two things:

* **Part A:** list traffic events as `[start_sec, end_sec, label]`.
* **Part B:** give a causal risk score, at every frame, that an accident starts within 5 s.

| member | role |
|---|---|
| Dagarova Solikha | Part A (event detection) and Part B (accident anticipation): models, rules, experiments; integration and packaging |
| Yakshinboyev Asilbek | team member |
| Torexanov Sanjar | Website (demo, EDA, results pages) |

## Install and run

```bash
pip install -r requirements.txt
bash weights/download.sh        # optional: weights/yolo11s.pt is committed; this only checks / fetches it
python run_submission.py --videos /data/test --out predictions.json
```

* The run needs no internet. `weights/yolo11s.pt` (19 MB, Ultralytics YOLO11s, COCO) is in the repo, and `download.sh` checks its sha256.
* `solution.py` sets `YOLO_OFFLINE=1` before Ultralytics is imported, so the library makes no network checks on the offline machine.
* A GPU is used when one is visible (the target is a T4). Otherwise it runs on the CPU.
* `run_submission.py` and `evaluate.py` are the organizers' files, unchanged.
* `predictions_samples.json` is our output on the sample videos. It was made with the command above on a Kaggle T4.

Check the output format and run the tests:

```bash
python evaluate.py --pred predictions_samples.json --validate-only
python -m pytest tests        # 24 tests on synthetic boxes and tracks, no video needed
```

## Layout

```
solution.py        the interface: CLASSES, detect_events (Part A), RiskEstimator (Part B)
src/scene.py       scene layout of this camera: road, crossings, islands, bus stop, signal queues
src/events.py      Part A: frame sampling, detection, stopped_vehicle + jaywalking rules
src/tracking.py    YOLO11s + ByteTrack, per-track histories (shared detector code)
src/risk.py        Part B: pair features (time-to-collision, closing speed, braking, ...), calibrator, alarm
src/video.py       fast sampled video reading (PyAV)
weights/           yolo11s.pt, download.sh, risk_calibrator.json (learned Part B weights)
tests/             unit tests
tools/             experiment scripts: caching, replay with the official metric, calibrator training,
                   lane-direction map, renderers for the website, Kaggle drivers (kaggle_day1..4.py)
notebooks/         the Kaggle notebooks we ran (each one embeds the repo, so it is self-contained)
```

## Approach

```
               ┌── Part A (whole file, any order) ──────────────────────────────────────────┐
 video.mp4 ──► │ keyframes only (every 0.5 s) → YOLO11s @1280 → boxes → rules on scene zones │ → events
               └─────────────────────────────────────────────────────────────────────────────┘
               ┌── Part B (causal, frame by frame inside step()) ─────────────────────────────┐
 frames ─────► │ every 4th frame → YOLO11s @640 → ByteTrack → pair features → logistic → alarm │ → risk
               └─────────────────────────────────────────────────────────────────────────────┘
```

### Scene layout (`src/scene.py`)

The task allows hard-coding facts about the scene. We drew polygons once on a sample frame and stored them normalised to [0, 1]:

* the carriageway;
* the three zebra crossings;
* the median, sign island and three refuge islands;
* the kerb-side parking strip;
* the bus stop;
* the two signal approaches where cars queue at red.

`tools/render_scene.py` draws them on any frame.

### Part A — event detection (`src/events.py`), rule-based

* **Frame sampling.** The organizer videos have a keyframe every 0.5 s. We read the packet headers first. If keyframes are ≤ 1 s apart, we decode only the keyframes (PyAV `skip_frame="NONKEY"`). That gives 2 samples per second at a fraction of the cost of full 4K decoding. Otherwise we fully decode at 2 fps. Times use the harness clock (frame index / fps).
* **Detection.** YOLO11s at 1280 px (pedestrians are small at this distance) on 1920-px frames, confidence ≥ 0.35. We use persons, bicycles, cars, motorcycles, buses and trucks. There is no tracker, because at 2 fps simple box matching is more reliable.
* **stopped_vehicle** ("stationary on the carriageway ≥ 10 s, not in a queue at a signal"):
  * A vehicle box that keeps IoU ≥ 0.6 with itself across samples is "standing".
  * It may be hidden for up to 3 s (passing traffic).
  * If it moves more than 0.25 of its own height, it has moved again.
  * The bottom-centre point must be on the carriageway. Buses at the bus stop don't count.
  * Minimum length is 12 s (10 s plus a margin for sampling). Inside a signal approach it is 150 s, which is longer than any red phase, so normal queues are never reported.
  * Overlapping segments are merged into one, as the FAQ asks.
* **jaywalking** ("a pedestrian on the carriageway outside a crossing"):
  * At each sample we ask: is any person's foot point on the carriageway, outside every zebra crossing and outside the bus-stop kerb, not on a two-wheeler (a rider) and not inside a vehicle box?
  * A "person" box that stays in one place for 15 s or more is ignored, even if it is missed for up to 10 s at a time. It is a pole, a road worker or someone waiting, not someone crossing, and such false detections flicker at night.
  * Runs of "yes" become segments. Gaps ≤ 1.5 s are merged, and a segment needs ≥ 1.5 s and ≥ 2 samples.
  * Both filters came from checking the event pictures on sample video C3905. Before them, people waiting at the bus stop produced an 80-s "jaywalking" segment.
* The other 12 classes are not predicted. The metric scores a predicted class that never occurs as 0, so we only report classes our rules handle reliably.

### Part B — accident anticipation (`src/risk.py`), rule-based features + a small learned calibrator

* **Frames.** Every round(fps / 8)-th frame goes through YOLO11s at 640 px and ByteTrack. The other frames repeat the last score. Everything depends only on past frames. Part B does not use Part A's output.
* **Features, per pair of nearby road users:**
  * Footprint time-to-collision.
  * Closing speed, and the deceleration needed to avoid a crash (DRAC).
  * Rising box overlap.
  * Braking while in conflict, and swerving.
  * Wrong-way motion against a lane-direction map learned online.
  * A 1-second memory (max and rise of the best pair).
* **Filters:** oncoming/adjacent lanes, standing queues and very young tracks are ignored. Distances are measured in box heights, so no camera calibration is needed.
* **Calibration.** A 12-weight logistic regression (`weights/risk_calibrator.json`) turns the features into a probability. An EMA and alarm hysteresis then give one alarm block per event and a 3-s warm-up. When idle, the score stays below 0.5.

### What is learned and what is rule-based

* **Learned:** the detector (pre-trained COCO weights, not fine-tuned) and the Part B logistic calibrator (trained on the ACCIDENT benchmark).
* **Rule-based:** the scene zones, all Part A rules, tracking, Part B geometry features and alarm logic.

## Data, models, licences

| what | use | licence |
|---|---|---|
| Organizer sample videos (4K, 29.97 fps) | scene layout, negatives for Part B, timing, `predictions_samples.json` | hackathon data |
| ACCIDENT benchmark, real CCTV clips (Kaggle `picekl/accident`) | Part B dev set and calibrator training (70/30 split by clip-name hash) | CC BY-NC-SA 4.0 |
| COCO (through the YOLO11 weights) | detector pre-training | CC BY 4.0 (annotations) |
| Ultralytics YOLO11s + ByteTrack implementation (`ultralytics==8.4.160`) | detector, tracker | AGPL-3.0 |
| PyAV / FFmpeg, OpenCV, NumPy | video decoding, image ops | BSD / LGPL, Apache-2.0, BSD |

We used no closed models or paid APIs at any stage. AI assistants helped write code and text.

## Results

### Part B (official metric; test = 30% of 240 ACCIDENT clips + organizer video C3905 as normal traffic)

| variant | Score B | AP | alarm P / R | false alarms / min (organizer camera) | first alarm < 4 s |
|---|---|---|---|---|---|
| A · hand formula | 0.102 | 0.000 | 0.44 / 0.15 | 3.29 | 41% |
| B · + lane / queue / age filters | 0.070 | 0.000 | 0.36 / 0.10 | 3.76 | 33% |
| C · no "overlap = collision", 3-s warm-up | 0.027 | 0.000 | 0.27 / 0.04 | 2.35 | 0% |
| D · class-balanced calibrator | 0.467 ⚠ | 0.080 | 0.86 / 0.87 | 0.47 | **100%** |
| **E · un-balanced calibrator (shipped)** | 0.039 | **0.097** | – (no alarms) | **0.00** | – |
| F · E + learned lane-direction prior | 0.041 | 0.103 | – (no alarms) | 0.00 | – |

**D is an artefact, not a result.** It fires right after the warm-up in every clip. ACCIDENT clips are short, and the crash usually happens in the first 10 s, so an early alarm "matches". We added the last column to catch this.

E ranks pre-crash frames better than chance (AP 0.10) and gives zero false alarms on 13 min of organizer video.

### Part A (sample videos)

We have no labels for the sample videos, so we can't give an F1. Instead we checked every detected event by eye on its contact sheet (`tools/render_scene.py --pred`). Counts per video (from `predictions_samples.json`):

| video | stopped_vehicle | jaywalking |
|---|---|---|
| C3896.MP4 (340 s, day) | 2 | 18 |
| C3897.MP4 (318 s, day) | 3 | 17 |
| C3905.MP4 (128 s, dusk/night) | 1 | 11 |

Honest reading of the pictures:
* The stopped_vehicle segments are vehicles that stand still for minutes. We don't know whether the annotators count long kerb-side waits as events.
* Many jaywalking segments are people crossing just outside the painted zebra, or stepping off the kerb near it. Some are false detections at night. Precision is unknown without labels.

### Runtime (official harness, Kaggle T4, 4 CPU cores; budget 3× duration for A + B)

| video | duration | Part A | Part B | total | × duration |
|---|---|---|---|---|---|
| C3896.MP4 (4K, 29.97 fps) | 340.3 s | 220.4 s | 534.0 s | 754.4 s | **2.22×** |
| C3897.MP4 | 317.8 s | 200.9 s | 495.8 s | 696.6 s | **2.19×** |
| C3905.MP4 | 127.6 s | 67.5 s | 193.0 s | 260.4 s | **2.04×** |

Measured with the official `run_submission.py` in a fresh virtualenv after `pip install -r requirements.txt`. Two consecutive runs gave identical events and risk curves (max difference 0.0000).

Earlier measurement for Part B alone: 1.55× duration on C3905, almost all of it the harness decoding 4K frames. Part A decodes only keyframes: 2.1× faster than real time on its own, about 0.5× duration.

Two safety nets keep a video inside the budget:

* Part A stops sampling after 0.8× the video duration of wall time and returns what it found.
* Part B reads Part A's wall time (only the time, never its events). If the projected total goes above 2.6×, it halves its frame rate.

## Seeds and determinism

* `random`, `numpy` and `torch` are seeded with 0.
* cuDNN runs in deterministic mode (`benchmark=False, deterministic=True`).
* Calibrator training is full-batch gradient descent, which is deterministic.
* Part A has no randomness. It depends only on the keyframes of the file.
* The Day 4 notebook runs the harness twice and compares the outputs.
* Two known sources of variation:
  * GPU vs CPU inference can change boxes at floating-point level.
  * Part B's frame-rate fallback only triggers on a machine slower than our budget plan. It never triggered in our runs.

## Reproduce the experiments

All experiments ran on Kaggle (GPU T4).

* `notebooks/day1..day4_kaggle.ipynb` are the exact notebooks. Each one embeds the repo and calls `tools/kaggle_dayN.py`.
* `tools/cache_tracks.py` runs the detector and tracker once per video. `tools/replay.py` then scores Part B variants with the official metric in seconds.
* `tools/train_calibrator.py` trains the logistic calibrator.
* `tools/build_flow_prior.py` builds the lane-direction map.
* `tools/render_scene.py`, `tools/render_video.py` and `tools/export_examples.py` make the website pictures (one per event moment, plus a timeline per video) and the annotated videos.

## Limits and next steps

* Part A covers 2 of 14 classes, and the scene polygons were drawn by hand on one frame. The next steps would be to label the samples for a real dev set, then add wrong_way (lane-direction map + tracks), red_light (signal state from the visible signal heads) and failure_to_yield (vehicle in a crossing while a pedestrian is on it).
* Part B's geometric features are weak predictors (train AUC 0.60). Time-to-collision is reliable only about 2 s ahead. A learned video model fine-tuned on accident datasets would be the next step.
* GPU video decoding (NVDEC via PyNvVideoCodec) failed on these files (`PyNvVCExceptionUnsupported`), so all decoding is on the CPU. `src/video.py` keeps a CPU fallback.

## Licence

AGPL-3.0 (see `LICENSE`), because the package uses Ultralytics YOLO11, which is AGPL-3.0. Our own code is shared under the same licence.
