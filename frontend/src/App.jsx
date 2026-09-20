import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { TalusProvider } from './context/TalusContext';
import Layout from './components/Layout';
import ErrorBoundary from './components/Common/ErrorBoundary';
import { LoadingSkeleton } from './components/Common/LoadingSkeleton';
const MapPage = lazy(() => import('./pages/MapPage'));
const ReportsPage = lazy(() => import('./pages/ReportsPage'));
const LabPage = lazy(() => import('./pages/LabPage'));
const RoutesPage = lazy(() => import('./pages/RoutesPage'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const VillagerPage = lazy(() => import('./pages/roles/VillagerPage'));
const DistrictPage = lazy(() => import('./pages/roles/DistrictPage'));
const StatePage = lazy(() => import('./pages/roles/StatePage'));
const RescuePage = lazy(() => import('./pages/roles/RescuePage'));
const AdminPage = lazy(() => import('./pages/AdminPage'));

// Modals stay global so deep links can open them
import WhatIfDrawer from './components/Simulation/WhatIfDrawer';
import SafeRouteModal from './components/Routing/SafeRouteModal';
import ReportModal from './components/Reports/ReportModal';
import AlertPanel from './components/Alerts/AlertPanel';
import RequireRole from './components/Auth/RequireRole';

function Warmup() {
  React.useEffect(() => {
    // Client-side wake: fire on Vercel load (villager default) so Render's 15-min sleep
    // is hidden behind the hero, not on the first SHAP click. No await, no block.
    const base = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/api\/?$/, '');
    fetch(`${base}/health`, { cache: 'no-store' }).catch(() => {});
  }, []);
  return null;
}

export default function App() {
  return (
    <TalusProvider>
      <Warmup />
      <ErrorBoundary>
        <BrowserRouter>
          <Suspense fallback={<div className="max-w-[1920px] mx-auto p-6"><LoadingSkeleton lines={6} /></div>}>
            <Routes>
              <Route element={<Layout />}>
                <Route index element={<Navigate to="/role/villager" replace />} />
                <Route path="map" element={<MapPage />} />
                <Route path="reports" element={<ReportsPage />} />
                <Route path="lab" element={<LabPage />} />
                <Route path="routes" element={<RoutesPage />} />
                {/* Role shells — villager open, officers + admin PIN-gated (direct URLs included) */}
                <Route path="role/villager" element={<VillagerPage />} />
                <Route path="role/district_officer" element={<RequireRole allow="district_officer"><DistrictPage /></RequireRole>} />
                <Route path="role/state_manager" element={<RequireRole allow="state_manager"><StatePage /></RequireRole>} />
                <Route path="role/rescue_team" element={<RequireRole allow="rescue_team"><RescuePage /></RequireRole>} />
                <Route path="admin" element={<RequireRole allow={['admin', 'district_officer', 'state_manager']}><AdminPage /></RequireRole>} />
                <Route path="dashboard" element={<Dashboard />} />
              </Route>
            </Routes>
          </Suspense>
          {/* Global drawers/modals — URL + state driven */}
          <WhatIfDrawer />
          <SafeRouteModal />
          <ReportModal />
          <AlertPanel />
        </BrowserRouter>
      </ErrorBoundary>
    </TalusProvider>
  );
}
