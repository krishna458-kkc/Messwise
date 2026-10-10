import React, { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useEnvironment } from '@/context/EnvironmentContext';
import { PageHeader } from '@/components/common/PageHeader';
import { KpiCard } from '@/components/common/KpiCard';
import { DataProvenanceBanner } from '@/components/common/DataProvenanceBanner';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import { BentoCard } from '@/components/common/BentoCard';
import { AnimatedList } from '@/components/animations/AnimatedList';
import { IntelligenceSummary } from '@/lib/types';
import { safeFixed } from '@/lib/formatters';
import {
  BarChart3,
  TrendingDown,
  AlertOctagon,
  Sparkles,
  RefreshCw,
  Scale,
  CheckCircle2,
  Award,
  AlertTriangle,
} from 'lucide-react';

export const WasteIntelligencePage: React.FC = () => {
  const { isSynthetic } = useEnvironment();
  const [data, setData] = useState<IntelligenceSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadIntelligence = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getIntelligenceSummary(isSynthetic);
      setData(res);
    } catch (err: any) {
      console.error('Failed to load waste intelligence:', err);
      setError(err.message || 'Error loading waste intelligence data');
    } finally {
      setLoading(false);
    }
  }, [isSynthetic]);

  useEffect(() => {
    loadIntelligence();
  }, [loadIntelligence]);

  // Filter actual anomalies
  const activeAnomalies = (data?.anomalies || []).filter(
    (a) => a.is_anomaly === true || Math.abs(a.z_score ?? 0) >= (a.threshold ?? 3.5)
  );

  return (
    <div>
      <PageHeader
        title="Waste Intelligence & Root-Cause Analytics"
        subtitle="Operational leftover analytics, anomaly detection, root-cause hypotheses, and dish performance rankings."
        icon={BarChart3}
        actions={
          <button
            onClick={loadIntelligence}
            className="btn-primary"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh Intelligence
          </button>
        }
      />

      <DataProvenanceBanner />

      {error && (
        <div className="mb-6 rounded-2xl border border-red-300 bg-red-50/80 p-4 text-xs text-red-900 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200">
          <div className="flex items-center gap-2 font-bold">
            <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-400" />
            Analytics Query Note:
          </div>
          <p className="mt-1 ml-6">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <LoadingSkeleton className="h-28" count={4} />
          </div>
          <LoadingSkeleton className="h-80" count={2} />
        </div>
      ) : data ? (
        <div className="space-y-6">
          {/* Top KPI Cards with CountUp */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              title="Total Leftovers Measured"
              value={data.kpi?.total_leftover_kg != null ? data.kpi.total_leftover_kg : 0}
              decimals={1}
              unit="kg"
              subtitle={`From ${safeFixed(data.kpi?.total_cooked_kg, 1)} kg cooked`}
              icon={Scale}
              badge={{ text: `${data.kpi?.total_meals_count ?? 0} meals logged`, variant: 'neutral' }}
            />
            <KpiCard
              title="Aggregate Waste Rate"
              value={data.kpi?.waste_percentage != null ? data.kpi.waste_percentage : 0}
              decimals={1}
              unit="%"
              subtitle="Leftover vs cooked mass"
              icon={TrendingDown}
              badge={{
                text: (data.kpi?.waste_percentage ?? 0) < 10 ? 'Healthy' : 'Needs Action',
                variant: (data.kpi?.waste_percentage ?? 0) < 10 ? 'positive' : 'negative',
              }}
            />
            <KpiCard
              title="Forecast Headcount MAE"
              value={data.kpi?.forecast_mae != null ? data.kpi.forecast_mae : '—'}
              decimals={1}
              unit="students"
              subtitle="Mean absolute error"
              icon={BarChart3}
              badge={{
                text: (data.kpi?.forecast_eval_count ?? 0) > 0 ? `${data.kpi.forecast_eval_count} evaluated` : 'Pending actuals',
                variant: 'accent',
              }}
            />
            <KpiCard
              title="Forecast WAPE"
              value={data.kpi?.forecast_wape != null ? `${safeFixed((data.kpi.forecast_wape ?? 0) * 100, 1)}%` : '—'}
              unit=""
              subtitle="Weighted error percentage"
              icon={Sparkles}
              badge={{
                text: 'Conformal validated',
                variant: 'positive',
              }}
            />
          </div>

          {/* Breakdown Bento Grid: Meal Type & Weekday */}
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {/* By Meal Type */}
            <BentoCard>
              <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
                <h3 className="font-display text-base font-bold text-[var(--text-primary)]">
                  Waste by Meal Type
                </h3>
                <span className="text-[11px] text-[var(--text-secondary)] font-semibold">Breakdown</span>
              </div>

              <div className="mt-4 space-y-3">
                {(data.by_meal_type || []).length === 0 ? (
                  <div className="py-4 text-center text-xs text-stone-500">No meal type breakdowns available</div>
                ) : (
                  <AnimatedList>
                    {(data.by_meal_type || []).map((m) => (
                      <div key={m.meal_type} className="flex items-center justify-between rounded-xl bg-[var(--surface-muted)] p-3.5 text-xs transition-colors hover:bg-[var(--border-subtle)]">
                        <div>
                          <span className="font-bold capitalize text-[var(--text-primary)] text-sm">{m.meal_type}</span>
                          <div className="text-[11px] text-[var(--text-secondary)] font-medium">
                            Leftovers: {safeFixed(m.leftover_kg, 1)} kg
                          </div>
                        </div>
                        <span className="font-display text-sm font-extrabold text-[var(--text-primary)] tabular-nums">
                          {safeFixed(m.waste_pct, 1)}% waste
                        </span>
                      </div>
                    ))}
                  </AnimatedList>
                )}
              </div>
            </BentoCard>

            {/* By Weekday */}
            <BentoCard>
              <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
                <h3 className="font-display text-base font-bold text-[var(--text-primary)]">
                  Waste by Day of Week
                </h3>
                <span className="text-[11px] text-[var(--text-secondary)] font-semibold">Day Variance</span>
              </div>

              <div className="mt-4 space-y-3">
                {(data.by_weekday || []).length === 0 ? (
                  <div className="py-4 text-center text-xs text-stone-500">No weekday breakdowns available</div>
                ) : (
                  <AnimatedList>
                    {(data.by_weekday || []).map((w) => (
                      <div key={w.weekday} className="flex items-center justify-between rounded-xl bg-[var(--surface-muted)] p-3.5 text-xs transition-colors hover:bg-[var(--border-subtle)]">
                        <div>
                          <span className="font-bold text-[var(--text-primary)] text-sm">{w.weekday}</span>
                          <div className="text-[11px] text-[var(--text-secondary)] font-medium">
                            Leftovers: {safeFixed(w.leftover_kg, 1)} kg
                          </div>
                        </div>
                        <span className="font-display text-sm font-extrabold text-[var(--text-primary)] tabular-nums">
                          {safeFixed(w.waste_pct, 1)}% waste
                        </span>
                      </div>
                    ))}
                  </AnimatedList>
                )}
              </div>
            </BentoCard>
          </div>

          {/* Anomaly Alerts & Root-Cause Hypotheses */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Anomalies */}
            <div className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
              <div className="flex items-center gap-2 border-b border-[var(--border)] pb-3">
                <AlertOctagon className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                <h3 className="font-display text-base font-bold text-[var(--text-primary)]">
                  Detected Dish Waste Anomalies (Z-Score Threshold)
                </h3>
              </div>

              <div className="mt-4 space-y-3">
                {activeAnomalies.length === 0 ? (
                  <div className="flex items-center gap-2.5 rounded-2xl bg-emerald-50/70 p-4 text-xs font-semibold text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300">
                    <CheckCircle2 className="h-4.5 w-4.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
                    <span>No statistical waste anomalies detected in current window (all within ±3.5σ).</span>
                  </div>
                ) : (
                  <AnimatedList>
                    {activeAnomalies.map((a, i) => (
                      <div
                        key={i}
                        className="rounded-2xl border border-amber-300 bg-amber-50/70 p-4 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-sm text-amber-950 dark:text-amber-100">{a.dish_name}</span>
                          <span className="rounded-full bg-amber-200/90 px-2.5 py-0.5 text-[10px] font-bold uppercase text-amber-900 dark:bg-amber-900/80 dark:text-amber-200">
                            Robust Z: {safeFixed(a.z_score, 1)}
                          </span>
                        </div>
                        <p className="mt-2 text-[11px] leading-relaxed text-amber-900/90 dark:text-amber-200/90 font-medium">
                          <strong>{a.meal_date}</strong> ({a.meal_type}):{' '}
                          {a.explanation ||
                            `Observed waste ${safeFixed(a.observed_waste_pct ?? a.waste_pct, 1)}% vs median ${safeFixed(a.historical_median_pct, 1)}%.`}
                        </p>
                      </div>
                    ))}
                  </AnimatedList>
                )}
              </div>
            </div>

            {/* Root-Cause Hypotheses */}
            <div className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
              <div className="flex items-center gap-2 border-b border-[var(--border)] pb-3">
                <Sparkles className="h-5 w-5 text-emerald-700 dark:text-[#D7F36B]" />
                <h3 className="font-display text-base font-bold text-[var(--text-primary)]">
                  Root-Cause Diagnostic Hypotheses
                </h3>
              </div>

              <div className="mt-4 space-y-3">
                {(data.hypotheses || []).length === 0 ? (
                  <div className="rounded-2xl bg-[var(--surface-muted)] p-5 text-center text-xs text-[var(--text-secondary)] font-medium">
                    No active root-cause hypotheses generated for this period.
                  </div>
                ) : (
                  <AnimatedList>
                    {(data.hypotheses || []).map((h, i) => (
                      <div key={i} className="rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-4 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-[var(--text-primary)] text-sm">{h.hypothesis}</span>
                          <span className="font-display font-extrabold text-emerald-700 dark:text-emerald-400">
                            {Math.round(h.confidence * 100)}% conf
                          </span>
                        </div>
                        <p className="mt-2 text-[11px] text-[var(--text-secondary)] leading-relaxed">
                          <strong>Evidence:</strong> {h.evidence}
                        </p>
                        <p className="mt-2 text-[11px] text-emerald-800 dark:text-emerald-300 font-semibold bg-emerald-50/50 dark:bg-emerald-950/30 p-2 rounded-xl">
                          <strong>Recommended Action:</strong> {h.suggested_action}
                        </p>
                      </div>
                    ))}
                  </AnimatedList>
                )}
              </div>
            </div>
          </div>

          {/* Dish Performance Rankings Panel */}
          {data.rankings && (
            <div className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
              <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
                <div className="flex items-center gap-2">
                  <Award className="h-5 w-5 text-emerald-700 dark:text-[#D7F36B]" />
                  <h3 className="font-display text-base font-bold text-[var(--text-primary)]">
                    Dish-by-Dish Operational Performance Rankings
                  </h3>
                </div>
                <span className="text-xs font-semibold text-[var(--text-secondary)]">
                  {data.rankings.total_dishes_evaluated ?? 0} dishes evaluated
                </span>
              </div>

              <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Highest Waste Dishes */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-amber-800 dark:text-amber-400 mb-3">
                    Highest Leftover Rate Dishes (Optimization Candidates)
                  </h4>
                  <div className="space-y-2">
                    {(data.rankings.highest_waste_dishes || []).slice(0, 4).map((d, idx) => (
                      <div key={idx} className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] p-3 text-xs">
                        <div>
                          <span className="font-bold text-[var(--text-primary)]">{d.dish_name}</span>
                          <span className="ml-2 text-[10px] uppercase text-[var(--text-secondary)]">({d.category})</span>
                          <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">
                            Cooked: {safeFixed(d.total_cooked, 1)} {d.unit || 'kg'} • Leftover: {safeFixed(d.total_leftover, 1)} {d.unit || 'kg'}
                          </div>
                        </div>
                        <span className="font-display text-sm font-extrabold text-amber-700 dark:text-amber-300 tabular-nums">
                          {safeFixed(d.waste_percentage ?? d.waste_pct, 1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Operational Performers */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-800 dark:text-emerald-400 mb-3">
                    Balanced Clearance Performers (Optimal Portions)
                  </h4>
                  <div className="space-y-2">
                    {(data.rankings.operational_performers || []).slice(0, 4).map((d, idx) => (
                      <div key={idx} className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] p-3 text-xs">
                        <div>
                          <span className="font-bold text-[var(--text-primary)]">{d.dish_name}</span>
                          <span className="ml-2 text-[10px] uppercase text-[var(--text-secondary)]">({d.category})</span>
                          <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">
                            Cooked: {safeFixed(d.total_cooked, 1)} {d.unit || 'kg'} • Leftover: {safeFixed(d.total_leftover, 1)} {d.unit || 'kg'}
                          </div>
                        </div>
                        <span className="font-display text-sm font-extrabold text-emerald-700 dark:text-emerald-400 tabular-nums">
                          {safeFixed(d.waste_percentage ?? d.waste_pct, 1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {data.rankings.data_limitation_note && (
                <div className="mt-4 rounded-xl bg-[var(--surface-muted)] p-3 text-[11px] text-[var(--text-secondary)] font-medium leading-relaxed">
                  {data.rankings.data_limitation_note}
                </div>
              )}
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
};
