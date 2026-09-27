import { TrendingUp, AlertTriangle, Activity, Car } from 'lucide-react';

export default function KpiCards() {
  const kpis = [
    { title: 'Total vehicles', value: '12,450', trend: '+14%', icon: <Car size={24} />, color: '#3b82f6' },
    { title: 'Critical incidents', value: '34', trend: '-2%', icon: <AlertTriangle size={24} />, color: '#ff4757' },
    { title: 'Average collision risk', value: '18%', trend: '+5%', icon: <Activity size={24} />, color: '#f59e0b' },
    { title: 'Detection accuracy (mAP)', value: '94.2%', trend: '+1.2%', icon: <TrendingUp size={24} />, color: '#2ed573' }
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '24px' }}>
      {kpis.map((kpi, i) => (
        <div key={i} style={{ backgroundColor: '#15181e', padding: '20px', borderRadius: '16px', border: '1px solid #2d3748', borderLeft: `4px solid ${kpi.color}`, display: 'flex', alignItems: 'center', gap: '16px', transition: 'transform 0.2s', cursor: 'pointer' }} onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-4px)'} onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}>
          <div style={{ backgroundColor: `${kpi.color}20`, padding: '12px', borderRadius: '12px', color: kpi.color }}>
            {kpi.icon}
          </div>
          <div>
            <h4 style={{ margin: '0 0 4px 0', color: '#8b949e', fontSize: '14px' }}>{kpi.title}</h4>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
              <span style={{ fontSize: '24px', fontWeight: 'bold', color: '#e2e8f0' }}>{kpi.value}</span>
              <span style={{ fontSize: '12px', color: kpi.trend.startsWith('+') ? '#2ed573' : '#ff4757', fontWeight: 'bold' }}>
                {kpi.trend}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}