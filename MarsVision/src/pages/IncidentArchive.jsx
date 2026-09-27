import { useState } from 'react';
import { AlertTriangle, Camera, CheckCircle, Database, Search, ChevronLeft, ChevronRight, Download } from 'lucide-react';
import InsightMetrics from '../components/ui/InsightMetrics';

const archiveReferenceTime = Date.parse('2026-01-01T12:00:00Z');
const archiveData = Array.from({ length: 25 }, (_, i) => ({
  id: `EVT-${1000 + i}`,
  date: new Date(archiveReferenceTime - i * 3600000).toLocaleString(),
  camera: i % 3 === 0 ? 'CAM_02 (Highway)' : 'CAM_01 (Main)',
  type: i % 4 === 0 ? 'ACCIDENT' : i % 5 === 0 ? 'WRONG_WAY' : 'JAYWALKING',
  risk: ((i * 37 % 50) / 100 + 0.4).toFixed(2),
  status: i % 7 === 0 ? 'REVIEWED' : 'PENDING'
}));

const archiveMetrics = [
  { label: 'Archive records', value: archiveData.length, detail: 'Fixed review sample', icon: Database, tone: 'cyan' },
  { label: 'Camera feeds', value: new Set(archiveData.map((row) => row.camera)).size, detail: 'In sample register', icon: Camera, tone: 'cyan' },
  { label: 'High risk', value: archiveData.filter((row) => Number(row.risk) >= 0.75).length, detail: 'Risk score ≥ 0.75', icon: AlertTriangle, tone: 'mars' },
  { label: 'Reviewed', value: archiveData.filter((row) => row.status === 'REVIEWED').length, detail: `${archiveData.filter((row) => row.status === 'PENDING').length} pending`, icon: CheckCircle, tone: 'amber' },
];

export default function IncidentArchive() {
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(0);
  const pageSize = 10;
  const normalizedSearch = searchTerm.trim().toLowerCase();
  const filtered = archiveData.filter((row) =>
    Object.values(row).some((value) => String(value).toLowerCase().includes(normalizedSearch))
  );
  const pageCount = Math.ceil(filtered.length / pageSize);
  const pageRows = filtered.slice(page * pageSize, (page + 1) * pageSize);

  const exportCsv = () => {
    const columns = ['id', 'date', 'camera', 'type', 'risk', 'status'];
    const escapeCsv = (value) => `"${String(value).replaceAll('"', '""')}"`;
    const csv = [
      columns.join(','),
      ...filtered.map((row) => columns.map((column) => escapeCsv(row[column])).join(','))
    ].join('\r\n');
    const url = URL.createObjectURL(new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'marsvision-incidents.csv';
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', height: '100%' }}>
      <div className="archive-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '16px' }}>
        <div>
          <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '10px', color: '#fff' }}>
            <Database color="#65d0d9" /> Incident archive
          </h2>
        </div>
        <div className="archive-header-tools" style={{ display: 'flex', gap: '12px' }}>
          <div className="archive-search" style={{ display: 'flex', alignItems: 'center', backgroundColor: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '8px 12px', border: '1px solid rgba(255,255,255,0.1)' }}>
            <Search size={16} color="#8b949e" style={{ marginRight: '8px' }} />
            <input 
              type="text" 
              className="archive-search-input"
              aria-label="Search incidents"
              placeholder="Search incidents..." 
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setPage(0); }}
              style={{ background: 'transparent', border: 'none', color: '#fff', outline: 'none', fontSize: '14px', width: '200px' }}
            />
          </div>
          <button onClick={exportCsv} style={{ display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: '#a9342b', color: '#fff', border: '1px solid rgba(255,128,104,0.32)', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
            <Download size={16} /> CSV
          </button>
        </div>
      </div>

      <InsightMetrics items={archiveMetrics} label="Sample archive statistics" />

      <div style={{ flex: 1, backgroundColor: 'rgba(20, 19, 25, 0.78)', backdropFilter: 'blur(12px)', borderRadius: '8px', border: '1px solid rgba(224,216,222,0.1)', overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', color: '#e2e8f0', fontSize: '14px' }}>
          <thead style={{ backgroundColor: 'rgba(0,0,0,0.5)', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
            <tr>
              <th style={{ padding: '16px' }}>Event ID</th>
              <th style={{ padding: '16px' }}>Date / Time</th>
              <th style={{ padding: '16px' }}>Camera</th>
              <th style={{ padding: '16px' }}>Event type</th>
              <th style={{ padding: '16px' }}>Risk Score</th>
              <th style={{ padding: '16px' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, i) => (
              <tr key={row.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.02)', backgroundColor: i % 2 === 0 ? 'rgba(255,255,255,0.01)' : 'transparent' }}>
                <td style={{ padding: '16px', fontFamily: 'monospace', color: '#65d0d9' }}>{row.id}</td>
                <td style={{ padding: '16px' }}>{row.date}</td>
                <td style={{ padding: '16px', color: '#8b949e' }}>{row.camera}</td>
                <td style={{ padding: '16px' }}>
                  <span style={{ color: row.type === 'ACCIDENT' ? '#ff4757' : '#e2e8f0', fontWeight: 'bold' }}>{row.type}</span>
                </td>
                <td style={{ padding: '16px', fontFamily: 'monospace' }}>{row.risk}</td>
                <td style={{ padding: '16px' }}>
                  <span style={{ backgroundColor: row.status === 'REVIEWED' ? 'rgba(46, 213, 115, 0.1)' : 'rgba(245, 158, 11, 0.1)', color: row.status === 'REVIEWED' ? '#2ed573' : '#f59e0b', padding: '4px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold' }}>
                    {row.status}
                  </span>
                </td>
              </tr>
            ))}
            {pageRows.length === 0 && <tr><td colSpan="6" style={{ padding: '24px', textAlign: 'center', color: '#8b949e' }}>No incidents found</td></tr>}
          </tbody>
        </table>
        
        <div style={{ padding: '16px', borderTop: '1px solid rgba(255,255,255,0.05)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
          <span style={{ color: '#8b949e', fontSize: '14px' }}>
            Showing {filtered.length === 0 ? 0 : page * pageSize + 1}-{Math.min((page + 1) * pageSize, filtered.length)} of {filtered.length}
          </span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button aria-label="Previous page" disabled={page === 0} onClick={() => setPage((current) => current - 1)} style={{ backgroundColor: 'rgba(255,255,255,0.05)', border: 'none', color: '#fff', padding: '6px', borderRadius: '4px', cursor: page === 0 ? 'not-allowed' : 'pointer', opacity: page === 0 ? 0.4 : 1 }}><ChevronLeft size={16} /></button>
            <button aria-label="Next page" disabled={page >= pageCount - 1} onClick={() => setPage((current) => current + 1)} style={{ backgroundColor: 'rgba(255,255,255,0.05)', border: 'none', color: '#fff', padding: '6px', borderRadius: '4px', cursor: page >= pageCount - 1 ? 'not-allowed' : 'pointer', opacity: page >= pageCount - 1 ? 0.4 : 1 }}><ChevronRight size={16} /></button>
          </div>
        </div>
      </div>
    </div>
  );
}