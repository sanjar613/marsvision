import { useState } from 'react';
import { AlertCircle, Play, AlertTriangle } from 'lucide-react';
import { formatSeconds } from '../../utils/formatters';

export default function EventTimeline({ events, onSeek }) {
  const [activeFilter, setActiveFilter] = useState('ALL');
  
  if (!events || events.length === 0) return null;

  // Filter events by the selected category.
  const filteredEvents = events.filter(e => {
    if (activeFilter === 'ALL') return true;
    if (activeFilter === 'CRITICAL') return e.label === 'accident' || e.label === 'jaywalking';
    if (activeFilter === 'TRAFFIC') return e.label !== 'accident' && e.label !== 'jaywalking';
    return true;
  });

  return (
    <div style={{ flex: 1, backgroundColor: 'rgba(20, 19, 25, 0.78)', backdropFilter: 'blur(12px)', padding: '18px', borderRadius: '8px', border: '1px solid rgba(224,216,222,0.1)', maxHeight: '450px', display: 'flex', flexDirection: 'column' }}>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ margin: 0, color: '#8b949e', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '16px' }}>
          <AlertCircle size={18} color="#ff4757" /> Incident timeline
        </h3>
        
        {/* Event filters */}
        <div style={{ display: 'flex', gap: '8px', backgroundColor: 'rgba(0,0,0,0.3)', padding: '4px', borderRadius: '8px' }}>
          {['ALL', 'CRITICAL', 'TRAFFIC'].map(filter => (
            <button key={filter} onClick={() => setActiveFilter(filter)} style={{
              background: activeFilter === filter ? '#ff4757' : 'transparent',
              color: activeFilter === filter ? '#fff' : '#8b949e',
              border: 'none', padding: '4px 10px', borderRadius: '4px', fontSize: '10px', fontWeight: 'bold', cursor: 'pointer', transition: '0.2s', fontFamily: 'monospace'
            }}>
              {filter}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto', paddingRight: '8px' }}>
        {filteredEvents.map((e, i) => {
          const isCritical = e.label === 'accident' || e.label === 'jaywalking';
          
          return (
            <button key={`${e.label}-${e.start}-${i}`} type="button" aria-label={`Seek to ${formatSeconds(e.start)}: ${e.label}`} onClick={() => onSeek(e.start)} style={{
              width: '100%',
              padding: '13px', backgroundColor: 'rgba(7,8,12,0.48)', borderRadius: '6px', 
              borderLeft: `3px solid ${isCritical ? '#f25540' : '#65d0d9'}`, borderTop: '1px solid rgba(255,255,255,0.045)', borderRight: '1px solid rgba(255,255,255,0.045)', borderBottom: '1px solid rgba(255,255,255,0.045)',
              cursor: 'pointer', transition: 'all 0.2s ease', display: 'flex', justifyContent: 'space-between', alignItems: 'center', textAlign: 'left', fontFamily: 'inherit'
            }}
            onMouseOver={(ev) => ev.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.05)'}
            onMouseOut={(ev) => ev.currentTarget.style.backgroundColor = 'rgba(0,0,0,0.4)'}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <AlertTriangle size={14} color={isCritical ? '#f25540' : '#65d0d9'} />
                  <span style={{ color: isCritical ? '#f25540' : '#65d0d9', fontWeight: '800', fontFamily: 'monospace', fontSize: '13px', letterSpacing: '0' }}>
                    {e.label.toUpperCase()}
                  </span>
                </div>
                <div style={{ color: '#8b949e', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px', fontFamily: 'monospace' }}>
                  <span style={{ backgroundColor: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: '4px' }}>T: {formatSeconds(e.start)}</span>
                  —
                  <span style={{ backgroundColor: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: '4px' }}>T: {formatSeconds(e.end)}</span>
                </div>
              </div>
              <div style={{ backgroundColor: isCritical ? 'rgba(242,85,64,0.11)' : 'rgba(101,208,217,0.1)', padding: '9px', borderRadius: '6px', display: 'flex' }}>
                <Play size={15} color={isCritical ? '#f25540' : '#65d0d9'} />
              </div>
            </button>
          )
        })}
      </div>
    </div>
  );
}