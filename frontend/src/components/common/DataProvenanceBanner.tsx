import React from 'react';
import { useEnvironment } from '@/context/EnvironmentContext';
import { AlertTriangle, Database, Info } from 'lucide-react';

export const DataProvenanceBanner: React.FC<{ compact?: boolean }> = ({ compact = false }) => {
  const { isSynthetic, setIsSynthetic, summary, isUnverifiedTest, isVerifiedPilot } = useEnvironment();

  if (isSynthetic === 0 && isVerifiedPilot) {
    return (
      <div className="mb-4 flex items-center justify-between rounded-lg border border-emerald-300 bg-emerald-50/80 px-4 py-2.5 text-xs text-emerald-900 dark:border-emerald-800/80 dark:bg-emerald-950/40 dark:text-emerald-200">
        <div className="flex items-center gap-2">
          <Database className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          <span>
            <strong>Verified Operational Pilot:</strong> Active kitchen measurements recorded and verified in accordance with supervisory audit protocol.
          </span>
        </div>
        <button
          onClick={() => setIsSynthetic(1)}
          className="ml-3 rounded border border-emerald-400 bg-white px-2 py-0.5 text-xs font-medium text-emerald-800 transition hover:bg-emerald-50 dark:border-emerald-700 dark:bg-emerald-900 dark:text-emerald-100"
        >
          Switch to Synthetic Demo
        </button>
      </div>
    );
  }

  if (isUnverifiedTest) {
    return (
      <div className="mb-4 rounded-xl border border-amber-300 bg-amber-50/90 p-3.5 text-amber-950 shadow-xs dark:border-amber-700/80 dark:bg-amber-950/40 dark:text-amber-200">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-2.5">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
            <div>
              <div className="font-semibold text-xs tracking-wide uppercase text-amber-800 dark:text-amber-300">
                🟡 Non-Pilot Data: Unverified Test Entries
              </div>
              <p className="mt-0.5 text-xs leading-relaxed text-amber-900/90 dark:text-amber-200/90">
                Found <strong>{summary?.unverified_test_meals_count || 0} manual test records</strong> in database, but <strong>0 records</strong> have been verified as a real operational pilot. Per data honesty rules, no carbon savings, financial ROI, or pilot success claims may be generated from unverified test entries.
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsSynthetic(1)}
            className="shrink-0 rounded-lg border border-amber-400 bg-white px-2.5 py-1 text-xs font-medium text-amber-900 transition hover:bg-amber-100 dark:border-amber-600 dark:bg-amber-900/60 dark:text-amber-100"
          >
            Switch to Synthetic Benchmark
          </button>
        </div>
      </div>
    );
  }

  // Synthetic demo mode
  if (compact) return null;

  return (
    <div className="mb-4 flex items-center justify-between rounded-lg border border-stone-200 bg-stone-100/70 px-3.5 py-2 text-xs text-stone-700 dark:border-stone-800 dark:bg-stone-900/40 dark:text-stone-300">
      <div className="flex items-center gap-2">
        <Info className="h-3.5 w-3.5 text-stone-500 dark:text-stone-400" />
        <span>
          <strong>Synthetic Benchmark Data (28 historical meals):</strong> Safe demonstration environment reflecting university mess patterns.
        </span>
      </div>
      <button
        onClick={() => setIsSynthetic(0)}
        className="rounded border border-stone-300 bg-white px-2 py-0.5 text-xs font-medium text-stone-800 transition hover:bg-stone-50 dark:border-stone-700 dark:bg-stone-800 dark:text-stone-200"
      >
        View Operational Logs
      </button>
    </div>
  );
};
