import React from 'react';
import { useTalusContext } from '../context/TalusContext';
import OpsQueuePreview from '../components/Ops/OpsQueuePreview';
import { FileText } from 'lucide-react';

/**
 * Field reports — full page (deep link /reports).
 * Never auto-opens the modal: the modal opens in place wherever requested and
 * closes back to the same page. Officers see the full queue; villagers see only
 * the submit action (unverified reports never leak to the field).
 */
export default function ReportsPage() {
  const { setIsReportModalOpen, reports, role, t } = useTalusContext();
  const isOfficer = role !== 'villager';

  return (
    <main className="max-w-[1920px] mx-auto px-3 sm:px-4 py-4 space-y-4">
      <div className="bg-zinc-900 text-white rounded-xl px-4 py-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="font-black text-sm tracking-wide">{t('reports.title')}</div>
          <div className="text-xs text-zinc-300 font-mono">{(reports || []).length} reports · EXIF + SHA256 + consent-gated</div>
        </div>
        <button
          onClick={() => setIsReportModalOpen(true)}
          aria-label={t('villager.submit_report_btn')}
          className="px-3 py-2 bg-white text-zinc-900 rounded-xl text-xs font-black flex items-center gap-1.5 focus-visible:ring-2"
        >
          <FileText className="w-4 h-4" /> {t('reports.submit')}
        </button>
      </div>
      {isOfficer ? (
        <div className="bg-white border-2 border-zinc-200 rounded-2xl p-4">
          <OpsQueuePreview reports={reports} t={t} limit={50} />
        </div>
      ) : (
        <div className="bg-white border-2 border-zinc-200 rounded-2xl p-6 text-center">
          <p className="text-xs text-zinc-600">{t('reports.offlineNote')}</p>
        </div>
      )}
    </main>
  );
}
