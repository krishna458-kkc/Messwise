import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useEnvironment } from '@/context/EnvironmentContext';
import { PageHeader } from '@/components/common/PageHeader';
import { DataProvenanceBanner } from '@/components/common/DataProvenanceBanner';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import { BentoCard } from '@/components/common/BentoCard';
import { PilotEvidenceReport, AuditEvent } from '@/lib/types';
import {
  FileText,
  ShieldCheck,
  Download,
  AlertTriangle,
  RefreshCw,
  CheckCircle2,
  Clock,
} from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const { isSynthetic, isVerifiedPilot, summary } = useEnvironment();
  const [report, setReport] = useState<PilotEvidenceReport | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Date filters for E2 Matched Pair
  const [bStart, setBStart] = useState<string>('2026-10-01');
  const [bEnd, setBEnd] = useState<string>('2026-10-04');
  const [pStart, setPStart] = useState<string>('2026-10-05');
  const [pEnd, setPEnd] = useState<string>('2026-10-07');

  const loadReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const [eData, aData] = await Promise.all([
        api.getEvidenceReport({
          is_synthetic: isSynthetic,
          baseline_start: bStart,
          baseline_end: bEnd,
          pilot_start: pStart,
          pilot_end: pEnd,
        }),
        api.getAuditEvents(30),
      ]);
      setReport(eData);
      setAuditEvents(aData.events || []);
    } catch (err: any) {
      console.error('Failed to load reports & audit data:', err);
      setError(err.message || 'Error loading governance report');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, [isSynthetic, bStart, bEnd, pStart, pEnd]);

  return (
    <div>
      <PageHeader
        title="Reports & Audit Governance"
        subtitle="Module E2 before/after matched-pair statistical evaluation and immutable supervisory audit trail."
        icon={FileText}
        actions={
          <button
            onClick={loadReports}
            className="flex items-center gap-2 rounded-xl bg-[#173D32] px-4 py-2 text-xs font-semibold text-white shadow-xs transition hover:bg-[#102C24] dark:bg-[#D7F36B] dark:text-[#102C24]"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Recalculate E2 Evaluation
          </button>
        }
      />

      <DataProvenanceBanner />

      {/* Strict Provenance Banner for Unverified Records */}
      {isSynthetic === 0 && !isVerifiedPilot && (
        <div className="mb-6 rounded-2xl border border-amber-300 bg-amber-50/90 p-5 text-amber-950 dark:border-amber-700/80 dark:bg-amber-950/40 dark:text-amber-200">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="font-display text-sm font-bold uppercase tracking-wider text-amber-900 dark:text-amber-100">
                Insufficient Verified Pilot Data (0 Verified Meals)
              </h3>
              <p className="mt-1 text-xs leading-relaxed text-amber-900/90 dark:text-amber-200/90">
                The database contains <strong>{summary?.unverified_test_meals_count || 0} unverified developer test records</strong>, but <strong>0 verified pilot records</strong>. The formal Pilot Evidence Report (E2) cannot evaluate statistical significance or real-world savings until verified kitchen records are logged under protocol.
              </p>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="mb-6 rounded-xl border border-red-300 bg-red-50 p-4 text-xs text-red-900 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          <div className="font-semibold">Reports calculation note:</div>
          <p className="mt-1">{error}</p>
        </div>
      )}

      {/* Date Window Parameter Box */}
      <div className="mb-6 rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
        <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)]">
          E2 Matched-Pair Evaluation Windows
        </span>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)]">Baseline Window Start</label>
            <input
              type="date"
              value={bStart}
              onChange={(e) => setBStart(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs font-medium focus:outline-hidden"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)]">Baseline Window End</label>
            <input
              type="date"
              value={bEnd}
              onChange={(e) => setBEnd(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs font-medium focus:outline-hidden"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)]">Pilot Window Start</label>
            <input
              type="date"
              value={pStart}
              onChange={(e) => setPStart(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs font-medium focus:outline-hidden"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)]">Pilot Window End</label>
            <input
              type="date"
              value={pEnd}
              onChange={(e) => setPEnd(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs font-medium focus:outline-hidden"
            />
          </div>
        </div>
      </div>

      {loading ? (
        <LoadingSkeleton className="h-64" count={2} />
      ) : (
        <div className="space-y-6">
          {/* E2 Matched Pair Results Panel */}
          {report && (
            <BentoCard>
              <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-[#173D32] dark:text-[#D7F36B]">
                    Statistical Matched-Pair Evaluation
                  </span>
                  <h3 className="mt-1 font-display text-xl font-bold text-[var(--text-primary)]">
                    Module E2: Before vs After Dining Comparison
                  </h3>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold border ${
                    report.has_sufficient_data
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800'
                      : 'bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800'
                  }`}
                >
                  {report.has_sufficient_data ? 'Sufficient Sample Size' : 'Data Collection in Progress'}
                </span>
              </div>

              <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3 text-center">
                <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-5">
                  <span className="text-[11px] font-semibold text-[var(--text-secondary)] uppercase">
                    Baseline Sample Meals
                  </span>
                  <div className="mt-2 font-display text-3xl font-extrabold text-[var(--text-primary)] tabular-nums">
                    {report.baseline_meals_count}
                  </div>
                  <span className="mt-1 text-[11px] text-stone-500">Pre-intervention period</span>
                </div>

                <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-5">
                  <span className="text-[11px] font-semibold text-[var(--text-secondary)] uppercase">
                    Pilot Sample Meals
                  </span>
                  <div className="mt-2 font-display text-3xl font-extrabold text-[var(--text-primary)] tabular-nums">
                    {report.pilot_meals_count}
                  </div>
                  <span className="mt-1 text-[11px] text-stone-500">Post-MessWise deployment</span>
                </div>

                <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-5">
                  <span className="text-[11px] font-semibold text-[var(--text-secondary)] uppercase">
                    Waste Reduction
                  </span>
                  <div className="mt-2 font-display text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 tabular-nums">
                    {report.waste_reduction_pct != null ? `${report.waste_reduction_pct.toFixed(1)}%` : '—'}
                  </div>
                  <span className="mt-1 text-[11px] text-stone-500">
                    {report.is_statistically_significant ? 'p < 0.05 (Significant)' : 'Awaiting power'}
                  </span>
                </div>
              </div>

              <div className="mt-4 rounded-xl bg-[var(--surface-muted)] p-3.5 text-xs text-[var(--text-secondary)]">
                <strong>Status Message:</strong> {report.status_message}
              </div>
            </BentoCard>
          )}

          {/* Module I: Immutable Audit Trail */}
          <div className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
              <div>
                <h3 className="font-display text-base font-bold text-[var(--text-primary)]">
                  Module I: Immutable Supervisory Audit Trail
                </h3>
                <p className="text-xs text-[var(--text-secondary)]">
                  Cryptographically ordered events recording overrides, plan freeze decisions, and kitchen actions
                </p>
              </div>
              <span className="text-xs font-semibold text-stone-500">
                {auditEvents.length} events logged
              </span>
            </div>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[var(--border)] text-[var(--text-secondary)]">
                    <th className="py-2.5 font-medium">Event ID</th>
                    <th className="py-2.5 font-medium">Timestamp</th>
                    <th className="py-2.5 font-medium">Actor</th>
                    <th className="py-2.5 font-medium">Action</th>
                    <th className="py-2.5 font-medium">Prior State</th>
                    <th className="py-2.5 font-medium">New State</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {auditEvents.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-stone-500">
                        No audit events recorded yet.
                      </td>
                    </tr>
                  ) : (
                    auditEvents.map((evt) => (
                      <tr key={evt.id} className="hover:bg-[var(--surface-muted)] transition">
                        <td className="py-3 font-semibold text-[var(--text-primary)] tabular-nums">#{evt.id}</td>
                        <td className="py-3 text-[var(--text-secondary)]">
                          {evt.ts ? new Date(evt.ts).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : '—'}
                        </td>
                        <td className="py-3 font-semibold text-[var(--text-primary)]">{evt.who || 'system'}</td>
                        <td className="py-3">
                          <span className="rounded-md bg-[var(--surface-muted)] px-2 py-0.5 text-[11px] font-semibold text-[#173D32] dark:text-[#D7F36B]">
                            {evt.action}
                          </span>
                        </td>
                        <td className="py-3 text-[var(--text-secondary)] truncate max-w-xs">{evt.old_value || '—'}</td>
                        <td className="py-3 font-medium text-[var(--text-primary)] truncate max-w-xs">{evt.new_value || '—'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
