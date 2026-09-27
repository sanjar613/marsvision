import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Video, Shield, Activity, BarChart2, Settings, Users, BookOpen, PanelLeftClose, PanelLeftOpen, Radar, FileText, Upload } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';

export default function DashboardLayout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(() => window.matchMedia('(min-width: 681px)').matches);
  const navigate = useNavigate();
  const { systemAlert } = useAppStore();

  const navGroups = [
    { label: 'MONITORING', items: [
    { path: '/', label: 'Live Monitor', icon: <Video size={20} /> },
    { path: '/archive', label: 'Incident Archive', icon: <Shield size={20} /> },
    { path: '/samples', label: 'Test Samples', icon: <Activity size={20} /> },
    ] },
    { label: 'INSIGHTS', items: [
    { path: '/eda', label: 'EDA & Results', icon: <BarChart2 size={20} /> },
    { path: '/reports', label: 'Executive Report', icon: <FileText size={20} /> },
    { path: '/architecture', label: 'Problem and approach', icon: <BookOpen size={20} /> },
    ] },
    { label: 'WORKSPACE', items: [
    { path: '/settings', label: 'Backend Config', icon: <Settings size={20} /> },
    { path: '/team', label: 'Team', icon: <Users size={20} /> },
    ] },
  ];

  return (
    <div className="dashboard-shell">
      <aside className="dashboard-sidebar" data-open={sidebarOpen}>
        <div className="sidebar-brand">
          <NavLink to="/" className="brand-lockup" aria-label="MarsVision home">
            <span className="brand-mark"><Radar size={21} strokeWidth={2.1} /></span>
            {sidebarOpen && <span className="brand-name">mars<span>vision</span><small>TRAFFIC INTELLIGENCE</small></span>}
          </NavLink>
          <button className="sidebar-toggle" aria-label={sidebarOpen ? 'Collapse navigation' : 'Expand navigation'} aria-expanded={sidebarOpen} onClick={() => setSidebarOpen(!sidebarOpen)} title={sidebarOpen ? 'Collapse navigation' : 'Expand navigation'}>
            {sidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
          </button>
        </div>

        <button
          type="button"
          className="sidebar-demo-cta"
          aria-label="Try demo and jump to video upload"
          title="Try demo"
          onClick={() => navigate('/', { replace: true, state: { focusUpload: Date.now() } })}
        >
          <span className="sidebar-demo-icon"><Upload size={17} /></span>
          {sidebarOpen && <span className="sidebar-demo-label">Try demo<small>VIDEO ANALYSIS</small></span>}
        </button>

        <nav className="dashboard-nav" aria-label="Main navigation">
          {navGroups.map((group) => (
            <div className="nav-group" key={group.label}>
              {sidebarOpen && <div className="nav-group-label">{group.label}</div>}
              {group.items.map((item) => (
                <NavLink key={item.path} to={item.path} end={item.path === '/'} title={!sidebarOpen ? item.label : undefined} className="dashboard-nav-link">
                  {item.icon}
                  {sidebarOpen && <span>{item.label}</span>}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span className="footer-mark">W</span>
          {sidebarOpen && <span>WIUT · CV TRACK 2026</span>}
        </div>
      </aside>

      <div className="dashboard-content">
        {systemAlert && <div className="system-alert" role="alert"><Shield size={17} />{systemAlert}</div>}
        <div className="workspace-topbar">
          <div className="workspace-context"><span className="context-dot" /><span>TRAFFIC SAFETY PLATFORM</span><span className="context-divider">/</span><span>OPERATIONS WORKSPACE</span></div>
          <div className="workspace-edition"><span className="edition-indicator" />HACKATHON EDITION</div>
        </div>
        <main className="dashboard-main">{children}</main>
      </div>
    </div>
  );
}