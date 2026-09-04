import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getZones, getZoneById } from '../services/zones';
import { getRiskSummary, getAlerts, acknowledgeAlert } from '../services/risk';
import { calculateRoute as fetchRoute, getRoadsStatus } from '../services/routing';
import { simulateConditions } from '../services/simulation';
import { getReportsQueue, submitReport as postReport } from '../services/reports';
import { dispatchAlerts as postDispatchAlerts } from '../services/alerts';
import { ROLES } from '../data/constants';
import { LOCATIONS, getLocationData } from '../data/locations';
import { translations, SUPPORTED_LANGS } from '../i18n/translations';

const TalusContext = createContext(null);

export function TalusProvider({ children }) {
  // Location State — NER multi-corridor (gangtok live, lachung/darjeeling preview)
  const [activeLocation, setActiveLocation] = useState('gangtok');
  const locationData = getLocationData(activeLocation);

  // Language State — persisted, drives all UI + alert dispatch language
  const [lang, setLangState] = useState(() => {
    try { return localStorage.getItem('talus_lang') || 'en'; } catch { return 'en'; }
  });
  const setLang = useCallback((newLang) => {
    setLangState(newLang);
    try { localStorage.setItem('talus_lang', newLang); } catch {}
  }, []);
  const t = useCallback((key) => {
    const table = translations[lang] || translations.en;
    return table[key] || translations.en[key] || key;
  }, [lang]);

  // Application State
  const [role, setRoleState] = useState('district_officer'); // default to district disaster officer
  const [selectedZoneId, setSelectedZoneId] = useState('S1'); // default to Slope S1 (Tathangchen Critical)
  const [zones, setZones] = useState([]);
  const [selectedZoneData, setSelectedZoneData] = useState(null);
  const [riskSummary, setRiskSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [roads, setRoads] = useState([]);
  const [reports, setReports] = useState([]);
  const [alertDispatchData, setAlertDispatchData] = useState(null);
  
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

  // Location switcher — Gangtok live, others preview (local fixtures until NGEN extraction)
  const switchLocation = useCallback((locId) => {
    const loc = getLocationData(locId);
    setActiveLocation(loc.id);
    const firstZone = loc.zones[0]?.id || 'S1';
    setSelectedZoneId(firstZone);
    setActiveSimulation(null);
  }, []);

  // Helper: build preview zones for non-live locations (fixture scores, no API)
  const buildPreviewZones = useCallback((locId) => {
    const loc = getLocationData(locId);
    // Preview risk mapping — distinct per corridor to show location differentiation
    const previewScores = locId === 'lachung'
      ? { N1: 86, N2: 73, N3: 64, N4: 49 }
      : locId === 'darjeeling'
      ? { D1: 81, D2: 76, D3: 62, D4: 46 }
      : { S1: 89, S2: 78, S3: 66, S4: 52 };
    const bands = (s) => s >= 85 ? 'CRITICAL' : s >= 75 ? 'HIGH' : s >= 65 ? 'MODERATE' : s >= 50 ? 'LOW' : 'VERY_LOW';
    return loc.zones.map(z => ({
      id: z.id,
      name: z.name,
      sector: z.type || '',
      risk_score: previewScores[z.id] ?? 60,
      risk_band: bands(previewScores[z.id] ?? 60),
      confidence: 62,
      status: bands(previewScores[z.id] ?? 60) === 'CRITICAL' ? 'Critical - preview' : 'Preview',
      geometry: { coordinates: z.coordinates, centroid: z.centroid, benches: z.benches },
      trend: z.id.endsWith('1') || z.id.endsWith('2') ? 'escalating' : 'stable',
    }));
  }, []);

  // Initial Data Load — live for Gangtok, preview for other corridors
  const loadInitialData = useCallback(async (overrideLang = null) => {
    const effectiveLang = overrideLang || lang;
    setLoading(true);
    setError(null);
    try {
      const loc = getLocationData(activeLocation);
      if (!loc.live) {
        // Preview location: no live API, use local fixtures
        const previewZones = buildPreviewZones(activeLocation);
        setZones(previewZones);
        setAlerts([]);
        setRoads(loc.roads);
        const previewReports = await getReportsQueue().catch(() => []);
        setReports(Array.isArray(previewReports) ? previewReports : previewReports.reports || []);
        setRiskSummary({
          criticalCount: previewZones.filter(z => z.risk_band === 'CRITICAL').length,
          highCount: previewZones.filter(z => z.risk_band === 'HIGH').length,
          moderateCount: previewZones.filter(z => z.risk_band === 'MODERATE').length,
          lowCount: previewZones.filter(z => z.risk_band === 'LOW' || z.risk_band === 'VERY_LOW').length,
          totalZones: previewZones.length,
          dataQualityConfidence: 62,
          activePersonnelInHazard: 0,
          systemStatus: previewZones.some(z => z.risk_band === 'CRITICAL') ? 'CRITICAL_ALERT' : 'HIGH_ALERT',
        });
        // Build preview zone detail from first zone
        const first = previewZones[0];
        if (first) {
          setSelectedZoneId(first.id);
          setSelectedZoneData({
            id: first.id,
            name: first.name,
            sector: first.sector,
            risk_score: first.risk_score,
            risk_band: first.risk_band,
            confidence: first.confidence,
            status: first.status,
            geometry: first.geometry,
            updated_at: new Date().toISOString(),
            missingEvidence: ["preview: NGEN extraction pending for this corridor"],
            missing_evidence: ["preview: NGEN extraction pending"],
            role_actions: {},
            telemetry: { slope_angle: 32, rainfall_24h: 88, rainfall_7d: 210, soil_moisture: 0.31 },
            shap: [{ feature: "preview", value: 0, rawValue: "0", description: "Preview — live SHAP after NGEN" }],
            trend: { direction: first.trend === 'escalating' ? 'rising' : 'stable', rapid: false, history: [], historySource: 'preview' },
            isPreview: true,
          });
        }
        const defaultRoute = await fetchRoute({ originKey: 'worker_zoneA_to_ap1' }).catch(() => null);
        setActiveRoutePlan(defaultRoute);
        return;
      }
      // Live path (Gangtok + now Lachung/Darjeeling via backend stores)
      const [zonesRes, alertsRes, roadsRes, reportsRes] = await Promise.all([
        getZones(activeLocation),
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

      // Load initial selected slope for this corridor (lang-aware for decisions)
      const firstLiveId = zonesRes.zones[0]?.id || 'S1';
      setSelectedZoneId(firstLiveId);
      const initialZone = await getZoneById(firstLiveId, lang);
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
  }, [activeLocation, buildPreviewZones]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Zone Selection Handler — live for Gangtok, preview fallback
  const selectZone = useCallback(async (zoneId) => {
    setSelectedZoneId(zoneId);
    setZoneLoading(true);
    try {
      const loc = getLocationData(activeLocation);
      if (!loc.live) {
        const previewZones = buildPreviewZones(activeLocation);
        const pz = previewZones.find(z => z.id === zoneId);
        if (pz) {
          setSelectedZoneData({
            id: pz.id,
            name: pz.name,
            sector: pz.sector,
            risk_score: pz.risk_score,
            risk_band: pz.risk_band,
            confidence: pz.confidence,
            status: pz.status,
            geometry: pz.geometry,
            updated_at: new Date().toISOString(),
            missingEvidence: ["preview: NGEN extraction pending for this corridor"],
            missing_evidence: ["preview: NGEN extraction pending"],
            role_actions: {},
            telemetry: { slope_angle: 32, rainfall_24h: 88, rainfall_7d: 210, soil_moisture: 0.31 },
            shap: [{ feature: "preview", value: 0, rawValue: "0", description: "Preview — live SHAP after NGEN" }],
            trend: { direction: pz.trend === 'escalating' ? 'rising' : 'stable', rapid: false, history: [], historySource: 'preview' },
            isPreview: true,
          });
        }
        return;
      }
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
  }, [activeSimulation, activeLocation, buildPreviewZones]);

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
    // Reload via location-aware loader
    await loadInitialData();
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
    // Location (multi-corridor)
    activeLocation,
    setActiveLocation: switchLocation,
    switchLocation,
    locationData,
    locations: LOCATIONS,

    // Language (i18n)
    lang,
    setLang,
    t,
    supportedLangs: SUPPORTED_LANGS,

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

  return <TalusContext.Provider value={value}>{children}</TalusContext.Provider>;
}

export function useTalusContext() {
  const context = useContext(TalusContext);
  if (!context) {
    throw new Error('useTalusContext must be used within a TalusProvider');
  }
  return context;
}

// Backward compat aliases — Mine* deprecated, use Talus*
export const MineContext = TalusContext;
export const MineProvider = TalusProvider;
export const useMineContext = useTalusContext;
