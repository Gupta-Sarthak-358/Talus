import React, { useEffect } from 'react';
import { useTalusContext } from '../context/TalusContext';

export default function ReportsPage() {
  const { setIsReportModalOpen } = useTalusContext();
  useEffect(() => { setIsReportModalOpen(true); }, []);
  return (
    <main className="max-w-[1920px] mx-auto px-3 sm:px-4 py-6">
      <div className="bg-mine-card border border-mine-border rounded-2xl p-6 text-center">
        <h2 className="text-sm font-bold text-mine-text">Field Reports — Full Page</h2>
        <p className="text-xs text-mine-muted mt-1">The report queue modal is open. Use the header “Field Reports” button or this page for deep link <code className="font-mono">/reports</code>. Close the modal to return to overview.</p>
      </div>
    </main>
  );
}
