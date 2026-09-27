from pydantic import BaseModel, Field
from typing import List, Tuple, Optional

class BBox(BaseModel):
    x: float
    y: float
    w: float
    h: float

class EventItem(BaseModel):
    label: str
    start: float
    end: float
    confidence: Optional[float] = None
    bbox: Optional[BBox] = None


class TrackedObject(BaseModel):
    track_id: int
    label: str
    confidence: float
    bbox: BBox


class DetectionFrame(BaseModel):
    time: float
    objects: List[TrackedObject]


class AnalysisResponse(BaseModel):
    events: List[EventItem]
    risk_curve: List[Tuple[float, float]]
    detections: List[DetectionFrame] = Field(default_factory=list)
    risk_threshold: float = 0.25