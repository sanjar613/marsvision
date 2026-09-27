import { useEffect, useMemo, useState } from 'react';
import { ScanEye } from 'lucide-react';

const formatTime = (time) => {
  const minutes = Math.floor(time / 60);
  const seconds = Math.floor(time % 60);
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
};

export default function DetectionInspector({ videoRef, detections = [], events = [], riskCurve = [] }) {
  const [playhead, setPlayhead] = useState(0);

  useEffect(() => {
    const video = videoRef?.current;
    if (!video) return undefined;
    const updatePlayhead = () => setPlayhead(video.currentTime || 0);
    const mediaEvents = ['timeupdate', 'seeked', 'loadedmetadata'];
    mediaEvents.forEach((eventName) => video.addEventListener(eventName, updatePlayhead));
    updatePlayhead();
    return () => mediaEvents.forEach((eventName) => video.removeEventListener(eventName, updatePlayhead));
  }, [videoRef]);

  const trackCount = useMemo(
    () => new Set(detections.flatMap((frame) => frame.objects.map((object) => object.track_id))).size,
    [detections]
  );
  const peakRisk = useMemo(() => riskCurve.reduce((peak, point) => {
    const score = Array.isArray(point) ? point[1] : point?.risk;
    return Number.isFinite(score) ? Math.max(peak, score) : peak;
  }, 0), [riskCurve]);

  let currentFrame = null;
  for (const frame of detections) {
    if (frame.time > playhead) break;
    currentFrame = frame;
  }
  const currentObjects = currentFrame && playhead - currentFrame.time <= 0.8 ? currentFrame.objects : [];

  return (
    <section className="detection-inspector" aria-label="Tracked object inspection">
      <header className="inspector-header">
        <div>
          <span>MODEL OUTPUT / CURRENT FRAME</span>
          <h3><ScanEye size={16} /> Tracked objects</h3>
        </div>
        <span className="inspector-time">{formatTime(playhead)}</span>
      </header>

      <div className="inspector-stats">
        <div><span>IN FRAME</span><strong>{currentObjects.length}</strong></div>
        <div><span>TRACK IDS</span><strong>{trackCount}</strong></div>
        <div><span>EVENTS</span><strong>{events.length}</strong></div>
        <div><span>PEAK RISK</span><strong>{peakRisk.toFixed(2)}</strong></div>
      </div>

      {detections.length === 0 ? (
        <p className="inspector-empty">This API response has no frame-level detections.</p>
      ) : currentObjects.length === 0 ? (
        <p className="inspector-empty">No road users detected at this time.</p>
      ) : (
        <div className="inspector-table-wrap">
          <table className="inspector-table">
            <thead><tr><th>TRACK ID</th><th>CLASS</th><th>CONFIDENCE</th></tr></thead>
            <tbody>
              {currentObjects.slice(0, 12).map((object) => (
                <tr key={`${object.track_id}-${object.label}`}>
                  <td>#{object.track_id}</td>
                  <td>{object.label.replaceAll('_', ' ')}</td>
                  <td>{Math.round(object.confidence * 100)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
          {currentObjects.length > 12 && <div className="inspector-overflow">+{currentObjects.length - 12} more objects in frame</div>}
        </div>
      )}
      <footer className="inspector-footer">YOLO11s detection · ByteTrack association</footer>
    </section>
  );
}