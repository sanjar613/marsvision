import { Camera, Maximize2 } from 'lucide-react';

export default function CameraGrid({ mainVideoUrl }) {
  const colors = { bg: '#0b0d10', primary: '#ff4757', text: '#e2e8f0', border: '#2d3748', panel: '#15181e' };

  const cameras = [
    { id: 'CAM_01', status: 'ACTIVE', url: mainVideoUrl, label: 'Main Intersection' },
    { id: 'CAM_02', status: 'STANDBY', url: null, label: 'Highway North' },
    { id: 'CAM_03', status: 'STANDBY', url: null, label: 'Pedestrian Crossing' },
    { id: 'CAM_04', status: 'OFFLINE', url: null, label: 'Bridge View' }
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px', marginTop: '24px' }}>
      {cameras.map((cam) => (
        <div key={cam.id} style={{ position: 'relative', backgroundColor: colors.bg, borderRadius: '12px', overflow: 'hidden', border: `1px solid ${cam.status === 'ACTIVE' ? colors.primary : colors.border}`, aspectRatio: '16/9' }}>
          
          {/* Camera status overlay */}
          <div style={{ position: 'absolute', top: '12px', left: '12px', zIndex: 10, display: 'flex', gap: '8px' }}>
            <div style={{ backgroundColor: 'rgba(0,0,0,0.7)', padding: '4px 8px', borderRadius: '4px', fontSize: '12px', fontFamily: 'monospace', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Camera size={12} color={cam.status === 'ACTIVE' ? colors.primary : '#8b949e'} />
              {cam.id}
            </div>
            {cam.status === 'ACTIVE' && (
              <div style={{ backgroundColor: 'rgba(255,71,87,0.2)', color: colors.primary, padding: '4px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold', border: `1px solid ${colors.primary}` }}>
                REC
              </div>
            )}
          </div>

          <div style={{ position: 'absolute', bottom: '12px', right: '12px', zIndex: 10 }}>
             <Maximize2 size={16} color="#fff" style={{ cursor: 'pointer', opacity: 0.7 }} />
          </div>

          {/* Video feed or no-signal state */}
          {cam.url ? (
            <video src={cam.url} autoPlay muted loop style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#8b949e', fontFamily: 'monospace' }}>
              <span style={{ fontSize: '24px', opacity: 0.2 }}>NO SIGNAL</span>
              <span style={{ marginTop: '8px' }}>{cam.label}</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}