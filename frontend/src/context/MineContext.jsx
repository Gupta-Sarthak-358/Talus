import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getZones, getZoneById } from '../services/zones';
import { getRiskSummary, getAlerts, acknowledgeAlert } from '../services/risk';
import { calculateRoute as fetchRoute } from '../services/routing';
import { simulateConditions } from '../services/simulation';
import { ROLES } from '../data/mockData';

const MineContext = createContext(null);

export function MineProvider({ children }) {
  // Application State
  const [role, setRoleState] = useState('safety_officer'); // default to safety officer
  const [selectedZoneId, setSelectedZoneId] = useState('B'); // default to Zone B (highlighting critical features)
  const [zones, setZones] = useState([]);
  const [selectedZoneData, setSelectedZoneData] = useState(null);
  const [riskSummary, setRiskSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  
  // UI & Modals State
  const [isWhatIfOpen, setIsWhatIfOpen] = useState(false);
  const [isRouteModalOpen, setIsRouteModalOpen] = useState(false);
  const [isCvModalOpen, setIsCvModalOpen] = useState(false);
  const [isAlertsDrawerOpen, setIsAlertsDrawerOpen] = useState(false);
  
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
      const [zonesRes, alertsRes] = await Promise.all([
        getZones(),
        getAlerts(),
      ]);

      setZones(zonesRes.zones);
      setAlerts(alertsRes.alerts);
      
      const summary = await getRiskSummary(zonesRes.zones);
      setRiskSummary(summary);

      // Load initial selected zone (Zone B)
      const initialZone = await getZoneById('B');
      setSelectedZoneData(initialZone.zone);

      // Preload default route plan
      const defaultRoute = await fetchRoute({ originKey: 'worker_zoneA_to_ap1' });
      setActiveRoutePlan(defaultRoute);
    } catch (err) {
      console.error('Failed to load initial mine intelligence:', err);
      setError(err.message || 'Failed to connect to mine intelligence service.');
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
        setSelectedZoneData({
          ...base.zone,
          risk_score: activeSimulation.risk_score,
          risk_band: activeSimulation.risk_band,
          confidence: activeSimulation.confidence,
          shap: activeSimulation.shap,
          trend: activeSimulation.trend,
          isSimulated: true,
        });
      } else {
        const zoneRes = await getZoneById(zoneId);
        setSelectedZoneData(zoneRes.zone);
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
        }));
      }

      // Recalculate summary KPIs
      setRiskSummary((prev) => {
        if (!prev) return prev;
        const isCritical = simResult.risk_band === 'CRITICAL';
        const isHigh = simResult.risk_band === 'HIGH';
        return {
          ...prev,
          criticalCount: isCritical ? 1 : 0,
          highCount: isHigh ? 1 : 0,
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
      setSelectedZoneData(currentZone.zone);
    } finally {
      setLoading(false);
    }
  };

  // Calculate Safe Route
  const executeRouting = async ({ originKey, avoidZoneIds }) => {
    try {
      const result = await fetchRoute({ originKey, avoidZoneIds });
      setActiveRoutePlan(result);
      return result;
    } catch (err) {
      console.error('Route calculation failed:', err);
      throw err;
    }
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
