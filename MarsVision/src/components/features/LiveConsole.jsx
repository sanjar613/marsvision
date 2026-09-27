import { useEffect, useRef } from 'react';
import { Terminal } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

export default function LiveConsole() {
  const { systemLogs } = useAppStore();
  const consoleEndRef = useRef(null);

  // Keep the newest log entry in view.
  useEffect(() => {
    if (consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [systemLogs]);

  const getLogColor = (type) => {
    switch(type) {
      case 'error': return '#ff4757';
      case 'warning': return '#f59e0b';
      case 'success': return '#2ed573';
      case 'cv_data': return '#3b82f6';
      default: return '#8b949e';
    }
  };

  return (
    <div style={{ 
      backgroundColor: '#050508', 
      borderRadius: '16px', 
      border: '1px solid rgba(59,130,246,0.3)',
      display: 'flex', 
      flexDirection: 'column', 
      height: '300px',
      overflow: 'hidden',
      boxShadow: 'inset 0 0 20px rgba(0,0,0,0.8)'
    }}>
      {/* Console header */}
      <div style={{ 
        backgroundColor: 'rgba(20,22,30,0.8)', 
        padding: '10px 16px', 
        borderBottom: '1px solid rgba(59,130,246,0.2)',
        display: 'flex', 
        alignItems: 'center', 
        gap: '8px' 
      }}>
        <Terminal size={16} color="#3b82f6" />
        <span style={{ color: '#e2e8f0', fontSize: '12px', fontFamily: 'monospace', fontWeight: 'bold' }}>
          MARS_VISION // RAW INFERENCE STREAM
        </span>
      </div>

      {/* Log output */}
      <div style={{ 
        padding: '16px', 
        overflowY: 'auto', 
        flex: 1,
        fontFamily: '"Fira Code", monospace',
        fontSize: '12px',
        lineHeight: '1.6'
      }}>
        {systemLogs.map((log, index) => (
          <div key={index} style={{ marginBottom: '4px', display: 'flex', gap: '12px' }}>
            <span style={{ color: '#475569', minWidth: '70px' }}>[{log.time}]</span>
            <span style={{ color: getLogColor(log.type), wordBreak: 'break-all' }}>
              {log.message}
            </span>
          </div>
        ))}
        <div ref={consoleEndRef} />
      </div>
    </div>
  );
}