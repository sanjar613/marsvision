import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity, ArrowDown, Download, FileVideo, Video } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';

import { useVideoAnalysis } from '../hooks/useVideoAnalysis';
import FileUploadZone from '../components/ui/FileUploadZone';
import EventTimeline from '../components/features/EventTimeline';
import DetectionInspector from '../components/features/DetectionInspector';
import PipelineShowcase from '../components/features/PipelineShowcase';
import RiskChart from '../components/features/RiskChart';
import BBoxOverlay from '../components/video/BBoxOverlay';
import LiveConsole from '../components/features/LiveConsole';
import AdvancedControls from '../components/video/AdvancedControls';
import HardwareMonitor from '../components/features/HardwareMonitor';
import IntersectionHeatmap from '../components/features/IntersectionHeatmap';
import ScenarioLauncher from '../components/features/ScenarioLauncher';
import { demoScenarios } from '../utils/demoScenarios';

export default function LiveDemo() {
  const { result, loading, error, processVideo, clearError } = useVideoAnalysis();
  const location = useLocation();
  const navigate = useNavigate();
  const [videoUrl, setVideoUrl] = useState(null);
  const [activeScenario, setActiveScenario] = useState(null);
  const [scenarioTime, setScenarioTime] = useState(0);
  const videoRef = useRef(null);
  const uploadHeadingRef = useRef(null);
  const focusUploadRequest = location.state?.focusUpload;
  const focusUploadRequested = Boolean(focusUploadRequest);
  const visibleVideoUrl = focusUploadRequested ? null : videoUrl;
  const routedScenario = demoScenarios.find((scenario) => scenario.id === location.state?.scenarioId);
  const selectedScenario = focusUploadRequested ? null : activeScenario || routedScenario;
  const analysisEvents = selectedScenario?.events || result.events;
  const analysisRiskCurve = selectedScenario?.risk_curve || result.risk_curve;

  useEffect(() => () => {
    if (videoUrl) URL.revokeObjectURL(videoUrl);
  }, [videoUrl]);

  useEffect(() => {
    if (!focusUploadRequest || loading) return undefined;
    const frame = window.requestAnimationFrame(() => {
      const heading = uploadHeadingRef.current;
      if (heading) {
        const behavior = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
        heading.scrollIntoView({ behavior, block: 'start' });
        heading.focus({ preventScroll: true });
      }
    });

    return () => window.cancelAnimationFrame(frame);
  }, [focusUploadRequest, loading]);

  const colors = { primary: '#f25540', text: '#e2e8f0', border: '#2b2b33', panel: '#14151b', info: '#65d0d9' };

  const handleUpload = async (file) => {
    if (!file) return;
    navigate('/', { replace: true, state: null });
    setActiveScenario(null);
    clearError();
    setVideoUrl(URL.createObjectURL(file));
    await processVideo(file);
  };

  const selectScenario = (scenario) => {
    clearError();
    navigate('/', { replace: true, state: null });
    setVideoUrl(null);
    setActiveScenario(scenario);
    setScenarioTime(0);
  };

  const resetAnalysis = () => {
    clearError();
    navigate('/', { replace: true, state: null });
    setVideoUrl(null);
    setActiveScenario(null);
    setScenarioTime(0);
  };

  const exportAnalysis = () => {
    const payload = {
      source: selectedScenario ? 'synthetic-demo-scenario' : 'backend-video-analysis',
      scenario: selectedScenario?.id,
      exported_at: new Date().toISOString(),
      events: analysisEvents,
      risk_curve: analysisRiskCurve,
      detections: result.detections,
      risk_threshold: result.risk_threshold,
    };
    const blobUrl = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = `marsvision-${selectedScenario?.id || 'analysis'}.json`;
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
  };

  const seekVideo = (time) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      videoRef.current.play();
    }
  };

  const jumpToUpload = () => {
    const heading = uploadHeadingRef.current;
    if (!heading) return;
    const behavior = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
    heading.scrollIntoView({ behavior, block: 'start' });
    heading.focus({ preventScroll: true });
  };

  return (
    <div className="monitor-page">
      <header className="monitor-header">
        <div className="monitor-title-block">
          <div className="monitor-eyebrow"><span className="eyebrow-pulse" />TRAFFIC SAFETY / CONTROL ROOM</div>
          <h1>Live traffic monitor</h1>
          <p>Review road events, movement conflicts, and collision risk from a single camera view.</p>
        </div>
        <div className="monitor-header-actions">
          <div className="monitor-header-status">
            <span className="header-status-icon"><Activity size={17} /></span>
            <div><strong>Analysis workspace</strong><span>{loading ? 'Analysis in progress' : error ? 'Analysis needs attention' : selectedScenario ? 'Simulation selected' : visibleVideoUrl ? 'Clip analysis complete' : 'Ready for a video source'}</span></div>
          </div>
            {!loading && !visibleVideoUrl && !selectedScenario && (
            <button type="button" className="monitor-try-demo" onClick={jumpToUpload}>
              Try demo <ArrowDown size={16} />
            </button>
          )}
        </div>
      </header>

      {!loading && !visibleVideoUrl && !selectedScenario && (
        <>
          <ScenarioLauncher scenarios={demoScenarios} onSelect={selectScenario} />
          <PipelineShowcase />
        </>
      )}

      {!loading && !visibleVideoUrl && !selectedScenario && (
        <div className="monitor-capabilities" aria-label="Analysis capabilities">
          <div className="capability-item"><span className="capability-icon"><FileVideo size={16} /></span><div><span>INPUT FORMATS</span><strong>MP4 · AVI · MOV</strong></div></div>
          <div className="capability-item"><span className="capability-icon"><Video size={16} /></span><div><span>ANALYSIS PATHS</span><strong>Clip upload or scenario replay</strong></div></div>
          <div className="capability-item"><span className="capability-icon"><Activity size={16} /></span><div><span>REVIEW OUTPUTS</span><strong>Events · risk · spatial clusters</strong></div></div>
        </div>
      )}

      {error && (
        <div role="alert" style={{ padding: '14px', backgroundColor: 'rgba(255, 71, 87, 0.1)', color: colors.primary, borderRadius: '6px', border: `1px solid ${colors.primary}`, fontSize: '13px' }}>
          Analysis could not complete: {error}
        </div>
      )}

      {!loading && !visibleVideoUrl && !selectedScenario && (
        <div className="monitor-start-grid monitor-upload-layout">
          <section className="ingest-panel">
            <div className="ingest-panel-heading"><span>01 / ANALYZE FOOTAGE</span><span className="ingest-tag">SERVER INFERENCE</span></div>
            <h2 id="video-upload-heading" ref={uploadHeadingRef} tabIndex={-1} className="upload-target-heading">Start with a traffic clip</h2>
            <p className="ingest-intro">Send camera footage to the configured MarsVision API and inspect its event timeline, risk curve, and spatial clusters.</p>
            <FileUploadZone onUpload={handleUpload} disabled={loading} />
            <div className="engine-notice">
              <span>MODEL STACK</span>
              <p>YOLO11s detects road users and ByteTrack follows them across frames. Event rules and calibrated collision-risk scoring use the competition junction layout; other camera views may reduce event accuracy.</p>
            </div>
            <div className="data-note">
              <span>DATA HANDLING</span>
              <p>The clip is sent to the configured backend for processing; its temporary video file is removed after the request.</p>
            </div>
          </section>
        </div>
      )}

      {loading && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ padding: '52px 24px', textAlign: 'center', backgroundColor: colors.panel, borderRadius: '8px', border: `1px dashed ${colors.primary}` }}>
          <motion.div animate={{ opacity: [0.55, 1, 0.55] }} transition={{ duration: 1.6, repeat: Infinity }} style={{ color: colors.primary, fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '13px', letterSpacing: '0.04em' }}>
            &gt; Initializing MarsVision analysis...
            <br/><br/>
            &gt; Processing video stream (detection + risk)...
          </motion.div>
        </motion.div>
      )}

      {(visibleVideoUrl || selectedScenario) && !loading && !error && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '9px' }}>
              <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: selectedScenario ? '#f6b84a' : '#35d39a' }} />
              <span style={{ color: selectedScenario ? '#f6b84a' : '#f25540', fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '10px' }}>{selectedScenario ? 'SIMULATED SCENARIO' : 'YOLO11S + BYTETRACK'}</span>
              <span style={{ color: '#8b949e', fontSize: '11px' }}>{selectedScenario?.title || 'Uploaded clip'}</span>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button type="button" onClick={exportAnalysis} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '7px 10px', color: '#cbd5e1', background: 'rgba(242,85,64,0.1)', border: '1px solid rgba(242,85,64,0.25)', borderRadius: '5px', cursor: 'pointer', fontSize: '11px' }}><Download size={13} /> Export JSON</button>
              <button type="button" onClick={resetAnalysis} style={{ padding: '7px 10px', color: '#cbd5e1', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '5px', cursor: 'pointer', fontSize: '11px' }}>New analysis</button>
            </div>
          </div>

          <div className={visibleVideoUrl ? 'analysis-review-grid' : 'scenario-review-grid'}>
            {visibleVideoUrl ? (
              <section className="video-review-panel">
                <h3>UPLOADED CLIP / LIVE DETECTION OVERLAY</h3>
                <div className="video-review-frame">
                  <video ref={videoRef} src={visibleVideoUrl} controls style={{ width: '100%', display: 'block' }} />
                  <BBoxOverlay videoRef={videoRef} detections={result.detections} />
                </div>
                <AdvancedControls videoRef={videoRef} riskCurve={result.risk_curve} events={result.events} riskThreshold={result.risk_threshold} />
              </section>
            ) : (
              <section style={{ minWidth: 0, padding: '18px', background: colors.panel, border: `1px solid ${colors.border}`, borderRadius: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'center' }}>
                  <span style={{ color: '#f6b84a', fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '10px' }}>SYNTHETIC REPLAY / NO CAMERA FOOTAGE</span>
                  <span style={{ color: '#8b949e', fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '10px' }}>{scenarioTime.toFixed(1)}s / {selectedScenario.duration}s</span>
                </div>
                <h3 style={{ margin: '12px 0 6px', color: colors.text, fontSize: '18px' }}>{selectedScenario.title}</h3>
                <p style={{ color: '#8b949e', fontSize: '12px', lineHeight: 1.6 }}>{selectedScenario.summary}</p>
                <div style={{ marginTop: '24px', padding: '18px', border: '1px solid rgba(59,130,246,0.16)', borderRadius: '6px', background: 'linear-gradient(135deg, rgba(59,130,246,0.06), rgba(255,71,87,0.04))' }}>
                  <div style={{ color: '#8b949e', fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '9px', letterSpacing: '0.1em' }}>EVENT SEQUENCE</div>
                  <div style={{ display: 'flex', gap: '7px', alignItems: 'center', marginTop: '14px' }}>
                    {selectedScenario.events.map((scenarioEvent) => <span key={`${scenarioEvent.label}-${scenarioEvent.start}`} style={{ width: '8px', height: '8px', borderRadius: '50%', background: scenarioEvent.label === 'jaywalking' ? colors.primary : '#f59e0b', boxShadow: `0 0 12px ${scenarioEvent.label === 'jaywalking' ? colors.primary : '#f59e0b'}` }} title={`${scenarioEvent.label} at ${scenarioEvent.start}s`} />)}
                    <span style={{ color: '#cbd5e1', fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '11px' }}>{selectedScenario.events.length} illustrative detections</span>
                  </div>
                  <input aria-label="Scenario replay position" type="range" min="0" max={selectedScenario.duration} step="0.1" value={scenarioTime} onChange={(event) => setScenarioTime(Number(event.target.value))} style={{ width: '100%', marginTop: '18px', accentColor: colors.info }} />
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#778394', fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '9px' }}><span>00:00</span><span>00:{String(selectedScenario.duration).padStart(2, '0')}</span></div>
                </div>
              </section>
            )}

            <div className="analysis-review-sidebar">
              {visibleVideoUrl ? (
                <DetectionInspector videoRef={videoRef} detections={result.detections} events={result.events} riskCurve={result.risk_curve} />
              ) : (
                <section style={{ minWidth: 0, backgroundColor: colors.panel, padding: '18px', borderRadius: '8px', border: `1px solid ${colors.border}` }}>
                  <h3 style={{ margin: '0 0 6px', color: '#8b949e', fontSize: '12px', fontFamily: 'ui-monospace, Consolas, monospace' }}>ILLUSTRATIVE JUNCTION MAP</h3>
                  <p style={{ marginBottom: '13px', color: '#778394', fontSize: '10px' }}>Reference activity only · not generated by the selected scenario</p>
                  <IntersectionHeatmap />
                </section>
              )}
              <EventTimeline events={analysisEvents} onSeek={selectedScenario ? setScenarioTime : seekVideo} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 340px), 1fr))', gap: '18px', alignItems: 'start' }}>
            <RiskChart data={analysisRiskCurve} threshold={selectedScenario ? 0.5 : result.risk_threshold} />
            <HardwareMonitor />
          </div>
          {!selectedScenario && <LiveConsole />}

        </motion.div>
      )}
    </div>
  );
}