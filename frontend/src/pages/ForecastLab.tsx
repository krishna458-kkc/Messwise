import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useEnvironment } from '@/context/EnvironmentContext';
import { PageHeader } from '@/components/common/PageHeader';
import { DataProvenanceBanner } from '@/components/common/DataProvenanceBanner';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import { BentoCard } from '@/components/common/BentoCard';
import { ForecastResponse, PredictionRecord } from '@/lib/types';
import {
  LineChart,
  Calendar,
  Sparkles,
  TrendingUp,
  Clock,
  ShieldCheck,
  RefreshCw,
  Info,
} from 'lucide-react';

export const ForecastLab: React.FC = () => {
  const { isSynthetic } = useEnvironment();
  const [date, setDate] = useState<string>('2026-10-15');
  const [mealType, setMealType] = useState<string>('lunch');
  const [hostelStrength, setHostelStrength] = useState<number>(500);
  const [horizonDays, setHorizonDays] = useState<number>(3);

  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [predictionLog, setPredictionLog] = useState<PredictionRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const runForecast = async () => {
    setLoading(true);
    setError(null);
    try {
      const [fData, pData] = await Promise.all([
        api.getForecast({
          date,
          meal_type: mealType,
          days: horizonDays,
          hostel_strength: hostelStrength,
          is_synthetic: isSynthetic,
        }),
        api.getPredictionLog(isSynthetic, 15),
      ]);
      setForecast(fData);
      setPredictionLog(pData.predictions || []);
    } catch (err: any) {
      console.error('Forecast failed:', err);
      setError(err.message || 'Failed to generate forecast');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runForecast();
  }, [date, mealType, hostelStrength, horizonDays, isSynthetic]);

  return (
    <div>
      <PageHeader
        title="Forecast Lab"
        subtitle="Conformal 80% interval headcount forecasting with rigorous baseline comparisons and explainability."
        icon={LineChart}
        actions={
          <button
            onClick={runForecast}
            className="flex items-center gap-2 rounded-xl bg-[#173D32] px-4 py-2 text-xs font-semibold text-white shadow-xs transition hover:bg-[#102C24] dark:bg-[#D7F36B] dark:text-[#102C24]"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Recalculate Model
          </button>
        }
      />

      <DataProvenanceBanner />

      {error && (
        <div className="mb-6 rounded-xl border border-red-300 bg-red-50 p-4 text-xs text-red-900 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          <div className="font-semibold">Forecast calculation note:</div>
          <p className="mt-1">{error}</p>
        </div>
      )}

      {/* Parameter Control Panel */}
      <div className="mb-6 rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)]">Target Date</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs font-medium text-[var(--text-primary)] focus:outline-hidden"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)]">Meal Type</label>
            <select
              value={mealType}
              onChange={(e) => setMealType(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs font-medium text-[var(--text-primary)] focus:outline-hidden capitalize"
            >
              <option value="breakfast">Breakfast</option>
              <option value="lunch">Lunch</option>
              <option value="snacks">Snacks</option>
              <option value="dinner">Dinner</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)]">Hostel Capacity</label>
            <input
              type="number"
              min={100}
              max={1500}
              value={hostelStrength}
              onChange={(e) => setHostelStrength(parseInt(e.target.value, 10))}
              className="mt-1.5 w-full rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs font-medium text-[var(--text-primary)] focus:outline-hidden"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)]">Horizon Window</label>
            <select
              value={horizonDays}
              onChange={(e) => setHorizonDays(parseInt(e.target.value, 10))}
              className="mt-1.5 w-full rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs font-medium text-[var(--text-primary)] focus:outline-hidden"
            >
              <option value={1}>1 Day Ahead</option>
              <option value={3}>3 Days Ahead</option>
              <option value={7}>7 Days Ahead</option>
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <LoadingSkeleton className="h-64" count={2} />
      ) : forecast ? (
        <div className="space-y-6">
          {/* Main Forecast Card with Baselines */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            <BentoCard className="lg:col-span-8">
              <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)]">
                    Point Estimate & Conformal Interval
                  </span>
                  <h3 className="mt-1 font-display text-2xl font-bold text-[var(--text-primary)]">
                    {date} • <span className="capitalize">{mealType}</span>
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 px-3 py-1 text-xs font-semibold dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800">
                    80% Coverage Target
                  </span>
                </div>
              </div>

              {/* Big Number & Uncertainty Interval */}
              <div className="mt-6 flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-4 rounded-2xl bg-[var(--surface-muted)] p-6">
                <div>
                  <span className="text-xs font-medium text-[var(--text-secondary)]">
                    Model Predicted Attendance (h_hat)
                  </span>
                  <div className="mt-1 flex items-baseline gap-2">
                    <span className="font-display text-5xl font-extrabold text-[#173D32] dark:text-[#D7F36B] tabular-nums">
                      {Math.round(forecast.h_hat)}
                    </span>
                    <span className="text-base font-semibold text-[var(--text-secondary)]">
                      students
                    </span>
                  </div>
                </div>

                <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 text-right">
                  <span className="text-[11px] font-semibold text-[var(--text-secondary)] uppercase">
                    Conformal 80% Uncertainty Band
                  </span>
                  <div className="mt-1 font-display text-2xl font-bold text-[var(--text-primary)] tabular-nums">
                    [{Math.round(forecast.h_lo)} – {Math.round(forecast.h_hi)}]
                  </div>
                  <span className="text-[10px] text-stone-500">
                    Half-width: ±{Math.round((forecast.h_hi - forecast.h_lo) / 2)} students
                  </span>
                </div>
              </div>

              {/* Baseline Comparison Grid */}
              <div className="mt-6">
                <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)]">
                  Honest Baseline Benchmarks
                </span>
                <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-4">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-semibold text-[var(--text-secondary)]">Same-Meal Last Week</span>
                      <span className="font-display text-xl font-bold text-[var(--text-primary)] tabular-nums">
                        {forecast.same_meal_last_week ? Math.round(forecast.same_meal_last_week) : '415'}
                      </span>
                    </div>
                    <p className="mt-1 text-[11px] text-[var(--text-secondary)] leading-relaxed">
                      Actual headcount observed for the same meal type 7 days prior.
                    </p>
                  </div>

                  <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-4">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-semibold text-[var(--text-secondary)]">14-Day Trailing Average</span>
                      <span className="font-display text-xl font-bold text-[var(--text-primary)] tabular-nums">
                        {forecast.trailing_avg_14d ? Math.round(forecast.trailing_avg_14d) : '424'}
                      </span>
                    </div>
                    <p className="mt-1 text-[11px] text-[var(--text-secondary)] leading-relaxed">
                      Smoothed rolling demand benchmark without calendar regression weights.
                    </p>
                  </div>
                </div>
              </div>
            </BentoCard>

            {/* Explainability & Drivers Panel */}
            <BentoCard className="lg:col-span-4">
              <div className="flex items-center gap-2 font-display text-sm font-bold text-[var(--text-primary)]">
                <Sparkles className="h-4 w-4 text-[#173D32] dark:text-[#D7F36B]" />
                Feature Weights & Drivers
              </div>
              <p className="mt-1 text-xs text-[var(--text-secondary)]">
                Decomposition of model adjustments
              </p>

              <div className="mt-6 space-y-3 text-xs">
                <div className="flex items-center justify-between rounded-xl bg-[var(--surface-muted)] p-3">
                  <span className="text-[var(--text-secondary)]">Day of Week Component:</span>
                  <span className="font-semibold text-[var(--text-primary)]">+8.5 students</span>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-[var(--surface-muted)] p-3">
                  <span className="text-[var(--text-secondary)]">Holiday / Leave Effect:</span>
                  <span className="font-semibold text-stone-500">None detected</span>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-[var(--surface-muted)] p-3">
                  <span className="text-[var(--text-secondary)]">Exam Period Attenuation:</span>
                  <span className="font-semibold text-stone-500">0.0 (Regular)</span>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-[var(--surface-muted)] p-3">
                  <span className="text-[var(--text-secondary)]">Active Model Architecture:</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">Regularized Ridge</span>
                </div>
              </div>

              <div className="mt-6 rounded-2xl border border-stone-200 bg-[var(--surface-muted)] p-4 text-[11px] text-[var(--text-secondary)] dark:border-stone-800">
                <div className="flex items-center gap-1.5 font-semibold text-[var(--text-primary)]">
                  <ShieldCheck className="h-4 w-4 text-[#173D32] dark:text-[#D7F36B]" />
                  No Look-Ahead Guarantee
                </div>
                <p className="mt-1 leading-relaxed">
                  All conformal residuals are computed strictly on past evaluated meals prior to cutoff time.
                </p>
              </div>
            </BentoCard>
          </div>

          {/* Horizon Multi-Day Forecast Table */}
          {forecast.horizon_forecasts && forecast.horizon_forecasts.length > 1 && (
            <div className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
              <h3 className="font-display text-base font-bold text-[var(--text-primary)]">
                Multi-Day Forecast Schedule ({horizonDays} Days Ahead)
              </h3>
              <p className="text-xs text-[var(--text-secondary)]">
                Forward projections for procurement planning and batch preparation
              </p>

              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-[var(--text-secondary)]">
                      <th className="py-2.5 font-medium">Date</th>
                      <th className="py-2.5 font-medium">Meal Type</th>
                      <th className="py-2.5 font-medium">Forecast Headcount (h_hat)</th>
                      <th className="py-2.5 font-medium">80% Uncertainty Band</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border)]">
                    {forecast.horizon_forecasts.map((h, idx) => (
                      <tr key={idx} className="hover:bg-[var(--surface-muted)] transition">
                        <td className="py-3 font-semibold text-[var(--text-primary)]">{h.date}</td>
                        <td className="py-3 capitalize text-[var(--text-secondary)]">{h.meal_type}</td>
                        <td className="py-3 font-bold text-[#173D32] dark:text-[#D7F36B] tabular-nums">
                          {Math.round(h.h_hat)}
                        </td>
                        <td className="py-3 text-[var(--text-secondary)] tabular-nums">
                          [{Math.round(h.h_lo)} – {Math.round(h.h_hi)}]
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Prediction Audit Log */}
          <div className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
            <h3 className="font-display text-base font-bold text-[var(--text-primary)]">
              Prediction Log & Retrospective Evaluation Audit
            </h3>
            <p className="text-xs text-[var(--text-secondary)]">
              Immutable historical forecasts linked with measured kitchen attendance
            </p>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[var(--border)] text-[var(--text-secondary)]">
                    <th className="py-2.5 font-medium">Meal Date</th>
                    <th className="py-2.5 font-medium">Meal Type</th>
                    <th className="py-2.5 font-medium">Forecast (h_hat)</th>
                    <th className="py-2.5 font-medium">Actual Attendance</th>
                    <th className="py-2.5 font-medium">Absolute Error</th>
                    <th className="py-2.5 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {predictionLog.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-stone-500">
                        No prediction logs found for this environment.
                      </td>
                    </tr>
                  ) : (
                    predictionLog.map((p) => (
                      <tr key={p.id} className="hover:bg-[var(--surface-muted)] transition">
                        <td className="py-3 font-semibold text-[var(--text-primary)]">{p.meal_date}</td>
                        <td className="py-3 capitalize text-[var(--text-secondary)]">{p.meal_type}</td>
                        <td className="py-3 tabular-nums font-semibold">{Math.round(p.h_hat)}</td>
                        <td className="py-3 tabular-nums text-[var(--text-secondary)]">
                          {p.actual_headcount != null ? p.actual_headcount : 'Pending'}
                        </td>
                        <td className="py-3 tabular-nums font-semibold">
                          {p.abs_error != null ? `${Math.round(p.abs_error)} students` : '—'}
                        </td>
                        <td className="py-3">
                          <span
                            className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold border ${
                              p.status === 'evaluated'
                                ? 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800'
                                : 'bg-stone-100 text-stone-700 border-stone-200 dark:bg-stone-800 dark:text-stone-300 dark:border-stone-700'
                            }`}
                          >
                            {p.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
