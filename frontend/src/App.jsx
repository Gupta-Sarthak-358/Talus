import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { TalusProvider } from './context/TalusContext';
import Layout from './components/Layout';
import Overview from './pages/Overview';
import MapPage from './pages/MapPage';
import ReportsPage from './pages/ReportsPage';
import LabPage from './pages/LabPage';
import RoutesPage from './pages/RoutesPage';
import Dashboard from './pages/Dashboard';
import VillagerPage from './pages/roles/VillagerPage';
import DistrictPage from './pages/roles/DistrictPage';
import StatePage from './pages/roles/StatePage';
import RescuePage from './pages/roles/RescuePage';

// Modals stay global so deep links can open them
import WhatIfDrawer from './components/Simulation/WhatIfDrawer';
import SafeRouteModal from './components/Routing/SafeRouteModal';
import ReportModal from './components/Reports/ReportModal';
import AlertPanel from './components/Alerts/AlertPanel';

export default function App() {
  return (
    <TalusProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Overview />} />
            <Route path="map" element={<MapPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="lab" element={<LabPage />} />
            <Route path="routes" element={<RoutesPage />} />
            {/* Role-specific demo pages: each role sees only what it needs */}
            <Route path="role/villager" element={<VillagerPage />} />
            <Route path="role/district_officer" element={<DistrictPage />} />
            <Route path="role/state_manager" element={<StatePage />} />
            <Route path="role/rescue_team" element={<RescuePage />} />
            {/* legacy single-screen still reachable for compare */}
            <Route path="dashboard" element={<Dashboard />} />
          </Route>
        </Routes>
        {/* Global drawers/modals — URL + state driven */}
        <WhatIfDrawer />
        <SafeRouteModal />
        <ReportModal />
        <AlertPanel />
      </BrowserRouter>
    </TalusProvider>
  );
}
