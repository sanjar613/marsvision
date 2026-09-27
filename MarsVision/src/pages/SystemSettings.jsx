import { Settings, Sliders, Cpu, Activity } from 'lucide-react';
import { Camera, ShieldCheck } from 'lucide-react';
import InsightMetrics from '../components/ui/InsightMetrics';
import { useAppStore } from '../store/useAppStore';

function GlassCard({ children, title, icon: Icon }) {
  return (
    <div style={{ 
      background: 'rgba(20, 19, 25, 0.72)', backdropFilter: 'blur(12px)',
      padding: '24px', borderRadius: '8px', border: '1px solid rgba(255, 71, 87, 0.2)',
      boxShadow: 'inset 0 0 20px rgba(255, 71, 87, 0.05)', flex: '1 1 300px'
    }}>
      <h3 style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#e2e8f0', marginTop: 0, borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '12px' }}>
        <Icon size={20} color="#ff4757" /> {title}
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginTop: '20px' }}>
        {children}
      </div>
    </div>
  );
}

export default function SystemSettings() {
  const { modelSettings, updateModelSettings } = useAppStore();
  const runtimeMetrics = [
    { label: 'Detector', value: 'YOLO11s', detail: 'Bundled model weights', icon: Activity, tone: 'cyan' },
    { label: 'Tracker', value: 'ByteTrack', detail: 'Road-user association', icon: Camera, tone: 'cyan' },
    { label: 'Risk alarm', value: '0.25', detail: 'Calibrated threshold', icon: ShieldCheck, tone: 'mars' },
    { label: 'Production device', value: 'CPU', detail: 'CPU-only PyTorch image', icon: Cpu, tone: 'amber' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ paddingBottom: '16px' }}>
        <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '10px', color: '#fff' }}>
          <Settings color="#ff4757" /> Inference configuration
        </h2>
        <p style={{ color: '#8b949e', marginTop: '8px' }}>Production pipeline reference and local threshold preview.</p>
      </div>

      <InsightMetrics items={runtimeMetrics} label="Production inference configuration" />

      <div className="settings-preview-notice" role="note">
        The sliders below update this browser preview only. They do not change the production server’s inference settings.
      </div>

      <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
        
        {/* Inference thresholds */}
        <GlassCard title="Local preview thresholds" icon={Sliders}>
          <div>
            <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: '#8b949e', fontSize: '14px' }}>
              <span>Confidence</span>
              <span style={{ color: '#ff4757', fontWeight: 'bold', textShadow: '0 0 8px rgba(255,71,87,0.5)' }}>
                {modelSettings.confidenceThreshold}
              </span>
            </label>
            <input 
              type="range" min="0.1" max="0.9" step="0.05" value={modelSettings.confidenceThreshold} 
              onChange={(e) => updateModelSettings({ confidenceThreshold: parseFloat(e.target.value) })}
              style={{ width: '100%', accentColor: '#ff4757', cursor: 'pointer' }}
            />
          </div>
          <div>
            <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: '#8b949e', fontSize: '14px' }}>
              <span>NMS IoU (overlap)</span>
              <span style={{ color: '#ff4757', fontWeight: 'bold', textShadow: '0 0 8px rgba(255,71,87,0.5)' }}>
                {modelSettings.iouThreshold}
              </span>
            </label>
            <input 
              type="range" min="0.1" max="0.9" step="0.05" value={modelSettings.iouThreshold} 
              onChange={(e) => updateModelSettings({ iouThreshold: parseFloat(e.target.value) })}
              style={{ width: '100%', accentColor: '#ff4757', cursor: 'pointer' }}
            />
          </div>
        </GlassCard>

        {/* Hardware acceleration */}
        <GlassCard title="Production runtime" icon={Cpu}>
          <div className="runtime-status-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <span style={{ color: '#e2e8f0' }}>Inference device</span>
            <span style={{ color: '#e4ad5a', fontFamily: 'monospace', fontWeight: 'bold', backgroundColor: 'rgba(228,173,90,0.1)', padding: '4px 8px', borderRadius: '4px' }}>CPU</span>
          </div>
          <div className="runtime-status-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <span style={{ color: '#e2e8f0' }}>GPU acceleration</span>
            <span style={{ color: '#9aa0aa', fontFamily: 'monospace', fontWeight: 'bold', backgroundColor: 'rgba(255,255,255,0.05)', padding: '4px 8px', borderRadius: '4px' }}>NOT CONFIGURED</span>
          </div>
        </GlassCard>

        {/* Module status */}
        <GlassCard title="Module status" icon={Activity}>
          {['YOLO11s object detector', 'ByteTrack object tracker', 'Calibrated risk estimator'].map((module, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '8px', height: '8px', backgroundColor: '#2ed573', borderRadius: '50%', boxShadow: '0 0 10px #2ed573' }} />
              <span style={{ color: '#8b949e', fontSize: '14px' }}>{module}</span>
            </div>
          ))}
        </GlassCard>

      </div>
    </div>
  );
}