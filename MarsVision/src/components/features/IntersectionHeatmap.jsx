import { motion } from 'framer-motion';
import { Crosshair, MapPin } from 'lucide-react';

const incidents = [
  { id: 'J-04', x: 45, y: 35, kind: 'JAYWALKING', intensity: 0.92, color: '#ff4757' },
  { id: 'J-07', x: 57, y: 66, kind: 'JAYWALKING', intensity: 0.76, color: '#ff4757' },
  { id: 'S-02', x: 73, y: 42, kind: 'STOPPED VEHICLE', intensity: 0.68, color: '#f59e0b' },
  { id: 'S-05', x: 29, y: 72, kind: 'STOPPED VEHICLE', intensity: 0.54, color: '#f59e0b' },
];

const palette = {
  panel: 'rgba(20, 22, 30, 0.72)',
  border: 'rgba(255, 255, 255, 0.08)',
  muted: '#8b949e',
  text: '#e2e8f0',
  info: '#65d0d9',
};

export default function IntersectionHeatmap() {
  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.42 }}
      aria-label="Intersection incident heatmap"
      style={{ minWidth: 0, padding: '18px', background: palette.panel, border: `1px solid ${palette.border}`, borderRadius: '8px', backdropFilter: 'blur(12px)' }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '14px', marginBottom: '14px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: palette.text, fontWeight: 700, fontSize: '14px' }}>
            <Crosshair size={17} color={palette.info} /> Intersection activity map
          </div>
          <div style={{ marginTop: '5px', color: palette.muted, fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '10px' }}>CAM_01 / CENTRAL JUNCTION / LAST 30 MIN</div>
        </div>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: palette.info, fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '10px' }}>
          <MapPin size={13} /> SECTOR 04
        </span>
      </div>

      <div style={{ position: 'relative', overflow: 'hidden', border: `1px solid ${palette.border}`, borderRadius: '6px', background: '#090d12', aspectRatio: '16 / 9' }}>
        <div style={{ position: 'absolute', inset: 0, backgroundImage: 'linear-gradient(rgba(101,208,217,0.075) 1px, transparent 1px), linear-gradient(90deg, rgba(101,208,217,0.075) 1px, transparent 1px)', backgroundSize: '28px 28px', pointerEvents: 'none', zIndex: 1 }} />
        <svg viewBox="0 0 640 360" role="img" aria-label="Schematic four-way intersection with incident clusters" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
          <defs>
            <pattern id="roadGrain" width="12" height="12" patternUnits="userSpaceOnUse">
              <path d="M0 12L12 0" stroke="rgba(255,255,255,0.018)" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="640" height="360" fill="#101820" />
          <rect x="0" y="0" width="640" height="360" fill="url(#roadGrain)" />
          <path d="M0 110H640V250H0Z" fill="#1b232b" />
          <path d="M235 0H405V360H235Z" fill="#1b232b" />
          <path d="M0 110H640M0 250H640M235 0V360M405 0V360" fill="none" stroke="rgba(148,163,184,0.22)" strokeWidth="2" />
          <path d="M0 180H235M405 180H640M320 0V110M320 250V360" fill="none" stroke="rgba(226,232,240,0.34)" strokeWidth="2" strokeDasharray="15 12" />
          <g fill="rgba(226,232,240,0.74)">
            {Array.from({ length: 8 }, (_, index) => <rect key={`north-${index}`} x={244 + index * 20} y="91" width="10" height="18" rx="1" />)}
            {Array.from({ length: 8 }, (_, index) => <rect key={`south-${index}`} x={244 + index * 20} y="251" width="10" height="18" rx="1" />)}
            {Array.from({ length: 6 }, (_, index) => <rect key={`west-${index}`} x="216" y={119 + index * 20} width="18" height="10" rx="1" />)}
            {Array.from({ length: 6 }, (_, index) => <rect key={`east-${index}`} x="406" y={119 + index * 20} width="18" height="10" rx="1" />)}
          </g>
          <path d="M20 32H86M20 32V86M620 32H554M620 32V86M20 328H86M20 328V274M620 328H554M620 328V274" fill="none" stroke="rgba(101,208,217,0.7)" strokeWidth="2" />

          {incidents.map((incident, index) => {
            const cx = incident.x * 6.4;
            const cy = incident.y * 3.6;
            return (
              <g key={incident.id}>
                <title>{`${incident.kind} ${incident.id}, intensity ${Math.round(incident.intensity * 100)} percent`}</title>
                <motion.circle
                  cx={cx}
                  cy={cy}
                  r="8"
                  fill="none"
                  stroke={incident.color}
                  strokeWidth="2"
                  initial={{ r: 8, opacity: 0.8 }}
                  animate={{ r: [8, 22, 8], opacity: [0.85, 0, 0.85] }}
                  transition={{ duration: 2.2, repeat: Infinity, delay: index * 0.35, ease: 'easeOut' }}
                />
                <circle cx={cx} cy={cy} r="5" fill={incident.color} opacity={incident.intensity} />
                <circle cx={cx} cy={cy} r="2" fill="#fff" />
              </g>
            );
          })}
          <text x="18" y="22" fill="rgba(148,163,184,0.82)" fontSize="10" fontFamily="monospace">N ↑</text>
          <text x="536" y="342" fill="rgba(148,163,184,0.82)" fontSize="9" fontFamily="monospace">SCALE 20m</text>
        </svg>
        <div style={{ position: 'absolute', top: '9px', right: '10px', zIndex: 2, padding: '4px 6px', color: '#35d39a', background: 'rgba(5,8,12,0.76)', border: '1px solid rgba(53,211,154,0.22)', borderRadius: '3px', fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '9px' }}>MAP FEED: SIMULATED</div>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '14px', marginTop: '13px' }}>
        {[
          { label: 'Jaywalking', color: '#ff4757' },
          { label: 'Stopped vehicle', color: '#f59e0b' },
        ].map((item) => (
          <span key={item.label} style={{ display: 'inline-flex', alignItems: 'center', gap: '7px', color: palette.muted, fontSize: '11px' }}>
            <i style={{ width: '8px', height: '8px', borderRadius: '50%', background: item.color, boxShadow: `0 0 9px ${item.color}` }} />{item.label}
          </span>
        ))}
        <span style={{ marginLeft: 'auto', color: palette.text, fontFamily: 'ui-monospace, Consolas, monospace', fontSize: '10px' }}>{incidents.length} CLUSTERS</span>
      </div>
    </motion.section>
  );
}
