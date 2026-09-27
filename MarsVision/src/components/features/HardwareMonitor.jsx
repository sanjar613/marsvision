import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Activity, Cpu, Gauge, Thermometer } from 'lucide-react';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const palette = {
  panel: 'rgba(20, 19, 25, 0.82)',
  border: 'rgba(255, 255, 255, 0.08)',
  muted: '#8b949e',
  text: '#e2e8f0',
  danger: '#ff4757',
  info: '#65d0d9',
  green: '#e4ad5a',
};

const initialSeries = Array.from({ length: 18 }, (_, index) => ({
  time: `-${(17 - index) * 3}s`,
  vram: 4.5 + (index % 6) * 0.16,
  latency: 2.08 + (index % 5) * 0.035,
}));

function MetricRing({ label, value, unit, percent, color, icon: Icon }) {
  const circumference = 2 * Math.PI * 19;
  const offset = circumference * (1 - Math.min(percent, 100) / 100);

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '11px', minWidth: '130px', flex: '1 1 130px' }}>
      <div style={{ position: 'relative', width: '48px', height: '48px', flex: '0 0 48px' }}>
        <svg viewBox="0 0 48 48" width="48" height="48" role="img" aria-label={`${label} ${value}${unit}`}>
          <circle cx="24" cy="24" r="19" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="4" />
          <circle cx="24" cy="24" r="19" fill="none" stroke={color} strokeWidth="4" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={offset} transform="rotate(-90 24 24)" />
        </svg>
        <Icon size={15} color={color} style={{ position: 'absolute', top: '16px', left: '16px' }} />
      </div>
      <div>
        <div style={{ color: palette.muted, fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '10px', letterSpacing: '0.08em', textTransform: 'uppercase' }}>{label}</div>
        <div style={{ color: palette.text, fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '18px', fontWeight: 700, lineHeight: 1.25 }}>{value}<span style={{ color: palette.muted, fontSize: '11px', marginLeft: '3px' }}>{unit}</span></div>
      </div>
    </div>
  );
}

export default function HardwareMonitor() {
  const [series, setSeries] = useState(initialSeries);
  const [metrics, setMetrics] = useState({ cpu: 38, temperature: 67, fps: 24 });
  const valuesRef = useRef({ vram: 5.06, latency: 2.18, cpu: 38, temperature: 67, fps: 24 });

  useEffect(() => {
    const timer = window.setInterval(() => {
      const values = valuesRef.current;
      const sample = {
        vram: Math.min(5.95, Math.max(4.05, values.vram + (Math.random() - 0.5) * 0.22)),
        latency: Math.min(2.38, Math.max(2.02, values.latency + (Math.random() - 0.5) * 0.055)),
        cpu: Math.round(Math.min(76, Math.max(24, values.cpu + (Math.random() - 0.5) * 8))),
        temperature: Math.round(Math.min(78, Math.max(58, values.temperature + (Math.random() - 0.5) * 3))),
        fps: Math.round(Math.min(30, Math.max(20, values.fps + (Math.random() - 0.5) * 3))),
      };
      valuesRef.current = sample;
      setMetrics({ cpu: sample.cpu, temperature: sample.temperature, fps: sample.fps });
      setSeries((previous) => [...previous.slice(1), { time: new Date().toLocaleTimeString(), vram: sample.vram, latency: sample.latency }]);
    }, 1800);

    return () => window.clearInterval(timer);
  }, []);

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      aria-label="Hardware and inference telemetry"
      style={{ minWidth: 0, padding: '18px', background: palette.panel, border: `1px solid ${palette.border}`, borderRadius: '8px', backdropFilter: 'blur(12px)' }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', flexWrap: 'wrap', marginBottom: '18px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: palette.text, fontWeight: 700, fontSize: '14px' }}>
            <Activity size={17} color={palette.info} /> Inference telemetry
          </div>
          <div style={{ marginTop: '5px', color: palette.muted, fontSize: '11px', fontFamily: 'ui-monospace, Consolas, monospace' }}>SYNTHETIC TELEMETRY / DEMONSTRATION VALUES</div>
        </div>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '7px', padding: '5px 8px', border: '1px solid rgba(53,211,154,0.24)', borderRadius: '4px', color: palette.green, fontSize: '10px', fontFamily: 'ui-monospace, Consolas, monospace', letterSpacing: '0.08em' }}>
          <motion.span animate={{ opacity: [1, 0.35, 1] }} transition={{ duration: 1.4, repeat: Infinity }} style={{ width: '6px', height: '6px', borderRadius: '50%', background: palette.green }} /> SIMULATED
        </div>
      </div>

      <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', padding: '14px 0 18px', borderTop: `1px solid ${palette.border}`, borderBottom: `1px solid ${palette.border}` }}>
        <MetricRing label="CPU load" value={metrics.cpu} unit="%" percent={metrics.cpu} color={palette.info} icon={Cpu} />
        <MetricRing label="GPU temp" value={metrics.temperature} unit="°C" percent={(metrics.temperature / 95) * 100} color={palette.danger} icon={Thermometer} />
        <MetricRing label="Throughput" value={metrics.fps} unit="FPS" percent={(metrics.fps / 30) * 100} color={palette.green} icon={Gauge} />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: '10px', margin: '16px 0 4px' }}>
        <span style={{ color: palette.muted, fontSize: '11px', fontFamily: 'ui-monospace, Consolas, monospace' }}>GPU VRAM / INFERENCE RUNTIME</span>
        <span style={{ color: palette.text, fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '11px' }}>2.2× target</span>
      </div>
      <div style={{ width: '100%', height: '150px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={series} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
            <CartesianGrid stroke="rgba(255,255,255,0.07)" strokeDasharray="3 5" vertical={false} />
            <XAxis dataKey="time" tick={{ fill: palette.muted, fontSize: 9 }} axisLine={false} tickLine={false} minTickGap={24} />
            <YAxis yAxisId="vram" domain={[4, 6]} ticks={[4, 5, 6]} tick={{ fill: palette.info, fontSize: 9 }} axisLine={false} tickLine={false} width={28} />
            <YAxis yAxisId="latency" orientation="right" domain={[2, 2.4]} ticks={[2, 2.2, 2.4]} tick={{ fill: palette.danger, fontSize: 9 }} axisLine={false} tickLine={false} width={30} />
            <Tooltip
              contentStyle={{ background: '#0b0d10', border: `1px solid ${palette.border}`, borderRadius: '5px', color: palette.text, fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '11px' }}
              formatter={(value, name) => [name === 'VRAM' ? `${Number(value).toFixed(2)} GB` : `${Number(value).toFixed(2)}×`, name]}
            />
            <Line yAxisId="vram" type="monotone" dataKey="vram" name="VRAM" stroke={palette.info} strokeWidth={2} dot={false} isAnimationActive={false} />
            <Line yAxisId="latency" type="monotone" dataKey="latency" name="Runtime" stroke={palette.danger} strokeWidth={2} dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div style={{ display: 'flex', gap: '16px', justifyContent: 'flex-end', color: palette.muted, fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '10px' }}>
        <span><i style={{ display: 'inline-block', width: '7px', height: '7px', marginRight: '6px', borderRadius: '50%', background: palette.info }} />VRAM (GB)</span>
        <span><i style={{ display: 'inline-block', width: '7px', height: '7px', marginRight: '6px', borderRadius: '50%', background: palette.danger }} />Runtime (× realtime)</span>
      </div>
    </motion.section>
  );
}
