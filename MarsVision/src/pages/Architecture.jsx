import { BookOpen, CheckCircle, XCircle, Activity, Clock, Target, Database, ArrowRightCircle } from 'lucide-react';
import InsightMetrics from '../components/ui/InsightMetrics';

const pipelineMetrics = [
  { label: 'Part A detector', value: 'YOLO11s', detail: 'Sparse-frame event detection', icon: BookOpen, tone: 'cyan' },
  { label: 'Part B tracker', value: 'ByteTrack', detail: 'Causal object identities', icon: Activity, tone: 'cyan' },
  { label: 'Risk horizon', value: '5.0 sec', detail: 'Forward collision estimate', icon: Clock, tone: 'mars' },
  { label: 'Calibrator inputs', value: '12 features', detail: 'Logistic risk model', icon: CheckCircle, tone: 'amber' },
];

function GlassPanel({ title, icon: Icon, children }) {
  return (
    <div style={{ background: 'rgba(20, 19, 25, 0.72)', backdropFilter: 'blur(12px)', padding: '24px', borderRadius: '12px', border: '1px solid rgba(224,216,222,0.09)' }}>
      <h3 style={{ margin: '0 0 16px 0', color: '#fff', fontSize: '20px', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '12px', display: 'flex', alignItems: 'center', gap: '10px' }}>
        {Icon && <Icon size={22} color="#65d0d9" />} {title}
      </h3>
      <div style={{ color: '#8b949e', lineHeight: '1.7', fontSize: '15px' }}>{children}</div>
    </div>
  );
}

