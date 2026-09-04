import React, { useEffect } from 'react';
import { useTalusContext } from '../context/TalusContext';

export default function LabPage() {
  const { setIsWhatIfOpen } = useTalusContext();
  useEffect(() => { setIsWhatIfOpen(true); }, []);
  return (
    <main className="max-w-[1920px] mx-auto px-3 sm:px-4 py-6">
      <div className="bg-mine-card border border-mine-border rounded-2xl p-6 text-center">
        <h2 className="text-sm font-bold text-mine-text">Scenario Lab — What-If Simulator</h2>
        <p className="text-xs text-mine-muted mt-1">Drawer is open. Try <code className="font-mono">S3 66→74</code> ML counterfactual or Causal physics. Deep link <code className="font-mono">/lab</code>.</p>
      </div>
    </main>
  );
}
