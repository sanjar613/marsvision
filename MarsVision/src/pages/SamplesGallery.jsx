import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Activity, AlertTriangle, ArrowUpRight, Play, Radio } from 'lucide-react';
import InsightMetrics from '../components/ui/InsightMetrics';
import { demoScenarios } from '../utils/demoScenarios';

export default function SamplesGallery() {
  const navigate = useNavigate();
  const colors = { panel: 'rgba(20,19,25,0.78)', primary: '#f25540', text: '#e2e8f0', border: 'rgba(224,216,222,0.1)', muted: '#8b949e' };
  const sampleEventCount = demoScenarios.reduce((total, scenario) => total + scenario.events.length, 0);
  const peakRisk = Math.max(...demoScenarios.flatMap((scenario) => scenario.risk_curve.map((point) => point[1])));
  const metrics = [
    { label: 'Scenario clips', value: demoScenarios.length, detail: 'Fixed junction previews', icon: Radio, tone: 'cyan' },
    { label: 'Illustrative events', value: sampleEventCount, detail: 'Across all scenarios', icon: Activity, tone: 'amber' },
    { label: 'Peak sample risk', value: peakRisk.toFixed(2), detail: 'Turning conflict preview', icon: AlertTriangle, tone: 'mars' },
    { label: 'Replay duration', value: `${demoScenarios[0].duration}s`, detail: 'Per sample clip', icon: Play, tone: 'cyan' },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} style={{ display: 'flex', flexDirection: 'column', gap: '20px', color: colors.text }}>
      <header style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap', paddingBottom: '16px', borderBottom: `1px solid ${colors.border}` }}>
        <div>
          <div style={{ color: colors.muted, fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '10px', letterSpacing: '0.1em' }}>DEMO LIBRARY / SCENARIO ANALYSIS</div>
          <h2 style={{ margin: '8px 0 5px', color: colors.text }}>Traffic scenarios</h2>
          <p style={{ color: colors.muted, fontSize: '12px' }}>Launch a deterministic preview of detection and risk analysis without uploading a clip.</p>
        </div>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '6px 8px', color: '#f6b84a', background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.24)', borderRadius: '4px', fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '9px' }}><Radio size={12} /> SYNTHETIC DATA</span>
      </header>

      <InsightMetrics items={metrics} label="Scenario library summary" />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))', gap: '14px' }}>
        {demoScenarios.map((scenario, index) => {
          const peakRisk = Math.max(...scenario.risk_curve.map((point) => point[1]));
          return (
            <motion.article key={scenario.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.32, delay: index * 0.07 }} whileHover={{ y: -3 }} style={{ minWidth: 0, overflow: 'hidden', background: colors.panel, border: `1px solid ${colors.border}`, borderRadius: '7px' }}>
              <div style={{ position: 'relative', aspectRatio: '16 / 8', overflow: 'hidden', background: 'linear-gradient(145deg, #111a22, #080b10)' }}>
                <svg viewBox="0 0 640 320" role="img" aria-label={`Schematic preview for ${scenario.title}`} style={{ width: '100%', height: '100%' }}>
                  <path d="M0 94H640V226H0ZM250 0H390V320H250Z" fill="#1b252e" />
                  <path d="M0 160H250M390 160H640M320 0V94M320 226V320" stroke="rgba(226,232,240,0.34)" strokeWidth="2" strokeDasharray="14 11" />
                  <path d="M0 94H640M0 226H640M250 0V320M390 0V320" stroke="rgba(101,208,217,0.38)" strokeWidth="1" />
                  {Array.from({ length: 7 }, (_, mark) => <rect key={mark} x={258 + mark * 18} y="75" width="9" height="17" fill="rgba(226,232,240,0.72)" />)}
                  <motion.circle cx={280 + index * 34} cy={142 + index * 18} r="8" fill={index === 1 ? '#f59e0b' : colors.primary} animate={{ opacity: [0.55, 1, 0.55], scale: [0.85, 1.16, 0.85] }} transition={{ duration: 2.2, repeat: Infinity }} />
                  <circle cx={280 + index * 34} cy={142 + index * 18} r="2.5" fill="#fff" />
                </svg>
                <span style={{ position: 'absolute', top: '10px', left: '11px', padding: '4px 6px', color: '#83dbe0', background: 'rgba(5,8,12,0.76)', border: '1px solid rgba(101,208,217,0.25)', borderRadius: '3px', fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '9px' }}>CAMERA SECTOR 0{index + 1}</span>
                <span style={{ position: 'absolute', right: '10px', bottom: '10px', padding: '4px 6px', color: colors.muted, background: 'rgba(5,8,12,0.76)', borderRadius: '3px', fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '9px' }}>{scenario.duration}s</span>
              </div>
              <div style={{ padding: '15px' }}>
                <div style={{ color: '#65d0d9', fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '9px', letterSpacing: '0' }}>{scenario.location}</div>
                <h3 style={{ margin: '7px 0', color: colors.text, fontSize: '15px' }}>{scenario.title}</h3>
                <p style={{ minHeight: '36px', color: colors.muted, fontSize: '11px', lineHeight: 1.55 }}>{scenario.summary}</p>
                <div style={{ display: 'flex', gap: '18px', margin: '13px 0', padding: '10px 0', borderTop: `1px solid ${colors.border}`, borderBottom: `1px solid ${colors.border}` }}>
                  <div><div style={{ color: colors.muted, fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '8px' }}>EVENTS</div><div style={{ marginTop: '4px', color: colors.text, fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '13px' }}>{scenario.events.length}</div></div>
                  <div><div style={{ color: colors.muted, fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '8px' }}>PEAK RISK</div><div style={{ marginTop: '4px', color: colors.primary, fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '13px' }}>{peakRisk.toFixed(2)}</div></div>
                </div>
                <button type="button" onClick={() => navigate('/', { state: { scenarioId: scenario.id } })} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', minHeight: '38px', padding: '0 10px', color: colors.text, background: 'rgba(101,208,217,0.08)', border: '1px solid rgba(101,208,217,0.24)', borderRadius: '5px', cursor: 'pointer', fontSize: '11px', fontWeight: 700 }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '7px' }}><Play size={13} /> Open scenario</span><ArrowUpRight size={14} color="#83dbe0" />
                </button>
              </div>
            </motion.article>
          );
        })}
      </div>

      <div style={{ padding: '12px 14px', color: '#8b949e', background: 'rgba(245,158,11,0.05)', border: '1px solid rgba(245,158,11,0.16)', borderRadius: '5px', fontSize: '11px', lineHeight: 1.55 }}>
        These scenarios illustrate the interface using fixed sample values. They do not process footage or represent detector results.
      </div>
    </motion.div>
  );
}