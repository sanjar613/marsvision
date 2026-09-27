import cv2
cv2.setNumThreads(1)
import tempfile
import os
import math
from pathlib import Path
from fastapi.concurrency import run_in_threadpool
from schemas.response import AnalysisResponse, BBox, DetectionFrame, EventItem, TrackedObject
from solution import RiskEstimator, detect_events
from src.tracking import ROAD_USERS

VISUALIZATION_INTERVAL = 0.5


def run_cv_pipeline(video_path: Path) -> AnalysisResponse:
    raw_events = detect_events(str(video_path))
    capture = cv2.VideoCapture(str(video_path))

    try:
        if not capture.isOpened():
            raise ValueError("Unable to read uploaded video")

        fps = float(capture.get(cv2.CAP_PROP_FPS))
        if not math.isfinite(fps) or fps <= 0:
            fps = 25.0

        metadata = {
            "video_id": video_path.name,
            "fps": fps,
            "width": int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "n_frames": int(capture.get(cv2.CAP_PROP_FRAME_COUNT)),
        }
        estimator = RiskEstimator()
        estimator.reset(metadata)

        risk_curve = []
        detections = []
        next_visualization_time = 0.0
        frame_index = 0
        while True:
            success, frame = capture.read()
            if not success:
                break

            timestamp = frame_index / fps
            inference_frame = frame_index % estimator.stride == 0
            score = estimator.step(frame, timestamp)
            risk_curve.append((timestamp, float(score)))

            if inference_frame and timestamp >= next_visualization_time:
                height, width = frame.shape[:2]
                objects = []
                for row in estimator.tracker.last_rows:
                    track_id, class_id, x1, y1, x2, y2, confidence = row
                    left = max(0.0, min(1.0, float(x1) / width))
                    top = max(0.0, min(1.0, float(y1) / height))
                    right = max(left, min(1.0, float(x2) / width))
                    bottom = max(top, min(1.0, float(y2) / height))
                    objects.append(TrackedObject(
                        track_id=int(track_id),
                        label=ROAD_USERS.get(int(class_id), 'road_user'),
                        confidence=float(confidence),
                        bbox=BBox(x=left, y=top, w=right - left, h=bottom - top),
                    ))
                detections.append(DetectionFrame(time=timestamp, objects=objects))
                next_visualization_time = timestamp + VISUALIZATION_INTERVAL

            frame_index += 1

        if frame_index == 0:
            raise ValueError("Uploaded video contains no readable frames")
    finally:
        capture.release()

    events = [
        EventItem(start=float(start), end=float(end), label=str(label))
        for start, end, label in raw_events
    ]
    return AnalysisResponse(
        events=events,
        risk_curve=risk_curve,
        detections=detections,
        risk_threshold=float(estimator.model.cfg.alarm_on),
    )

async def process_video_file(file_bytes: bytes) -> AnalysisResponse:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)

    try:
        return await run_in_threadpool(run_cv_pipeline, tmp_path)
    finally:
        try:
            os.remove(tmp_path)
        except FileNotFoundError:
            pass