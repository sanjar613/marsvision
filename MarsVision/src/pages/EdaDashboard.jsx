import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart, Line } from 'recharts';
import { Activity, BarChart2, Clock, ShieldAlert } from 'lucide-react';
import InsightMetrics from '../components/ui/InsightMetrics';

export default function EdaDashboard() {
  const colors = { bg: '#090a0e', panel: '#14151b', primary: '#f25540', text: '#e2e8f0', border: '#2b2b33', secondary: '#65d0d9' };

  // Runtime data from website_content.md
  const runtimeData = [
    { video: 'C3896 (340s)', partA: 0.65, partB: 1.57, total: 2.22 },
    { video: 'C3897 (318s)', partA: 0.63, partB: 1.56, total: 2.19 },
    { video: 'C3905 (128s)', partA: 0.53, partB: 1.51, total: 2.04 }
  ];

  const eventsData = [
    { video: 'C3896', stopped: 2, jaywalking: 18 },
    { video: 'C3897', stopped: 3, jaywalking: 17 },
    { video: 'C3905', stopped: 1, jaywalking: 11 }
  ];

  // Part B ablation data
  const ablationData = [
    { model: 'A. Hand formula', score: 0.102, fa_min: 3.29 },
    { model: 'C. No overlap + warm-up', score: 0.027, fa_min: 2.35 },
    { model: 'D. Balanced (Artefact)', score: 0.467, fa_min: 0.47 },
    { model: 'E. Shipped Calibrator', score: 0.039, fa_min: 0.00 }
  ];

  const averageRuntime = runtimeData.reduce((total, sample) => total + sample.total, 0) / runtimeData.length;
  const shippedCalibrator = ablationData.find((model) => model.model === 'E. Shipped Calibrator');
  const bestScore = Math.max(...ablationData.map((model) => model.score));
  const metrics = [
    { label: 'Mean runtime', value: `${averageRuntime.toFixed(2)}×`, detail: 'Across 3 sample clips', icon: Clock, tone: 'cyan' },
    { label: 'Runtime budget', value: '3.00×', detail: `${(3 - averageRuntime).toFixed(2)}× mean headroom`, icon: Activity, tone: 'amber' },
    { label: 'Top ablation score', value: bestScore.toFixed(3), detail: 'Model D · artefact, not shipped', icon: BarChart2, tone: 'mars' },
    { label: 'Shipped false alarms', value: `${shippedCalibrator.fa_min.toFixed(2)}`, detail: 'Per minute on evaluation set', icon: ShieldAlert, tone: 'cyan' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: `1px solid ${colors.border}`, paddingBottom: '16px' }}>
        <div>
          <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '10px' }}><BarChart2 color={colors.primary} /> EDA & Results</h2>
          <p style={{ color: '#8b949e', marginTop: '8px', marginBottom: 0 }}>Official Kaggle T4 metrics and ablation results.</p>
        </div>
      </div>

      <InsightMetrics items={metrics} label="Evaluation summary" />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 400px), 1fr))', gap: '24px' }}>
        
        {/* Runtime chart */}
        <div style={{ backgroundColor: 'rgba(20, 19, 25, 0.78)', padding: '20px', borderRadius: '8px', border: `1px solid ${colors.border}` }}>
          <h3 style={{ marginTop: 0, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '16px' }}>
            <Clock size={18} color={colors.secondary} /> Runtime per sample video (Limit: 3.0x)
          </h3>
          <div style={{ height: '250px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={runtimeData} layout="vertical" margin={{ left: 20, right: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.border} horizontal={false} />
                <XAxis type="number" domain={[0, 3]} stroke="#8b949e" />
                <YAxis dataKey="video" type="category" stroke="#8b949e" width={100} />
                <Tooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} contentStyle={{ backgroundColor: colors.bg, borderColor: colors.border }} />
                <Bar dataKey="partA" stackId="a" fill="#65d0d9" name="Part A (Events)" />
                <Bar dataKey="partB" stackId="a" fill="#f25540" name="Part B (Risk)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Part B ablation chart */}
        <div style={{ backgroundColor: 'rgba(20, 19, 25, 0.78)', padding: '20px', borderRadius: '8px', border: `1px solid ${colors.border}` }}>
          <h3 style={{ marginTop: 0, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '16px' }}>
            <ShieldAlert size={18} color={colors.primary} /> Part B Ablation: Score vs False Alarms
          </h3>
          <div style={{ height: '250px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={ablationData} margin={{ top: 20, right: 20, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.border} vertical={false} />
                <XAxis dataKey="model" stroke="#8b949e" tick={{fontSize: 10}} />
                <YAxis yAxisId="left" stroke="#8b949e" />
                <YAxis yAxisId="right" orientation="right" stroke="#ff4757" />
                <Tooltip contentStyle={{ backgroundColor: colors.bg, borderColor: colors.border }} />
                <Bar yAxisId="left" dataKey="score" fill="#65d0d9" name="Score B" barSize={30} />
                <Line yAxisId="right" type="monotone" dataKey="fa_min" stroke="#f25540" strokeWidth={2} name="False Alarms / min" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <p style={{ fontSize: '12px', color: '#8b949e', marginTop: '12px', textAlign: 'center' }}>Model D has the highest score (0.467), but produces false alarms. Model E (0.00 false alarms) was selected for submission.</p>
        </div>

        <div style={{ backgroundColor: 'rgba(20, 19, 25, 0.78)', padding: '20px', borderRadius: '8px', border: `1px solid ${colors.border}` }}>
          <h3 style={{ marginTop: 0, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '16px' }}>
            <Activity size={18} color={colors.secondary} /> Detected events per sample
          </h3>
          <div style={{ height: '250px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={eventsData}>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                <XAxis dataKey="video" stroke="#8b949e" />
                <YAxis stroke="#8b949e" allowDecimals={false} />
                <Tooltip contentStyle={{ backgroundColor: colors.bg, borderColor: colors.border }} />
                <Bar dataKey="stopped" stackId="events" fill="#e4ad5a" name="Stopped vehicles" />
                <Bar dataKey="jaywalking" stackId="events" fill="#65d0d9" name="Jaywalking" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}