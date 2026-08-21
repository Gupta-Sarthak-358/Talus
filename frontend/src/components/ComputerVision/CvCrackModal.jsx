import React, { useState, useEffect } from 'react';
import { useMineContext } from '../../context/MineContext';
import { getCvCrackAnalysis } from '../../services/cv';
import { Eye, X, Camera, ShieldCheck, Sparkles, Layers, ArrowRight, Info, AlertTriangle } from 'lucide-react';

export default function CvCrackModal() {
  const { isCvModalOpen, setIsCvModalOpen, selectedZoneId } = useMineContext();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showMask, setShowMask] = useState(true);

  useEffect(() => {
    if (isCvModalOpen) {
      setLoading(true);
      getCvCrackAnalysis(selectedZoneId || 'B')
        .then((res) => setAnalysis(res.analysis))
        .finally(() => setLoading(false));
    }
  }, [isCvModalOpen, selectedZoneId]);

  if (!isCvModalOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-3xl bg-mine-card border border-mine-border rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-4 bg-mine-darker border-b border-mine-border flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-talus-500/20 text-talus-400 flex items-center justify-center">
              <Eye className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">
                Computer Vision — Geotechnical Crack Extraction
              </h3>
              <p className="text-[11px] text-slate-400">
                Drone-captured highwall imagery segmenting crack density and strike orientation
              </p>
            </div>
          </div>

          <button
            onClick={() => setIsCvModalOpen(false)}
            className="p-1.5 rounded-lg hover:bg-mine-border text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-4 overflow-y-auto">
          {loading || !analysis ? (
            <div className="p-12 text-center text-slate-400 text-xs animate-pulse">
              Loading drone orthomosaic and running CV segmentation inference...
            </div>
          ) : (
            <>
              {/* Drone Canvas Preview */}
              <div className="relative w-full h-56 bg-gradient-to-br from-slate-900 via-stone-900 to-zinc-950 rounded-xl overflow-hidden border border-mine-border flex items-center justify-center">
                {/* Synthetic Highwall Rock Texture with Fractures */}
                <svg className="absolute inset-0 w-full h-full opacity-60" xmlns="http://www.w3.org/2000/svg">
                  <defs>
                    <pattern id="rock-strata" width="100" height="20" patternUnits="userSpaceOnUse">
                      <path d="M 0 10 Q 25 15 50 10 T 100 10" fill="none" stroke="#475569" strokeWidth="0.75" />
                    </pattern>
                  </defs>
                  <rect width="100%" height="100%" fill="url(#rock-strata)" />
                  
                  {/* Fractures / Cracks overlay */}
                  {showMask && (
                    <g className="transition-opacity duration-300">
                      {/* Main tension crack */}
                      <path
                        d="M 120 40 L 160 85 L 210 110 L 260 165 L 310 210"
                        fill="none"
                        stroke="#ef4444"
                        strokeWidth="3.5"
                        strokeDasharray="1, 1"
                        className="animate-pulse"
                      />
                      <circle cx="210" cy="110" r="4" fill="#ef4444" />

                      {/* Secondary fracture */}
                      <path
                        d="M 280 60 L 330 95 L 390 140"
                        fill="none"
                        stroke="#f97316"
                        strokeWidth="2.5"
                      />

                      {/* Toe fracture */}
                      <path
                        d="M 420 130 L 480 170 L 540 190"
                        fill="none"
                        stroke="#f59e0b"
                        strokeWidth="2"
                      />
                    </g>
                  )}
                </svg>

                {/* Canvas Overlay Controls */}
                <div className="absolute top-3 left-3 bg-mine-darkest/90 border border-mine-border px-2.5 py-1 rounded text-[10px] font-mono text-slate-300 backdrop-blur-sm">
                  {analysis.captureTimestamp}
                </div>

                <div className="absolute bottom-3 right-3 flex gap-2">
                  <button
                    onClick={() => setShowMask(!showMask)}
                    className="px-2.5 py-1 bg-mine-card/90 hover:bg-mine-dark border border-mine-border text-[11px] font-semibold text-slate-200 rounded backdrop-blur-sm transition-colors"
                  >
                    {showMask ? 'Hide Segmentation Mask' : 'Show Segmentation Mask'}
                  </button>
                </div>
              </div>

              {/* Extracted Geotechnical Parameters */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                <div className="p-3 bg-mine-darker rounded-xl border border-mine-border">
                  <div className="text-[10px] uppercase text-slate-400 font-semibold">Tension Crack Density</div>
                  <div className="text-lg font-bold font-mono text-orange-400 mt-0.5">
                    {analysis.crackDensityPerSqm} /m²
                  </div>
                  <div className="text-[9px] text-slate-400">Direct Risk Weight: +14</div>
                </div>

                <div className="p-3 bg-mine-darker rounded-xl border border-mine-border">
                  <div className="text-[10px] uppercase text-slate-400 font-semibold">Max Crack Aperture/Length</div>
                  <div className="text-lg font-bold font-mono text-slate-100 mt-0.5">
                    {analysis.maxCrackLengthMeters} m
                  </div>
                  <div className="text-[9px] text-slate-400">Total: {analysis.totalCrackLengthMeters} m</div>
                </div>

                <div className="p-3 bg-mine-darker rounded-xl border border-mine-border">
                  <div className="text-[10px] uppercase text-slate-400 font-semibold">Dominant Strike Strike</div>
                  <div className="text-sm font-bold font-mono text-slate-100 mt-1">
                    {analysis.dominantOrientation.split('(')[0]}
                  </div>
                  <div className="text-[9px] text-red-400">Parallel to Highwall</div>
                </div>

                <div className="p-3 bg-mine-darker rounded-xl border border-mine-border">
                  <div className="text-[10px] uppercase text-slate-400 font-semibold">CV Confidence</div>
                  <div className="text-lg font-bold font-mono text-emerald-400 mt-0.5">
                    {analysis.confidence}%
                  </div>
                  <div className="text-[9px] text-slate-400">YOLOv8-Seg + UNet</div>
                </div>
              </div>

              {/* Detected Fractures Table */}
              <div className="space-y-1.5">
                <div className="text-xs font-semibold text-slate-300">
                  Segmented Discontinuity Instances:
                </div>
                <div className="space-y-1">
                  {analysis.detectedCracks.map((c) => (
                    <div
                      key={c.id}
                      className="p-2 bg-mine-darker/80 rounded-lg border border-mine-border/80 text-xs flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2 font-medium text-slate-200">
                        <span className="w-1.5 h-1.5 rounded-full bg-red-400"></span>
                        <span>{c.label}</span>
                      </div>
                      <div className="flex items-center gap-4 text-slate-400 font-mono text-[11px]">
                        <span>Length: {c.length}</span>
                        <span>Aperture: {c.width}</span>
                        <span>Strike: {c.strike}</span>
                        <span
                          className={`font-semibold ${
                            c.severity === 'Severe' ? 'text-red-400' : 'text-amber-400'
                          }`}
                        >
                          {c.severity}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Pipeline Principle Alert */}
              <div className="p-3 bg-talus-950/40 border border-talus-500/30 rounded-xl text-xs text-slate-300 flex items-start gap-2.5">
                <Info className="w-4 h-4 text-talus-400 shrink-0 mt-0.5" />
                <p className="text-[11px] leading-relaxed">
                  <strong>Engineering Transparency Principle</strong>: Computer vision models extract measurable geometric metrics (crack length, aperture, joint orientation) rather than making black-box collapse predictions. These structured metrics are passed directly to the <strong>Talus Risk Engine</strong>.
                </p>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-mine-darker border-t border-mine-border flex justify-end">
          <button
            onClick={() => setIsCvModalOpen(false)}
            className="px-4 py-2 bg-talus-600 hover:bg-talus-500 text-white rounded-lg text-xs font-bold transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}
