import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, ReferenceLine } from 'recharts';

export default function RiskChart({ data, threshold = 0.25 }) {
  const colors = { bg: '#0b0d10', primary: '#ff4757', text: '#e2e8f0', border: '#2d3748', panel: '#15181e' };
  
  const formattedData = (Array.isArray(data) ? data : []).flatMap((point) => {
    const [time, risk] = Array.isArray(point) ? point : [point?.time, point?.risk];
    const timestamp = Number(time);
    const score = Number(risk);
    if (!Number.isFinite(timestamp) || !Number.isFinite(score)) return [];
    return [{ time: timestamp.toFixed(1), risk: score }];
  });

  return (
    <div style={{ backgroundColor: colors.panel, padding: '24px', borderRadius: '16px', border: `1px solid ${colors.border}` }}>
      <h3 style={{ marginTop: 0, color: '#8b949e', fontSize: '16px' }}>
        Accident risk curve · Part B
      </h3>
      <div style={{ height: '280px', width: '100%', marginTop: '20px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={formattedData}>
            <defs>
              <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={colors.primary} stopOpacity={0.4}/>
                <stop offset="95%" stopColor={colors.primary} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={colors.border} vertical={false} />
            <XAxis dataKey="time" stroke="#8b949e" tick={{ fontSize: 12 }} tickMargin={10} />
            <YAxis stroke="#8b949e" domain={[0, 1]} tick={{ fontSize: 12 }} tickMargin={10} />
            <Tooltip 
              contentStyle={{ backgroundColor: colors.bg, borderColor: colors.border, borderRadius: '8px', color: '#fff' }} 
              itemStyle={{ color: colors.primary, fontWeight: 'bold' }}
            />
            <ReferenceLine y={threshold} stroke="#f25540" strokeDasharray="5 5" label={{ value: `Alarm ${threshold.toFixed(2)}`, fill: '#f25540', fontSize: 10, position: 'insideTopRight' }} />
            <Area type="monotone" dataKey="risk" stroke={colors.primary} strokeWidth={3} fillOpacity={1} fill="url(#colorRisk)" activeDot={{ r: 6, fill: colors.primary, stroke: colors.bg, strokeWidth: 2 }} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}