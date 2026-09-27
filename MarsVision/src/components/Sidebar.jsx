export default function Sidebar({ activeTab, setActiveTab }) {
  const colors = {
    panel: '#1a1d24',
    primary: '#ff4757',
    text: '#e2e8f0',
    border: '#2d3748'
  };

  const navItemStyle = (tabId) => ({
    padding: '12px 20px',
    cursor: 'pointer',
    backgroundColor: activeTab === tabId ? colors.primary : 'transparent',
    color: activeTab === tabId ? '#fff' : colors.text,
    borderRadius: '8px',
    marginBottom: '10px',
    transition: '0.3s',
    fontWeight: 'bold',
  });

  return (
    <div style={{ width: '250px', backgroundColor: colors.panel, padding: '20px', display: 'flex', flexDirection: 'column', borderRight: `1px solid ${colors.border}` }}>
      <h2 style={{ color: colors.primary, marginBottom: '40px', letterSpacing: '1px' }}>MARS_VISION</h2>
      <div onClick={() => setActiveTab('demo')} style={navItemStyle('demo')}>Live Demo</div>
      <div onClick={() => setActiveTab('samples')} style={navItemStyle('samples')}>Test videos</div>
      <div onClick={() => setActiveTab('eda')} style={navItemStyle('eda')}>EDA & Analytics</div>
      <div onClick={() => setActiveTab('team')} style={navItemStyle('team')}>About the team</div>
    </div>
  );
}