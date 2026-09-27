import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { MapPin } from 'lucide-react';

export default function CityRadar() {
  const [angle, setAngle] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => setAngle(a => (a + 5) % 360), 50);
    return () => clearInterval(interval);
  }, []);

  const points = [
    { id: 1, x: '30%', y: '40%', status: 'safe' },
    { id: 2, x: '70%', y: '60%', status: 'alert' },
    { id: 3, x: '50%', y: '20%', status: 'safe' }
  ];

  return (
    <div style={{ 
      width: '100%', height: '250px', position: 'relative', borderRadius: '16px', overflow: 'hidden',
      background: 'radial-gradient(circle, rgba(59,130,246,0.1) 0%, rgba(11,13,16,1) 80%)',
      border: '1px solid rgba(59,130,246,0.2)', display: 'flex', justifyContent: 'center', alignItems: 'center'
    }}>
      {/* Radar grid */}
      <div style={{ position: 'absolute', width: '200px', height: '200px', borderRadius: '50%', border: '1px solid rgba(59,130,246,0.3)' }} />
      <div style={{ position: 'absolute', width: '100px', height: '100px', borderRadius: '50%', border: '1px solid rgba(59,130,246,0.3)' }} />
      <div style={{ position: 'absolute', width: '100%', height: '1px', backgroundColor: 'rgba(59,130,246,0.2)' }} />
      <div style={{ position: 'absolute', height: '100%', width: '1px', backgroundColor: 'rgba(59,130,246,0.2)' }} />

      {/* Scanning beam */}
      <div style={{
        position: 'absolute', width: '100px', height: '2px', backgroundColor: '#3b82f6',
        top: '50%', left: '50%', transformOrigin: '0% 50%',
        transform: `rotate(${angle}deg)`,
        boxShadow: '0 0 15px #3b82f6, 0 0 30px #3b82f6',
        background: 'linear-gradient(90deg, rgba(59,130,246,1) 0%, rgba(59,130,246,0) 100%)'
      }} />

      {/* Camera locations */}
      {points.map(p => (
        <motion.div key={p.id} 
          initial={{ scale: 0.8, opacity: 0.5 }} 
          animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }} 
          transition={{ repeat: Infinity, duration: p.status === 'alert' ? 1 : 3 }}
          style={{ position: 'absolute', left: p.x, top: p.y, color: p.status === 'alert' ? '#ff4757' : '#3b82f6' }}
        >
          <MapPin size={16} fill="currentColor" />
        </motion.div>
      ))}

      <div style={{ position: 'absolute', bottom: '12px', left: '12px', color: '#3b82f6', fontFamily: 'monospace', fontSize: '12px', fontWeight: 'bold' }}>
        RADAR SECURE LINK ACTV
      </div>
    </div>
  );
}