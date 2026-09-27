import { useEffect, useState } from 'react';

export default function BBoxOverlay({ videoRef, detections = [] }) {
  const [activeObjects, setActiveObjects] = useState([]);

  useEffect(() => {
    const video = videoRef?.current;
    if (!video || detections.length === 0) {
      setActiveObjects([]);
      return undefined;
    }

    const syncActiveFrame = () => {
      const currentTime = video.currentTime;
      let low = 0;
      let high = detections.length - 1;
      let candidate = -1;
      while (low <= high) {
        const middle = (low + high) >> 1;
        if (detections[middle].time <= currentTime) {
          candidate = middle;
          low = middle + 1;
        } else {
          high = middle - 1;
        }
      }

      const nextFrameIndex = candidate >= 0 && currentTime - detections[candidate].time <= 0.8 ? candidate : -1;
      setActiveObjects(nextFrameIndex >= 0 ? detections[nextFrameIndex].objects : []);
    };

    const mediaEvents = ['timeupdate', 'seeked', 'loadedmetadata', 'play'];
    mediaEvents.forEach((eventName) => video.addEventListener(eventName, syncActiveFrame));
    syncActiveFrame();
    return () => mediaEvents.forEach((eventName) => video.removeEventListener(eventName, syncActiveFrame));
  }, [detections, videoRef]);

  return (
    <div className="tracking-overlay" aria-hidden="true">
      {activeObjects.map((object) => {
        const color = object.label === 'person' ? '#62d3d8' : object.label === 'bicycle' ? '#c18cf2' : '#f25540';
        const { x, y, w, h } = object.bbox;
        return (
          <div key={`${object.track_id}-${object.label}`} className="tracking-box" style={{
            left: `${x * 100}%`, top: `${y * 100}%`, width: `${w * 100}%`, height: `${h * 100}%`,
            '--track-color': color
          }}>
            <span className="tracking-label">{object.label} <b>#{object.track_id}</b> · {Math.round(object.confidence * 100)}%</span>
            <span className="tracking-center" />
          </div>
        );
      })}
    </div>
  );
}