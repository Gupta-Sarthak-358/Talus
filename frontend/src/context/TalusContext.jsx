import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { getZones, getZoneById } from '../services/zones';
import { getRiskSummary, getAlerts, acknowledgeAlert } from '../services/risk';
import { calculateRoute as fetchRoute, getRoadsStatus, defaultOriginKey } from '../services/routing';
import { simulateConditions } from '../services/simulation';
import { getReportsQueue, submitReport as postReport, savePhotoBackground, saveReportOutbox, readReportOutbox, dropReportOutbox } from '../services/reports';
import { dispatchAlerts as postDispatchAlerts } from '../services/alerts';
import { ROLES } from '../data/constants';
import { LOCATIONS, getLocationData } from '../data/locations';
import { translations, SUPPORTED_LANGS } from '../i18n/translations';

export const TalusContext = createContext(null);

export function TalusProvider({ children }) {
  // Location State — NER multi-corridor (all live via backend stores)
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
  const [scoringMode, setScoringMode] = useState('fixture'); // 'live-rf' when backend serves trained-RF scores
  const [selectedZoneData, setSelectedZoneData] = useState(null);
  const [riskSummary, setRiskSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [roads, setRoads] = useState([]);
  const [reports, setReports] = useState([]);
  const [alertDispatchData, setAlertDispatchData] = useState(null);
  
  // UI & Modals State
  const [isWhatIfOpen, setIsWhatIfOpen] = useState(false);
  const [isRouteModalOpen, setIsRouteModalOpen] = useState(false);
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
    hazardGlow: true,
    routes: true,
    roads: true,
    runout: true,
    wounds: true,
  });

  // Loading and Error States
  const [loading, setLoading] = useState(true);
  const [zoneLoading, setZoneLoading] = useState(false);
  const [simulationLoading, setSimulationLoading] = useState(false);
  const [error, setError] = useState(null);

  // Corridor invalidation: switching corridors invalidates corridor-specific data (zones, roads, isolation, warning, reports filter, selectedZone)
  const selectZoneSeq = useRef(0);
  // Location switcher — all corridors live via backend
  const switchLocation = useCallback((locId) => {
    const loc = getLocationData(locId);
    setActiveLocation(loc.id);
    const firstZone = loc.zones[0]?.id || 'S1';
    setSelectedZoneId(firstZone);
    setSelectedZoneData(null); // invalidate old corridor detail cache immediately
    setActiveSimulation(null);
    selectZoneSeq.current += 1; // cancel any in-flight selectZone
  }, []);

  // Initial Data Load — all corridors live via backend stores; backend-down
  // shows the error state, never invented scores.
  const loadInitialData = useCallback(async (overrideLang = null) => {
    const effectiveLang = overrideLang || lang;
    setLoading(true);
    setError(null);
    try {
      // Live path (Gangtok + Lachung/Darjeeling via backend stores) — alerts are lang-aware
      const [zonesRes, alertsRes, roadsRes, reportsRes] = await Promise.all([
        getZones(activeLocation),
        getAlerts(effectiveLang),
        getRoadsStatus(activeLocation),
        getReportsQueue(),
      ]);

      setZones(zonesRes.zones);
      setScoringMode(zonesRes.scoring || 'fixture');
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

      // Preload default route plan for the active corridor
      // (upper -> valley avoiding R2; per-corridor waypoints so routes render
      // on that corridor's map instead of off-screen at Gangtok)
      const defaultRoute = await fetchRoute({ originKey: defaultOriginKey(activeLocation), location: activeLocation });
      setActiveRoutePlan(defaultRoute);
    } catch (err) {
      console.error('Failed to load initial NER intelligence:', err);
      setError(err.message || 'Failed to connect to landslide intelligence service.');
    } finally {
      setLoading(false);
    }
  }, [activeLocation, lang]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Zone Selection Handler — race-guarded: stale response must not overwrite fresh selection (see PLAN §14)
  const selectZone = useCallback(async (zoneId) => {
    const seq = ++selectZoneSeq.current;
    const locAtStart = activeLocation;
    setSelectedZoneId(zoneId);
    setZoneLoading(true);
    try {
      let data;
      if (activeSimulation && activeSimulation.zone_id === zoneId) {
        const base = await getZoneById(zoneId, lang);
        if (seq !== selectZoneSeq.current || locAtStart !== activeLocation) return; // stale
        const baseObj = base.zone || base;
        data = {
          ...baseObj,
          risk_score: activeSimulation.risk_score,
          risk_band: activeSimulation.risk_band,
          confidence: activeSimulation.confidence,
          shap: activeSimulation.shap,
          trend: activeSimulation.trend,
          isSimulated: true,
          caveat: activeSimulation.caveat,
        };
      } else {
        const zoneRes = await getZoneById(zoneId, lang);
        if (seq !== selectZoneSeq.current || locAtStart !== activeLocation) return; // stale B overwrote S2
        data = zoneRes.zone || zoneRes;
      }
      setSelectedZoneData(data);
    } catch (err) {
      if (seq !== selectZoneSeq.current) return;
      console.error(`Error loading zone ${zoneId}:`, err);
    } finally {
      if (seq === selectZoneSeq.current) setZoneLoading(false);
    }
  }, [activeSimulation, activeLocation, lang]);

  // Refetch selected zone when language changes so role_actions translate (villager avoid_msg etc.)
  useEffect(() => {
    if (selectedZoneId) {
      selectZone(selectedZoneId);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang]);

  // Role Switcher Handler — persists to localStorage so refresh keeps lane
  const setRole = (newRoleId) => {
    setRoleState(newRoleId);
    try { localStorage.setItem('talus_auth', JSON.stringify({ role: newRoleId, at: new Date().toISOString() })); } catch {}
  };
  // Restore saved role on mount (villager open, officers stay logged in until lock)
  useEffect(() => {
    try {
      const raw = localStorage.getItem('talus_auth');
      if (raw) {
        const a = JSON.parse(raw);
        if (a.role && a.role !== role) setRoleState(a.role);
      }
    } catch {}
  }, []);

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

  // Calculate Safe Route (defaults to active corridor's upper -> valley preset)
  const executeRouting = async ({ originKey = null, location = null, avoidZoneIds } = {}) => {
    const loc = location || activeLocation;
    try {
      const result = await fetchRoute({ originKey: originKey || defaultOriginKey(loc), location: loc, avoidZoneIds });
      setActiveRoutePlan(result);
      return result;
    } catch (err) {
      console.error('Route calculation failed:', err);
      throw err;
    }
  };

  // Reports Management (validation errors surface; network failures are
  // outboxed by the caller with the photo thumbnail — see ReportModal)
  const submitNewReport = async (reportData) => {
    const res = await postReport(reportData);
    const updated = await getReportsQueue();
    setReports(updated);
    return res;
  };

  const refreshReports = async () => {
    // Flush background outbox first (oldest first), then reload the live queue
    for (const entry of readReportOutbox()) {
      try {
        const res = await postReport(entry.payload);
        if (entry.thumb && res?.id) {
          savePhotoBackground(res.id, { dataUrl: entry.thumb, filename: entry.payload?.photo?.filename || '', mime: entry.payload?.photo?.mime || '' });
        }
        dropReportOutbox(entry.outboxId);
      } catch {
        break; // still offline — keep the rest queued
      }
    }
    const updated = await getReportsQueue();
    setReports(updated);
    return readReportOutbox().length;
  };

  // Roads Management
  const refreshRoads = async () => {
    const updated = await getRoadsStatus(activeLocation);
    setRoads(updated);
  };

  // Multilingual Alert Dispatch Fixture (app fixture or env-gated SMS)
  const dispatchAlertFixture = async (opts = {}) => {
    const res = await postDispatchAlerts(opts);
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
    scoringMode,
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
    // Fallback for HMR / outside-provider render — prevents hard crash, shows loading state
    console.warn('useTalusContext outside TalusProvider — returning fallback');
    return {
      zones: [], reports: [], roads: [], alerts: [],
      selectedZoneData: null, selectedZoneId: 'S1',
      locationData: { label: 'Gangtok Corridor, Sikkim', zones: [] },
      t: (k) => k, lang: 'en', role: 'villager',
      setIsReportModalOpen: () => {}, setIsAlertsDrawerOpen: () => {},
      setRole: () => {}, selectZone: () => {},
      loading: true, zoneLoading: false, error: null,
    };
  }
  return context;
}

// Backward compat aliases — Mine* deprecated, use Talus*
export const MineContext = TalusContext;
export const MineProvider = TalusProvider;
export const useMineContext = useTalusContext;
