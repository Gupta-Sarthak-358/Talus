import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getZones, getZoneById } from '../services/zones';
import { getRiskSummary, getAlerts, acknowledgeAlert } from '../services/risk';
import { calculateRoute as fetchRoute, getRoadsStatus } from '../services/routing';
import { simulateConditions } from '../services/simulation';
import { getReportsQueue, submitReport as postReport } from '../services/reports';
import { dispatchAlerts as postDispatchAlerts } from '../services/alerts';
import { ROLES, MOCK_MULTILINGUAL_ALERT } from '../data/mockData';

const MineContext = createContext(null);

export function MineProvider({ children }) {
  // Application State
  const [role, setRoleState] = useState('district_officer'); // default to district disaster officer
  const [selectedZoneId, setSelectedZoneId] = useState('S1'); // default to Slope S1 (Tathangchen Critical)
  const [zones, setZones] = useState([]);
  const [selectedZoneData, setSelectedZoneData] = useState(null);
  const [riskSummary, setRiskSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [roads, setRoads] = useState([]);
  const [reports, setReports] = useState([]);
  const [alertDispatchData, setAlertDispatchData] = useState(MOCK_MULTILINGUAL_ALERT);
  
  // UI & Modals State
  const [isWhatIfOpen, setIsWhatIfOpen] = useState(false);
  const [isRouteModalOpen, setIsRouteModalOpen] = useState(false);
  const [isCvModalOpen, setIsCvModalOpen] = useState(false);
  const [isAlertsDrawerOpen, setIsAlertsDrawerOpen] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isRoadsModalOpen, setIsRoadsModalOpen] = useState(false);
  
  // Simulation Overrides State
  const [activeSimulation, setActiveSimulation] = useState(null); // null when using baseline
  
  // Route Display State
  const [activeRoutePlan, setActiveRoutePlan] = useState(null);
  const [routeMode, setRouteMode] = useState('both'); // 'both', 'risk_aware', 'normal', 'none'
  
  // Map Layer Controls
  const [mapLayers, setMapLayers] = useState({
    sensors: true,
    infrastructure: true,
    hazardGlow: true,
    contourBenches: true,
    routes: true,
    roads: true,
  });

  // Loading and Error States
  const [loading, setLoading] = useState(true);
  const [zoneLoading, setZoneLoading] = useState(false);
  const [simulationLoading, setSimulationLoading] = useState(false);
  const [error, setError] = useState(null);

  // Initial Data Load
  const loadInitialData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [zonesRes, alertsRes, roadsRes, reportsRes] = await Promise.all([
        getZones(),
        getAlerts(),
        getRoadsStatus(),
        getReportsQueue(),
      ]);

      setZones(zonesRes.zones);
      setAlerts(alertsRes.alerts);
      setRoads(roadsRes);
      setReports(reportsRes);
      
      const summary = await getRiskSummary(zonesRes.zones);
      setRiskSummary(summary);

      // Load initial selected slope (S1 Tathangchen)
      const initialZone = await getZoneById('S1');
      setSelectedZoneData(initialZone.zone || initialZone);

      // Preload default route plan (S1 -> S4 avoiding R2)
      const defaultRoute = await fetchRoute({ originKey: 'worker_zoneA_to_ap1' });
      setActiveRoutePlan(defaultRoute);
    } catch (err) {
      console.error('Failed to load initial NER intelligence:', err);
      setError(err.message || 'Failed to connect to landslide intelligence service.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Zone Selection Handler
  const selectZone = useCallback(async (zoneId) => {
    setSelectedZoneId(zoneId);
    setZoneLoading(true);
    try {
      // If the selected zone has an active simulation override, use simulated data
      if (activeSimulation && activeSimulation.zone_id === zoneId) {
        const base = await getZoneById(zoneId);
        const baseObj = base.zone || base;
        setSelectedZoneData({
          ...baseObj,
          risk_score: activeSimulation.risk_score,
          risk_band: activeSimulation.risk_band,
          confidence: activeSimulation.confidence,
          shap: activeSimulation.shap,
          trend: activeSimulation.trend,
          isSimulated: true,
          caveat: activeSimulation.caveat,
        });
      } else {
        const zoneRes = await getZoneById(zoneId);
        setSelectedZoneData(zoneRes.zone || zoneRes);
      }
    } catch (err) {
      console.error(`Error loading zone ${zoneId}:`, err);
    } finally {
      setZoneLoading(false);
    }
  }, [activeSimulation]);

  // Role Switcher Handler
  const setRole = (newRoleId) => {
    setRoleState(newRoleId);
  };

  // Run What-If Simulation
  const runSimulation = async (params) => {
    setSimulationLoading(true);
    try {
      const simResult = await simulateConditions(params);
      setActiveSimulation(simResult);

      // Update zone list with simulated risk for map coloring
      setZones((prevZones) =>
        prevZones.map((z) =>
          z.id === params.zone_id
            ? {
                ...z,
                risk_score: simResult.risk_score,
                risk_band: simResult.risk_band,
                confidence: simResult.confidence,
                isSimulated: true,
                caveat: simResult.caveat,
              }
            : z
        )
      );

      // If simulated zone is currently selected, update its view immediately
      if (selectedZoneId === params.zone_id) {
        setSelectedZoneData((prev) => ({
          ...prev,
          risk_score: simResult.risk_score,
          risk_band: simResult.risk_band,
          confidence: simResult.confidence,
          shap: simResult.shap,
          trend: simResult.trend,
          isSimulated: true,
          simulationExplanation: simResult.explanationText,
          caveat: simResult.caveat,
        }));
      }

      // Recalculate summary KPIs
      setRiskSummary((prev) => {
        if (!prev) return prev;
        const isCritical = simResult.risk_band === 'CRITICAL';
        const isHigh = simResult.risk_band === 'HIGH';
        return {
          ...prev,
          criticalCount: isCritical ? (prev.criticalCount || 1) : prev.criticalCount,
          highCount: isHigh ? (prev.highCount || 1) + 1 : prev.highCount,
        };
      });

      return simResult;
    } catch (err) {
      console.error('Simulation calculation failed:', err);
      throw err;
    } finally {
      setSimulationLoading(false);
    }
  };

  // Reset What-If Simulation back to baseline
  const resetSimulation = async () => {
    setActiveSimulation(null);
    setLoading(true);
    try {
      const zonesRes = await getZones();
      setZones(zonesRes.zones);
      const summary = await getRiskSummary(zonesRes.zones);
      setRiskSummary(summary);
      const currentZone = await getZoneById(selectedZoneId);
      setSelectedZoneData(currentZone.zone || currentZone);
    } finally {
      setLoading(false);
    }
  };

  // Calculate Safe Route
  const executeRouting = async ({ originKey = 'worker_zoneA_to_ap1', avoidZoneIds } = {}) => {
    try {
      const result = await fetchRoute({ originKey, avoidZoneIds });
      setActiveRoutePlan(result);
      return result;
    } catch (err) {
      console.error('Route calculation failed:', err);
      throw err;
    }
  };

  // Reports Management
  const submitNewReport = async (reportData) => {
    const res = await postReport(reportData);
    const updated = await getReportsQueue();
    setReports(updated);
    return res;
  };

  const refreshReports = async () => {
    const updated = await getReportsQueue();
    setReports(updated);
  };

  // Roads Management
  const refreshRoads = async () => {
    const updated = await getRoadsStatus();
    setRoads(updated);
  };

  // Multilingual Alert Dispatch Fixture
  const dispatchAlertFixture = async () => {
    const res = await postDispatchAlerts();
    setAlertDispatchData(res);
    return res;
  };

  // Dismiss / Acknowledge Alert
  const handleAcknowledgeAlert = async (alertId) => {
    try {
      await acknowledgeAlert(alertId);
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, acknowledged: true } : a))
      );
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  // Toggle Map Layer
  const toggleMapLayer = (layerKey) => {
    setMapLayers((prev) => ({
      ...prev,
      [layerKey]: !prev[layerKey],
    }));
  };

  const value = {
    // Role
    role,
    setRole,
    currentRoleMeta: ROLES.find((r) => r.id === role) || ROLES[0],
    
    // Zones & Risk
    zones,
    selectedZoneId,
    selectedZoneData,
    selectZone,
    riskSummary,
    
    // Alerts
    alerts,
    handleAcknowledgeAlert,
    unacknowledgedAlertsCount: alerts.filter((a) => !a.acknowledged).length,
    alertDispatchData,
    dispatchAlertFixture,

    // Roads
    roads,
    refreshRoads,

    // Reports
    reports,
    submitNewReport,
    refreshReports,

    // Routing
    activeRoutePlan,
    routeMode,
    setRouteMode,
    executeRouting,

    // Simulation
    activeSimulation,
    runSimulation,
    resetSimulation,
    simulationLoading,

    // Modals
    isWhatIfOpen,
    setIsWhatIfOpen,
    isRouteModalOpen,
    setIsRouteModalOpen,
    isCvModalOpen,
    setIsCvModalOpen,
    isAlertsDrawerOpen,
    setIsAlertsDrawerOpen,
    isReportModalOpen,
    setIsReportModalOpen,
    isRoadsModalOpen,
    setIsRoadsModalOpen,

    // Map Layers
    mapLayers,
    toggleMapLayer,

    // Global Status
    loading,
    zoneLoading,
    error,
    refreshData: loadInitialData,
  };

  return <MineContext.Provider value={value}>{children}</MineContext.Provider>;
}

export function useMineContext() {
  const context = useContext(MineContext);
  if (!context) {
    throw new Error('useMineContext must be used within a MineProvider');
  }
  return context;
}