export default function Architecture() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', paddingBottom: '40px' }}>
      
      {/* Header */}
      <div style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '16px' }}>
        <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '10px', color: '#fff', fontSize: '28px' }}>
          <Target color="#ff4757" size={32} /> Problem and approach
        </h2>
        <p style={{ color: '#8b949e', marginTop: '12px', fontSize: '16px', lineHeight: '1.6', maxWidth: '800px' }}>
          A fixed CCTV camera watches a signalised intersection in Tashkent. Our system does two jobs: event detection (Part A) and accident anticipation (Part B), processing video dynamically and seeing only the past.
        </p>
      </div>

      <InsightMetrics items={pipelineMetrics} label="System Pipeline Overview" />

      {/* Pipeline Image Placeholder */}
      <div style={{ borderRadius: '12px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)' }}>
        <img src="/pipeline.png" alt="Approach Pipeline" style={{ width: '100%', display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }} />
      </div>

      {/* Part A */}
      <GlassPanel title="Part A: Event detection" icon={BookOpen}>
        <p style={{ marginTop: 0 }}>4K video is expensive to read. Decoding every frame on a 4-core CPU runs at only about 0.9× real time. Therefore, we sample keyframes (2 fps) and run them through <strong>YOLO11s (COCO)</strong> to find vehicles and pedestrians.</p>
        
        <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap', marginTop: '16px' }}>
          <div style={{ flex: '1 1 300px' }}>
            <h4 style={{ color: '#fff', marginBottom: '8px' }}>Scene Map & Rules</h4>
            <ul style={{ paddingLeft: '20px', margin: 0 }}>
              <li style={{ marginBottom: '8px' }}><strong>stopped_vehicle:</strong> A vehicle stationary for ≥12s. We exclude red-light queues (vehicles must stand for 150s to trigger) and buses at the bus stop.</li>
              <li><strong>jaywalking:</strong> A person on the road outside zebra crossings. People waiting at the kerb or static workers/poles are ignored.</li>
            </ul>
          </div>
          <div style={{ flex: '1 1 300px', borderRadius: '8px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)' }}>
             <img src="/scene_C3896.jpg" alt="Scene Map" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          </div>
        </div>
      </GlassPanel>

      {/* Part B */}
      <GlassPanel title="Part B: Accident anticipation" icon={Activity}>
        <p style={{ marginTop: 0 }}>Every 4th frame goes through YOLO11s and <strong>ByteTrack</strong> to follow road users over time. For every pair of nearby road users we measure:</p>
        <ul style={{ paddingLeft: '20px', color: '#e2e8f0', marginBottom: '16px' }}>
          <li>Time-to-collision and closing speed.</li>
          <li>The braking needed to avoid a crash, sudden swerving.</li>
          <li>Driving against the usual lane direction.</li>
        </ul>
        <p style={{ margin: 0 }}>A logistic-regression model (trained on the public ACCIDENT dataset) turns these 12 features into a probability. We apply smoothing and an alarm rule to output at most one alarm per event, with no alarms in the first 3 seconds.</p>
      </GlassPanel>

      {/* Data & Models */}
      <GlassPanel title="Data and models" icon={Database}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', color: '#e2e8f0', fontSize: '14px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}>
                <th style={{ padding: '12px 8px' }}>What</th>
                <th style={{ padding: '12px 8px' }}>Used for</th>
                <th style={{ padding: '12px 8px' }}>Licence</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '12px 8px' }}>Organizer sample videos</td>
                <td style={{ padding: '12px 8px' }}>Scene map, tests, final results</td>
                <td style={{ padding: '12px 8px', color: '#65d0d9' }}>Hackathon data</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '12px 8px' }}>ACCIDENT benchmark</td>
                <td style={{ padding: '12px 8px' }}>Part B training and testing</td>
                <td style={{ padding: '12px 8px', color: '#65d0d9' }}>CC BY-NC-SA 4.0</td>
              </tr>
              <tr>
                <td style={{ padding: '12px 8px' }}>YOLO11s (Ultralytics)</td>
                <td style={{ padding: '12px 8px' }}>Object Detection</td>
                <td style={{ padding: '12px 8px', color: '#65d0d9' }}>AGPL-3.0</td>
              </tr>
            </tbody>
          </table>
        </div>
      </GlassPanel>

      {/* Execution Report Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 300px), 1fr))', gap: '16px' }}>
        
        <div style={{ background: 'rgba(46, 213, 115, 0.05)', padding: '24px', borderRadius: '12px', border: '1px solid rgba(46, 213, 115, 0.16)' }}>
          <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#2ed573', margin: '0 0 16px 0', fontSize: '18px' }}>
            <CheckCircle size={20} /> What worked
          </h4>
          <ul style={{ margin: 0, paddingLeft: '20px', color: '#8b949e', fontSize: '14px', lineHeight: '1.6' }}>
            <li style={{ marginBottom: '8px' }}>Reading only keyframes made Part A cheap (runs at ~0.6× video length).</li>
            <li style={{ marginBottom: '8px' }}>The handcrafted scene map removed most false alarms (verified manually).</li>
            <li>Ablation analysis caught a fake 0.47 score (caused by luck/warm-up bias) before shipping.</li>
          </ul>
        </div>
        
        <div style={{ background: 'rgba(242,85,64,0.05)', padding: '24px', borderRadius: '12px', border: '1px solid rgba(242,85,64,0.18)' }}>
          <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#ff4757', margin: '0 0 16px 0', fontSize: '18px' }}>
            <XCircle size={20} /> What didn't work
          </h4>
          <ul style={{ margin: 0, paddingLeft: '20px', color: '#8b949e', fontSize: '14px', lineHeight: '1.6' }}>
            <li style={{ marginBottom: '8px' }}>GPU video decoding (NVDEC) failed on the provided heavily compressed 4K files.</li>
            <li style={{ marginBottom: '8px' }}>Geometric risk features proved weak (AUC 0.60), and the calibrator partly learns scene shortcuts.</li>
            <li>Lack of official labels for sample videos prevented calculating a real F1 score for Part A.</li>
          </ul>
        </div>

        <div style={{ background: 'rgba(101, 208, 217, 0.05)', padding: '24px', borderRadius: '12px', border: '1px solid rgba(101, 208, 217, 0.18)' }}>
          <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#65d0d9', margin: '0 0 16px 0', fontSize: '18px' }}>
            <ArrowRightCircle size={20} /> What we'd do next
          </h4>
          <ul style={{ margin: 0, paddingLeft: '20px', color: '#8b949e', fontSize: '14px', lineHeight: '1.6' }}>
            <li style={{ marginBottom: '8px' }}>Label the sample videos to create a real dev set and tune rules directly against it.</li>
            <li style={{ marginBottom: '8px' }}>Add new events: `wrong_way`, `red_light`, and `failure_to_yield`.</li>
            <li>Fine-tune a dedicated video-action model on accident datasets specifically for Part B.</li>
          </ul>
        </div>

      </div>
    </div>
  );
}