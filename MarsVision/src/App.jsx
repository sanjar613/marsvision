import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import DashboardLayout from './layouts/DashboardLayout';
import AnimatedPage from './components/ui/AnimatedPage';

const LiveDemo = lazy(() => import('./pages/LiveDemo'));
const EdaDashboard = lazy(() => import('./pages/EdaDashboard'));
const SamplesGallery = lazy(() => import('./pages/SamplesGallery'));
const SystemSettings = lazy(() => import('./pages/SystemSettings'));
const TeamInfo = lazy(() => import('./pages/TeamInfo'));
const IncidentArchive = lazy(() => import('./pages/IncidentArchive'));
const Architecture = lazy(() => import('./pages/Architecture'));
const ReportGenerator = lazy(() => import('./pages/ReportGenerator'));

export default function App() {
  return (
    <BrowserRouter>
      <DashboardLayout>
        <Suspense fallback={<div role="status" style={{ color: '#8b949e', padding: '32px' }}>Loading view...</div>}>
          <Routes>
            <Route path="/" element={<AnimatedPage><LiveDemo /></AnimatedPage>} />
            <Route path="/archive" element={<AnimatedPage><IncidentArchive /></AnimatedPage>} />
            <Route path="/architecture" element={<AnimatedPage><Architecture /></AnimatedPage>} />
            <Route path="/eda" element={<AnimatedPage><EdaDashboard /></AnimatedPage>} />
            <Route path="/samples" element={<AnimatedPage><SamplesGallery /></AnimatedPage>} />
            <Route path="/settings" element={<AnimatedPage><SystemSettings /></AnimatedPage>} />
            <Route path="/team" element={<AnimatedPage><TeamInfo /></AnimatedPage>} />
            <Route path="/reports" element={<AnimatedPage><ReportGenerator /></AnimatedPage>} />
          </Routes>
        </Suspense>
      </DashboardLayout>
    </BrowserRouter>
  );
}