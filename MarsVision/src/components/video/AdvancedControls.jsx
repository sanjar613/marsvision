import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Download, Pause, Play, SkipBack, SkipForward } from 'lucide-react';

const colors = {
  panel: 'rgba(20, 19, 25, 0.82)',
  border: 'rgba(255, 255, 255, 0.08)',
  muted: '#8b949e',
  text: '#e2e8f0',
  danger: '#ff4757',
  info: '#65d0d9',
};

const formatTime = (seconds) => {
  if (!Number.isFinite(seconds) || seconds < 0) return '00:00';
  const minutes = Math.floor(seconds / 60);
  const remainder = Math.floor(seconds % 60);
  return `${String(minutes).padStart(2, '0')}:${String(remainder).padStart(2, '0')}`;
};

const seekMediaElement = (mediaElement, time) => {
  mediaElement.currentTime = Math.min(Math.max(time, 0), Number.isFinite(mediaElement.duration) ? mediaElement.duration : time);
};

export default function AdvancedControls({ videoRef, riskCurve = [], events = [], riskThreshold = 0.25, frameRate = 25 }) {
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    const video = videoRef?.current;
    if (!video) return undefined;

    const syncState = () => {
      setCurrentTime(video.currentTime || 0);
      setDuration(Number.isFinite(video.duration) ? video.duration : 0);
      setIsPlaying(!video.paused && !video.ended);
      setPlaybackRate(video.playbackRate || 1);
    };
    const mediaEvents = ['timeupdate', 'durationchange', 'loadedmetadata', 'play', 'pause', 'ratechange', 'ended'];
    mediaEvents.forEach((eventName) => video.addEventListener(eventName, syncState));
    syncState();

    return () => mediaEvents.forEach((eventName) => video.removeEventListener(eventName, syncState));
  }, [videoRef]);

  const riskSegments = riskCurve.reduce((segments, point, index) => {
    const [time, score] = Array.isArray(point) ? point : [point.time, point.risk];
    if (score < riskThreshold || duration <= 0) return segments;
    const nextPoint = riskCurve[index + 1];
    const nextTime = Array.isArray(nextPoint) ? nextPoint[0] : nextPoint?.time;
    const start = Math.max(0, time);
    const end = Math.min(duration, nextTime ?? time + 1);
    const previous = segments.at(-1);
    if (previous && start <= previous.end + 0.08) previous.end = end;
    else segments.push({ start, end });
    return segments;
  }, []);

  const seekTo = (time) => {
    const video = videoRef?.current;
    if (!video) return;
    seekMediaElement(video, time);
  };

  const togglePlayback = () => {
    const video = videoRef?.current;
    if (!video) return;
    if (video.paused) video.play().catch(() => {});
    else video.pause();
  };

  const changePlaybackRate = (event) => {
    const rate = Number(event.target.value);
    setPlaybackRate(rate);
    if (videoRef?.current) videoRef.current.playbackRate = rate;
  };

  const exportFrame = () => {
    const video = videoRef?.current;
    if (!video || !video.videoWidth || !video.videoHeight || exporting) return;

    setExporting(true);
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext('2d');
    context?.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (blob) {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `marsvision-frame-${formatTime(video.currentTime).replace(':', '-')}.png`;
        document.body.append(link);
        link.click();
        link.remove();
        window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      }
      setExporting(false);
    }, 'image/png');
  };

  const buttonStyle = {
    width: '38px',
    height: '38px',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: colors.text,
    background: 'rgba(255,255,255,0.04)',
    border: `1px solid ${colors.border}`,
    borderRadius: '6px',
    cursor: 'pointer',
  };

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      aria-label="Video playback controls"
      style={{ padding: '14px 16px', marginTop: '10px', background: colors.panel, border: `1px solid ${colors.border}`, borderRadius: '8px', backdropFilter: 'blur(12px)' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
        <button type="button" aria-label="Previous frame" title="Previous frame" onClick={() => seekTo(currentTime - 1 / Math.max(frameRate, 1))} style={buttonStyle}>
          <SkipBack size={17} />
        </button>
        <button type="button" aria-label={isPlaying ? 'Pause video' : 'Play video'} title={isPlaying ? 'Pause' : 'Play'} onClick={togglePlayback} style={{ ...buttonStyle, color: colors.info, background: 'rgba(101,208,217,0.08)', borderColor: 'rgba(101,208,217,0.24)' }}>
          {isPlaying ? <Pause size={17} /> : <Play size={17} />}
        </button>
        <button type="button" aria-label="Next frame" title="Next frame" onClick={() => seekTo(currentTime + 1 / Math.max(frameRate, 1))} style={buttonStyle}>
          <SkipForward size={17} />
        </button>

        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: '4px', color: colors.muted, fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '12px' }}>
          SPEED
          <select aria-label="Playback speed" value={playbackRate} onChange={changePlaybackRate} style={{ color: colors.text, background: '#11141a', border: `1px solid ${colors.border}`, borderRadius: '5px', padding: '7px 9px' }}>
            {[0.5, 1, 2, 4].map((rate) => <option key={rate} value={rate}>{rate}x</option>)}
          </select>
        </label>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: '1 1 240px', minWidth: '180px', marginLeft: '4px' }}>
          <span style={{ color: colors.muted, fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '11px', minWidth: '38px' }}>{formatTime(currentTime)}</span>
          <input
            aria-label="Video timeline; red regions indicate elevated risk"
            type="range"
            min="0"
            max={duration || 0}
            step="0.01"
            value={Math.min(currentTime, duration || 0)}
            onChange={(event) => seekTo(Number(event.target.value))}
            style={{ width: '100%', height: '6px', accentColor: colors.danger, cursor: duration ? 'pointer' : 'default', background: `linear-gradient(90deg, ${colors.info} 0%, ${colors.info} ${duration ? currentTime / duration * 100 : 0}%, rgba(255,255,255,0.12) ${duration ? currentTime / duration * 100 : 0}%, rgba(255,255,255,0.12) 100%)`, borderRadius: '99px' }}
          />
          <span style={{ color: colors.muted, fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '11px', minWidth: '38px', textAlign: 'right' }}>{formatTime(duration)}</span>
        </div>

        <button type="button" onClick={exportFrame} disabled={!duration || exporting} title="Export current frame as PNG" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', minHeight: '38px', padding: '0 12px', color: exporting ? colors.muted : colors.text, background: 'rgba(101,208,217,0.08)', border: '1px solid rgba(101,208,217,0.26)', borderRadius: '6px', cursor: !duration || exporting ? 'not-allowed' : 'pointer', fontSize: '12px', fontWeight: 700 }}>
          <Download size={15} /> {exporting ? 'Exporting…' : 'Export Frame'}
        </button>
      </div>

      {duration > 0 && (
        <div className="analysis-timeline" aria-label="Clip analysis timeline">
          <div className="analysis-timeline-lane" aria-label="Detected events">
            <span className="analysis-timeline-label">EVENTS</span>
            <div className="analysis-timeline-track">
              {events.filter((event) => Number.isFinite(event.start) && Number.isFinite(event.end)).map((event, index) => {
                const color = event.label === 'jaywalking' ? colors.danger : '#e8aa56';
                return (
                  <button
                    key={`${event.label}-${event.start}-${index}`}
                    type="button"
                    className="analysis-event-marker"
                    aria-label={`Seek to ${event.label} event at ${formatTime(event.start)}`}
                    title={`${event.label.replaceAll('_', ' ')} · ${formatTime(event.start)}–${formatTime(event.end)}`}
                    onClick={() => seekTo(event.start)}
                    style={{ left: `${Math.min(event.start / duration, 1) * 100}%`, width: `${Math.max((event.end - event.start) / duration * 100, 0.5)}%`, '--event-color': color }}
                  />
                );
              })}
            </div>
          </div>
          <div className="analysis-timeline-lane" aria-label={`Risk score above ${riskThreshold.toFixed(2)}`}>
            <span className="analysis-timeline-label">RISK</span>
            <div className="analysis-timeline-track analysis-risk-track">
              <span className="analysis-risk-threshold" style={{ left: `${riskThreshold * 100}%` }} title={`Calibrated alarm threshold: ${riskThreshold.toFixed(2)}`} />
              {riskSegments.map((segment, index) => (
                <span key={`${segment.start}-${index}`} className="analysis-risk-marker" style={{ left: `${segment.start / duration * 100}%`, width: `${Math.max((segment.end - segment.start) / duration * 100, 0.25)}%` }} />
              ))}
            </div>
          </div>
        </div>
      )}
    </motion.section>
  );
}
