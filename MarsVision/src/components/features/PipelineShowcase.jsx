import { useEffect, useState } from 'react';
import { Activity, ArrowUpRight, Crosshair, Radar } from 'lucide-react';

const CHART_WIDTH = 560;
const CHART_HEIGHT = 142;
const CHART_GUTTER = 8;

function summarizeAnalysis(data) {
  const riskCurve = Array.isArray(data.risk_curve) ? data.risk_curve : [];
  const detections = Array.isArray(data.detections) ? data.detections : [];
  const threshold = Number.isFinite(data.risk_threshold) ? data.risk_threshold : 0.25;
  const trackIds = new Set();
  let peakRisk = 0;
  let peakTime = 0;

  for (const frame of detections) {
    for (const object of frame.objects || []) {
      if (Number.isFinite(object.track_id)) trackIds.add(object.track_id);
    }
  }

  for (const point of riskCurve) {
    if (!Array.isArray(point) || !Number.isFinite(point[0]) || !Number.isFinite(point[1])) continue;
    if (point[1] > peakRisk) {
      peakRisk = point[1];
      peakTime = point[0];
    }
  }

  const duration = riskCurve.length ? Number(riskCurve[riskCurve.length - 1][0]) || 0 : 0;
  const sampleCount = Math.min(riskCurve.length, 72);
  const plotPoints = Array.from({ length: sampleCount }, (_, index) => {
    const sourceIndex = sampleCount <= 1 ? 0 : Math.round(index * (riskCurve.length - 1) / (sampleCount - 1));
    const [time, score] = riskCurve[sourceIndex];
    const x = CHART_GUTTER + (duration > 0 ? time / duration : 0) * (CHART_WIDTH - CHART_GUTTER * 2);
    const y = CHART_GUTTER + (1 - Math.min(Math.max(score, 0), 1)) * (CHART_HEIGHT - CHART_GUTTER * 2);
    return `${index === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');

  return {
    duration,
    peakRisk,
    peakTime,
    threshold,
    trackCount: trackIds.size,
    detectionFrames: detections.length,
    sampleCount: riskCurve.length,
    plotPoints,
    source: data.source,
  };
}

const formatDuration = (seconds) => {
  const minutes = Math.floor(seconds / 60);
  const remainder = Math.floor(seconds % 60);
  return `${String(minutes).padStart(2, '0')}:${String(remainder).padStart(2, '0')}`;
};

export default function PipelineShowcase() {
  const [showcase, setShowcase] = useState(null);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetch('/marsvision-analysis.json', { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Sample analysis request failed: ${response.status}`);
        return response.json();
      })
      .then((data) => setShowcase(summarizeAnalysis(data)))
      .catch((error) => {
        if (error.name !== 'AbortError') setLoadError(true);
      });

    return () => controller.abort();
  }, []);

  const thresholdY = CHART_GUTTER + (1 - (showcase?.threshold ?? 0.25)) * (CHART_HEIGHT - CHART_GUTTER * 2);
  const areaPath = showcase?.plotPoints
    ? `${showcase.plotPoints} L${CHART_WIDTH - CHART_GUTTER},${CHART_HEIGHT - CHART_GUTTER} L${CHART_GUTTER},${CHART_HEIGHT - CHART_GUTTER} Z`
    : '';

  return (
    <section className="pipeline-showcase" aria-label="MarsVision pipeline showcase">
      <header className="showcase-heading">
        <div>
          <div className="showcase-kicker"><span className="showcase-orbit-dot" /> FIELD TEST / C3896</div>
          <h2>From pixels to risk, in real time.</h2>
          <p>One clip. Two connected models. Every tracked road user becomes a measurable safety signal.</p>
        </div>
        <a className="showcase-data-link" href="/marsvision-analysis.json" target="_blank" rel="noreferrer">
          View analysis data <ArrowUpRight size={14} />
        </a>
      </header>

      <div className="showcase-grid">
        <figure className="showcase-footage">
          <div className="showcase-footage-topline">
            <span><span className="record-indicator" /> MODEL OUTPUT / PART A</span>
            <span>YOLO11S <i /> BYTETRACK</span>
          </div>
          <img
            src="/example.gif"
            alt="Traffic footage annotated with YOLO11s object detections and ByteTrack identities"
            fetchPriority="high"
          />
          <figcaption>
            <span><Crosshair size={13} /> Detection + identity tracking</span>
            <span>OBJECT CLASSES / TRACK IDS / CONFIDENCE</span>
          </figcaption>
          <span className="footage-corner footage-corner-tl" />
          <span className="footage-corner footage-corner-br" />
        </figure>

        <section className="showcase-risk" aria-label="Accident anticipation sample analysis">
          <header className="showcase-risk-heading">
            <div>
              <div className="showcase-kicker"><Activity size={12} /> MODEL OUTPUT / PART B</div>
              <h3>Accident anticipation</h3>
            </div>
            <span className="sample-data-badge"><Radar size={12} /> SAMPLE RUN</span>
          </header>

          {loadError ? (
            <div className="showcase-risk-unavailable" role="status">Sample risk analysis is unavailable.</div>
          ) : (
            <>
              <div className="showcase-metrics" aria-live="polite">
                <div className="showcase-metric showcase-metric-peak">
                  <span>PEAK RISK</span>
                  <strong>{showcase ? showcase.peakRisk.toFixed(3) : '—'}</strong>
                  <small>{showcase ? `at ${formatDuration(showcase.peakTime)}` : 'loading sample'}</small>
                </div>
                <div className="showcase-metric">
                  <span>UNIQUE TRACKS</span>
                  <strong>{showcase ? showcase.trackCount : '—'}</strong>
                  <small>{showcase ? `${showcase.detectionFrames} tracked frames` : 'loading sample'}</small>
                </div>
              </div>

              <div className="showcase-chart-heading">
                <span>CALIBRATED RISK CURVE</span>
                <span>{showcase ? formatDuration(showcase.duration) : '--:--'} CLIP</span>
              </div>
              <div className={`showcase-chart${showcase ? ' is-loaded' : ''}`}>
                {showcase && (
                  <svg viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`} role="img" aria-label={`Risk peaks at ${showcase.peakRisk.toFixed(3)} at ${formatDuration(showcase.peakTime)}. Alarm threshold ${showcase.threshold.toFixed(2)}.`}>
                    <defs>
                      <linearGradient id="showcaseRiskFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#f25540" stopOpacity="0.3" />
                        <stop offset="100%" stopColor="#f25540" stopOpacity="0" />
                      </linearGradient>
                    </defs>
                    {[0.25, 0.5, 0.75].map((tick) => {
                      const y = CHART_GUTTER + (1 - tick) * (CHART_HEIGHT - CHART_GUTTER * 2);
                      return <line key={tick} x1={CHART_GUTTER} y1={y} x2={CHART_WIDTH - CHART_GUTTER} y2={y} className="showcase-chart-gridline" />;
                    })}
                    <line x1={CHART_GUTTER} y1={thresholdY} x2={CHART_WIDTH - CHART_GUTTER} y2={thresholdY} className="showcase-threshold-line" />
                    <path d={areaPath} fill="url(#showcaseRiskFill)" />
                    <path d={showcase.plotPoints} className="showcase-risk-line" />
                  </svg>
                )}
              </div>
              <div className="showcase-chart-axis"><span>00:00</span><span>00:{String(Math.floor((showcase?.duration || 0) / 2) % 60).padStart(2, '0')}</span><span>{showcase ? formatDuration(showcase.duration) : '--:--'}</span></div>

              <footer className="showcase-risk-footer">
                <span><i className="risk-legend-line" /> Risk score</span>
                <span><i className="threshold-legend-line" /> Alarm {showcase ? showcase.threshold.toFixed(2) : '0.25'}</span>
                <span>{showcase ? `${showcase.sampleCount.toLocaleString()} samples` : 'Fetching analysis'}</span>
              </footer>
            </>
          )}
        </section>
      </div>

      <div className="showcase-pipeline-strip">
        <span><b>01</b> Detect road users <i>YOLO11s</i></span>
        <span className="pipeline-connector" />
        <span><b>02</b> Maintain identities <i>ByteTrack</i></span>
        <span className="pipeline-connector" />
        <span><b>03</b> Estimate collision risk <i>Calibrated model</i></span>
      </div>
    </section>
  );
}