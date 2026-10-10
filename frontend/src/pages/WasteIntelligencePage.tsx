import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useEnvironment } from '@/context/EnvironmentContext';
import { PageHeader } from '@/components/common/PageHeader';
import { KpiCard } from '@/components/common/KpiCard';
import { DataProvenanceBanner } from '@/components/common/DataProvenanceBanner';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import { BentoCard } from '@/components/common/BentoCard';
import { IntelligenceSummary } from '@/lib/types';
import {
  BarChart3,
  TrendingDown,
  AlertOctagon,
  Sparkles,
  RefreshCw,
  Scale,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';

export const WasteIntelligencePage: React.FC = () => {
  const { isSynthetic } = useEnvironment();
  const [data, setData] = useState<IntelligenceSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadIntelligence = async () => {
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
  };

  useEffect(() => {
    loadIntelligence();
  }, [isSynthetic]);

  return (
    <div>
      <PageHeader
        title="Waste Intelligence & Root-Cause Analytics"
        subtitle="Operational leftover analytics, anomaly detection, root-cause hypotheses, and dish performance rankings."
        icon={BarChart3}
        actions={
          <button
            onClick={loadIntelligence}
            className="flex items-center gap-2 rounded-xl bg-[#173D32] px-4 py-2 text-xs font-semibold text-white shadow-xs transition hover:bg-[#102C24] dark:bg-[#D7F36B] dark:text-[#102C24]"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh Intelligence
          </button>
        }
      />

      <DataProvenanceBanner />

      {error && (
        <div className="mb-6 rounded-xl border border-red-300 bg-red-50 p-4 text-xs text-red-900 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          <div className="font-semibold">Analytics query note:</div>
          <p className="mt-1">{error}</p>
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
          {/* Top KPI Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              title="Total Leftovers Measured"
              value={data.kpi.total_leftover_kg ? data.kpi.total_leftover_kg.toFixed(1) : '0.0'}
              unit="kg"
              subtitle={`From ${data.kpi.total_cooked_kg ? data.kpi.total_cooked_kg.toFixed(1) : '0.0'} kg cooked`}
              icon={Scale}
              badge={{ text: `${data.kpi.total_meals_count} meals logged`, variant: 'neutral' }}
            />
            <KpiCard
              title="Aggregate Waste Rate"
              value={data.kpi.waste_percentage ? data.kpi.waste_percentage.toFixed(1) : '0.0'}
              unit="%"
              subtitle="Leftover vs cooked mass"
              icon={TrendingDown}
              badge={{
                text: data.kpi.waste_percentage < 10 ? 'Healthy' : 'Needs Action',
                variant: data.kpi.waste_percentage < 10 ? 'positive' : 'negative',
              }}
            />
            <KpiCard
              title="Forecast Headcount MAE"
              value={data.kpi.forecast_mae != null ? data.kpi.forecast_mae.toFixed(1) : '—'}
              unit="students"
              subtitle="Mean absolute error"
              icon={BarChart3}
              badge={{
                text: data.kpi.forecast_eval_count > 0 ? `${data.kpi.forecast_eval_count} evaluated` : 'Pending actuals',
                variant: 'accent',
              }}
            />
            <KpiCard
              title="Forecast WAPE"
              value={data.kpi.forecast_wape != null ? `${(data.kpi.forecast_wape * 100).toFixed(1)}%` : '—'}
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
                <h3 className="font-display text-sm font-bold text-[var(--text-primary)]">
                  Waste by Meal Type
                </h3>
                <span className="text-[11px] text-[var(--text-secondary)] font-medium">Breakdown</span>
              </div>

              <div className="mt-4 space-y-3">
                {data.by_meal_type.length === 0 ? (
                  <div className="py-4 text-center text-xs text-stone-500">No meal type breakdowns available</div>
                ) : (
                  data.by_meal_type.map((m) => (
                    <div key={m.meal_type} className="flex items-center justify-between rounded-xl bg-[var(--surface-muted)] p-3 text-xs">
                      <div>
                        <span className="font-semibold capitalize text-[var(--text-primary)]">{m.meal_type}</span>
                        <div className="text-[10px] text-[var(--text-secondary)]">
                          Leftovers: {m.leftover_kg ? m.leftover_kg.toFixed(1) : 0} kg
                        </div>
                      </div>
                      <span className="font-display text-sm font-bold text-stone-700 dark:text-stone-300 tabular-nums">
                        {m.waste_pct ? m.waste_pct.toFixed(1) : 0}% waste
                      </span>
                    </div>
                  ))
                )}
              </div>
            </BentoCard>

            {/* By Weekday */}
            <BentoCard>
              <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
                <h3 className="font-display text-sm font-bold text-[var(--text-primary)]">
                  Waste by Day of Week
                </h3>
                <span className="text-[11px] text-[var(--text-secondary)] font-medium">Day Variance</span>
              </div>

              <div className="mt-4 space-y-3">
                {data.by_weekday.length === 0 ? (
                  <div className="py-4 text-center text-xs text-stone-500">No weekday breakdowns available</div>
                ) : (
                  data.by_weekday.map((w) => (
                    <div key={w.weekday} className="flex items-center justify-between rounded-xl bg-[var(--surface-muted)] p-3 text-xs">
                      <div>
                        <span className="font-semibold text-[var(--text-primary)]">{w.weekday}</span>
                        <div className="text-[10px] text-[var(--text-secondary)]">
                          Leftovers: {w.leftover_kg ? w.leftover_kg.toFixed(1) : 0} kg
                        </div>
                      </div>
                      <span className="font-display text-sm font-bold text-stone-700 dark:text-stone-300 tabular-nums">
                        {w.waste_pct ? w.waste_pct.toFixed(1) : 0}% waste
                      </span>
                    </div>
                  ))
                )}
              </div>
            </BentoCard>
          </div>

          {/* Anomaly Alerts & Root-Cause Hypotheses */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Anomalies */}
            <div className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
              <div className="flex items-center gap-2 border-b border-[var(--border)] pb-3">
                <AlertOctagon className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                <h3 className="font-display text-sm font-bold text-[var(--text-primary)]">
                  Detected Dish Waste Anomalies (Z-Score Threshold)
                </h3>
              </div>

              <div className="mt-4 space-y-3">
                {data.anomalies.length === 0 ? (
                  <div className="flex items-center gap-2 py-4 text-xs text-emerald-700 dark:text-emerald-400">
                    <CheckCircle2 className="h-4 w-4" />
                    <span>No statistical waste anomalies detected in current window (all within ±2σ).</span>
                  </div>
                ) : (
                  data.anomalies.map((a, i) => (
                    <div
                      key={i}
                      className="rounded-xl border border-amber-200 bg-amber-50/60 p-3.5 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold">{a.dish_name}</span>
                        <span className="rounded-full bg-amber-200/80 px-2 py-0.5 text-[10px] font-bold uppercase text-amber-900">
                          {a.severity} (Z: {a.z_score.toFixed(1)})
                        </span>
                      </div>
                      <p className="mt-1 text-[11px] leading-relaxed">
                        {a.meal_date} ({a.meal_type}): {a.leftover_kg.toFixed(1)} kg leftover ({a.waste_pct.toFixed(1)}%). {a.message}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Root-Cause Hypotheses */}
            <div className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
              <div className="flex items-center gap-2 border-b border-[var(--border)] pb-3">
                <Sparkles className="h-4 w-4 text-[#173D32] dark:text-[#D7F36B]" />
                <h3 className="font-display text-sm font-bold text-[var(--text-primary)]">
                  Root-Cause Diagnostic Hypotheses
                </h3>
              </div>

              <div className="mt-4 space-y-3">
                {data.hypotheses.length === 0 ? (
                  <div className="py-4 text-center text-xs text-stone-500">
                    No active root-cause hypotheses generated for this period.
                  </div>
                ) : (
                  data.hypotheses.map((h, i) => (
                    <div key={i} className="rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] p-3.5 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-[var(--text-primary)]">{h.hypothesis}</span>
                        <span className="font-display font-bold text-emerald-600 dark:text-emerald-400">
                          {Math.round(h.confidence * 100)}% conf
                        </span>
                      </div>
                      <p className="mt-1 text-[11px] text-[var(--text-secondary)] leading-relaxed">
                        <strong>Evidence:</strong> {h.evidence}
                      </p>
                      <p className="mt-1 text-[11px] text-[#173D32] dark:text-[#D7F36B] font-medium">
                        <strong>Action:</strong> {h.suggested_action}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
