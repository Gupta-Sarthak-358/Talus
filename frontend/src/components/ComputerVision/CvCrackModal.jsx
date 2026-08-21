import React, { useState, useEffect } from 'react';
import { useMineContext } from '../../context/MineContext';
import { getCvCrackAnalysis } from '../../services/cv';
import { Eye, X, Camera, ShieldCheck, Sparkles, Layers, ArrowRight, Info, AlertTriangle } from 'lucide-react';

export default function CvCrackModal() {
  const { isCvModalOpen, setIsCvModalOpen, selectedZoneId } = useMineContext();
  const [analysis, setAnalysis] = useState(null);
  const [deferredMessage, setDeferredMessage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showMask, setShowMask] = useState(true);

  useEffect(() => {
    if (isCvModalOpen) {
      setLoading(true);
      getCvCrackAnalysis(selectedZoneId || 'B')
        .then((res) => {
          if (res.deferred) {
            setDeferredMessage(res.message);
          } else {
            setAnalysis(res.analysis);
          }
        })
        .finally(() => setLoading(false));
    }
  }, [isCvModalOpen, selectedZoneId]);

  if (!isCvModalOpen) return null;

  if (deferredMessage) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
        <div className="w-full max-w-lg bg-mine-card border border-mine-border rounded-2xl shadow-2xl overflow-hidden">
          <div className="p-4 bg-mine-darker border-b border-mine-border flex items-center gap-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-bold text-white">Computer Vision — Deferred Capability</h3>
          </div>
          <div className="p-5 text-sm text-slate-300 leading-relaxed">{deferredMessage}</div>
          <div className="px-5 pb-5">
            <button
              onClick={() => setIsCvModalOpen(false)}
              className="px-3 py-1.5 rounded-lg bg-mine-border hover:bg-slate-600 text-xs font-semibold text-white transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-3xl bg-mine-card border border-mine-border rounded-2xl shadow-xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-4 bg-mine-darker border-b border-mine-border flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-talus-600/15 text-talus-600 flex items-center justify-center">
              <Eye className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-mine-text">
                Computer Vision — Geotechnical Crack Extraction
              </h3>
              <p className="text-[11px] text-mine-muted">
                Drone-captured highwall imagery segmenting crack density and strike orientation
              </p>
            </div>
          </div>

          <button
            onClick={() => setIsCvModalOpen(false)}
            className="p-1.5 rounded-lg hover:bg-mine-dark text-mine-muted hover:text-mine-text transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-4 overflow-y-auto">
          {loading || !analysis ? (
            <div className="p-12 text-center text-mine-muted text-xs animate-pulse">
              Loading drone orthomosaic and running CV segmentation inference...
            </div>
          ) : (
            <>
              {/* Drone Canvas Preview */}
              <div className="relative w-full h-56 bg-mine-dark rounded-xl overflow-hidden border border-mine-border flex items-center justify-center">
                {/* Synthetic Highwall Rock Texture with Fractures */}
                <svg className="absolute inset-0 w-full h-full opacity-60" xmlns="http://www.w3.org/2000/svg">
                  <defs>
                    <pattern id="rock-strata" width="100" height="20" patternUnits="userSpaceOnUse">
                      <path d="M 0 10 Q 25 15 50 10 T 100 10" fill="none" stroke="#997e67" strokeWidth="0.75" />
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
                        stroke="#c74732"
                        strokeWidth="3.5"
                        strokeDasharray="1, 1"
                        className="animate-pulse"
                      />
                      <circle cx="210" cy="110" r="4" fill="#c74732" />

                      {/* Secondary fracture */}
                      <path
                        d="M 280 60 L 330 95 L 390 140"
                        fill="none"
                        stroke="#d96b24"
                        strokeWidth="2.5"
                      />

                      {/* Toe fracture */}
                      <path
                        d="M 420 130 L 480 170 L 540 190"
                        fill="none"
                        stroke="#d99a24"
                        strokeWidth="2"
                      />
                    </g>
                  )}
                </svg>

                {/* Canvas Overlay Controls */}
                <div className="absolute top-3 left-3 bg-mine-darker border border-mine-border px-2.5 py-1 rounded text-[10px] font-mono text-mine-muted">
                  {analysis.captureTimestamp}
                </div>

                <div className="absolute bottom-3 right-3 flex gap-2">
                  <button
                    onClick={() => setShowMask(!showMask)}
                    className="px-2.5 py-1 bg-mine-card hover:bg-mine-dark border border-mine-border text-[11px] font-semibold text-mine-text rounded transition-colors"
                  >
                    {showMask ? 'Hide Segmentation Mask' : 'Show Segmentation Mask'}
                  </button>
                </div>
              </div>

              {/* Extracted Geotechnical Parameters */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                <div className="p-3 bg-mine-darker rounded-xl border border-mine-border">
                  <div className="text-[10px] uppercase text-mine-muted font-semibold">Tension Crack Density</div>
                  <div className="text-lg font-bold font-mono text-risk-high mt-0.5">
                    {analysis.crackDensityPerSqm} /m²
                  </div>
                  <div className="text-[9px] text-mine-muted">Direct Risk Weight: +14</div>
                </div>

                <div className="p-3 bg-mine-darker rounded-xl border border-mine-border">
                  <div className="text-[10px] uppercase text-mine-muted font-semibold">Max Crack Aperture/Length</div>
                  <div className="text-lg font-bold font-mono text-mine-text mt-0.5">
                    {analysis.maxCrackLengthMeters} m
                  </div>
                  <div className="text-[9px] text-mine-muted">Total: {analysis.totalCrackLengthMeters} m</div>
                </div>

                <div className="p-3 bg-mine-darker rounded-xl border border-mine-border">
                  <div className="text-[10px] uppercase text-mine-muted font-semibold">Dominant Strike Strike</div>
                  <div className="text-sm font-bold font-mono text-mine-text mt-1">
                    {analysis.dominantOrientation.split('(')[0]}
                  </div>
                  <div className="text-[9px] text-risk-critical">Parallel to Highwall</div>
                </div>

                <div className="p-3 bg-mine-darker rounded-xl border border-mine-border">
                  <div className="text-[10px] uppercase text-mine-muted font-semibold">CV Confidence</div>
                  <div className="text-lg font-bold font-mono text-risk-verylow mt-0.5">
                    {analysis.confidence}%
                  </div>
                  <div className="text-[9px] text-mine-muted">YOLOv8-Seg + UNet</div>
                </div>
              </div>

              {/* Detected Fractures Table */}
              <div className="space-y-1.5">
                <div className="text-xs font-semibold text-mine-text">
                  Segmented Discontinuity Instances:
                </div>
                <div className="space-y-1">
                  {analysis.detectedCracks.map((c) => (
                    <div
                      key={c.id}
                      className="p-2 bg-mine-darker rounded-lg border border-mine-border text-xs flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2 font-medium text-mine-text">
                        <span className="w-1.5 h-1.5 rounded-full bg-risk-critical"></span>
                        <span>{c.label}</span>
                      </div>
                      <div className="flex items-center gap-4 text-mine-muted font-mono text-[11px]">
                        <span>Length: {c.length}</span>
                        <span>Aperture: {c.width}</span>
                        <span>Strike: {c.strike}</span>
                        <span
                          className={`font-semibold ${
                            c.severity === 'Severe' ? 'text-risk-critical' : 'text-risk-moderate'
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
              <div className="p-3 bg-mine-darker border border-mine-border rounded-xl text-xs text-mine-text flex items-start gap-2.5">
                <Info className="w-4 h-4 text-talus-600 shrink-0 mt-0.5" />
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
