export const formatSeconds = (seconds) => {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s < 10 ? '0' : ''}${s}`;
};

export const getRiskLevel = (riskScore) => {
  if (riskScore > 0.7) return { label: 'CRITICAL', color: '#ff4757' };
  if (riskScore > 0.4) return { label: 'WARNING', color: '#f59e0b' };
  return { label: 'SAFE', color: '#2ed573' };
};