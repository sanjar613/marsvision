import { Thermometer, Wind, CloudRain, Eye } from 'lucide-react';

export default function EnvironmentSensor() {
  const metrics = [
    { label: 'Light level', value: '420 lx', status: 'LOW_VISIBILITY', icon: Eye, color: '#f59e0b' },
    { label: 'Road surface moisture', value: '87%', status: 'WET_ROAD', icon: CloudRain, color: '#3b82f6' },
    { label: 'Temperature', value: '-2°C', status: 'ICE_WARNING', icon: Thermometer, color: '#00d2d3' },
    { label: 'Wind speed', value: '12 m/s', status: 'NORMAL', icon: Wind, color: '#2ed573' }
  ];

  return (
    <div style={{ backgroundColor: 'rgba(20, 22, 30, 0.4)', backdropFilter: 'blur(12px)', padding: '24px', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
      <h3 style={{ marginTop: 0, color: '#8b949e', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '16px', marginBottom: '20px' }}>
        <Thermometer size={18} color="#3b82f6" /> Environmental telemetry (CV impact)
      </h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px' }}>
        {metrics.map((m, i) => (
          <div key={i} style={{ backgroundColor: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '12px', borderLeft: `3px solid ${m.color}`, display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#8b949e', fontSize: '12px' }}>
              <m.icon size={14} color={m.color} /> {m.label}
            </div>
            <div style={{ color: '#e2e8f0', fontSize: '20px', fontWeight: 'bold', fontFamily: 'monospace' }}>
              {m.value}
            </div>
            <div style={{ color: m.color, fontSize: '10px', fontWeight: 'bold', letterSpacing: '1px', backgroundColor: `${m.color}20`, padding: '2px 6px', borderRadius: '4px', alignSelf: 'flex-start' }}>
              {m.status}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}