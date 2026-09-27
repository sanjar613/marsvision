"""Fast sampled video reading (shared with Part A).

The organizer videos are 4K @ 30 fps; plain `cv2.VideoCapture.read()` decodes
~20 frames/s on a 4-core Kaggle CPU, which alone eats most of the time budget.
PyAV with frame-threaded decoding is several times faster, and only the frames
we keep are converted to numpy (optionally downscaled inside libswscale).

    for idx, t, frame in iter_frames(path, target_fps=8, width=1280):
        ...
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

import numpy as np


def video_info(path: str | Path) -> dict:
    import av

    with av.open(str(path)) as c:
        s = c.streams.video[0]
        fps = float(s.average_rate or s.guessed_rate or 25.0)
        n = s.frames or int(round(float(c.duration or 0) / 1e6 * fps))
        return {"fps": fps, "n_frames": n, "width": s.codec_context.width,
                "height": s.codec_context.height, "duration": n / fps if fps else 0.0}


def iter_frames(path: str | Path, target_fps: float | None = None, width: int | None = None,
                threads: int = 0) -> Iterator[tuple[int, float, np.ndarray]]:
    """Yield (frame_index, t_sec, BGR uint8 frame) for every `stride`-th frame.

    t_sec = frame_index / fps, the same clock the organizers' harness uses.
    width: resize so the frame is this wide (keeps aspect); None = native.
    """
    import av

    with av.open(str(path)) as c:
        s = c.streams.video[0]
        s.thread_type = "AUTO"
        if threads:
            s.codec_context.thread_count = threads
        fps = float(s.average_rate or s.guessed_rate or 25.0)
        stride = max(1, int(round(fps / target_fps))) if target_fps else 1
        out_w = out_h = None
        if width and width < s.codec_context.width:
            out_w = int(width)
            out_h = int(round(s.codec_context.height * width / s.codec_context.width / 2) * 2)
        for idx, fr in enumerate(c.decode(s)):
            if idx % stride:
                continue
            if out_w:
                img = fr.to_ndarray(format="bgr24", width=out_w, height=out_h)
            else:
                img = fr.to_ndarray(format="bgr24")
            yield idx, idx / fps, img


def benchmark(path: str | Path, seconds: float = 20.0, **kw) -> float:
    """Decoded-and-kept frames per second of wall time for the first `seconds` of video."""
    import time

    info = video_info(path)
    t0, n = time.perf_counter(), 0
    for _idx, t, _img in iter_frames(path, **kw):
        n += 1
        if t >= seconds:
            break
    dt = time.perf_counter() - t0
    return round(seconds / dt, 2) if dt else float("inf")  # video-seconds per wall-second


def iter_frames_gpu(path: str | Path, target_fps: float | None = None, batch: int = 32,
                    gpu_id: int = 0) -> Iterator[tuple[int, float, object]]:
    """Same as iter_frames, but decoded by the GPU's hardware decoder (NVDEC).

    Needs `pip install PyNvVideoCodec` and an NVIDIA GPU; yields RGB frames as
    DLPack-capable GPU objects (use torch.from_dlpack(f)). Falls back to the
    CPU reader (BGR numpy) if PyNvVideoCodec is not available.
    """
    try:
        import PyNvVideoCodec as nvc
        dec = nvc.SimpleDecoder(str(path), gpu_id=gpu_id, use_device_memory=True,
                                output_color_type=nvc.OutputColorType.RGB)
    except Exception:  # package missing, no GPU, or driver without video libraries
        yield from iter_frames(path, target_fps=target_fps)
        return
    info = video_info(path)
    fps = info["fps"]
    stride = max(1, int(round(fps / target_fps))) if target_fps else 1
    idx = list(range(0, len(dec), stride))
    for k in range(0, len(idx), batch):
        chunk = idx[k:k + batch]
        for i, fr in zip(chunk, dec.get_batch_frames_by_index(chunk)):
            yield i, i / fps, fr
