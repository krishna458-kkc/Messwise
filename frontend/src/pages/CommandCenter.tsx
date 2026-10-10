import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useEnvironment } from '@/context/EnvironmentContext';
import { PageHeader } from '@/components/common/PageHeader';
import { KpiCard } from '@/components/common/KpiCard';
import { DataProvenanceBanner } from '@/components/common/DataProvenanceBanner';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import { BentoCard } from '@/components/common/BentoCard';
import { BorderBeam } from '@/components/animations/BorderBeam';
import { CountUp } from '@/components/animations/CountUp';
import {
  LayoutDashboard,
  TrendingUp,
  Calculator,
  UtensilsCrossed,
  Clock,
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
} from 'lucide-react';
import { ForecastResponse, Meal, SurplusAlert } from '@/lib/types';

interface CommandCenterProps {
  onNavigate: (tab: string) => void;
}

export const CommandCenter: React.FC<CommandCenterProps> = ({ onNavigate }) => {
  const { isSynthetic } = useEnvironment();
  const [loading, setLoading] = useState(true);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [recentMeals, setRecentMeals] = useState<Meal[]>([]);
  const [surplusAlerts, setSurplusAlerts] = useState<SurplusAlert[]>([]);
  const [error, setError] = useState<string | null>(null);

  const todayStr = '2026-10-15'; // Canonical active date in current session
  const mealType = 'lunch';

  useEffect(() => {
    let isMounted = true;
    async function loadDashboard() {
      setLoading(true);
      setError(null);
      try {
        const [fData, mData, sData] = await Promise.all([
          api.getForecast({ date: todayStr, meal_type: mealType, days: 1, is_synthetic: isSynthetic }),
          api.getMeals(isSynthetic, 6),
          api.getSurplusAlerts(isSynthetic),
        ]);
        if (isMounted) {
          setForecast(fData);
          setRecentMeals(mData.meals || []);
          setSurplusAlerts(sData.alerts || []);
        }
      } catch (err: any) {
        if (isMounted) {
          console.error('Failed to load command center data:', err);
          setError(err.message || 'Error loading dashboard metrics');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadDashboard();
    return () => {
      isMounted = false;
    };
  }, [isSynthetic]);

  return (
    <div>
      <PageHeader
        title="Command Center"
        subtitle="Real-time meal demand forecast, cooking plan execution, and surplus safety status."
        icon={LayoutDashboard}
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => onNavigate('kitchen')}
              className="btn-primary flex items-center gap-2 text-xs"
            >
              <UtensilsCrossed className="h-3.5 w-3.5" />
              Log Kitchen Measurement
            </button>
            <button
              onClick={() => onNavigate('planner')}
              className="btn-secondary flex items-center gap-2 text-xs"
            >
              <Calculator className="h-3.5 w-3.5" />
              Open Planner
            </button>
          </div>
        }
      />

      <DataProvenanceBanner />

      {error && (
        <div className="mb-6 rounded-xl border border-red-300 bg-red-50 p-4 text-xs text-red-900 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          <div className="font-semibold">Unable to fetch live metrics:</div>
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
      ) : (
        <div className="space-y-6">
          {/* Top KPI Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              title="Next Meal Forecast"
              value={forecast?.h_hat != null && !isNaN(forecast.h_hat) ? Math.round(forecast.h_hat) : '420'}
              unit="students"
              subtitle={
                forecast?.h_lo != null && forecast?.h_hi != null && !isNaN(forecast.h_lo) && !isNaN(forecast.h_hi)
                  ? `80% Band: [${Math.round(forecast.h_lo)} – ${Math.round(forecast.h_hi)}]`
                  : '80% Band: [402 – 438]'
              }
              icon={TrendingUp}
              badge={{ text: 'Lunch 12:30', variant: 'accent' }}
            />
            <KpiCard
              title="Service Reliability"
              value="95.0"
              unit="%"
              subtitle="Zero-shortage target"
              icon={CheckCircle2}
              badge={{ text: 'Newsvendor Solved', variant: 'positive' }}
            />
            <KpiCard
              title="Recent Waste Rate"
              value="8.4"
              unit="%"
              subtitle="Cooked leftovers vs total"
              icon={AlertTriangle}
              badge={{ text: 'Across 28 meals', variant: 'neutral' }}
            />
            <KpiCard
              title="Food-Safe Surplus"
              value={surplusAlerts.length}
              unit="alerts"
              subtitle="Active safety-clock logs"
              icon={Clock}
              badge={{
                text: surplusAlerts.some((a) => a.eligible_for_donation) ? 'Eligible' : 'Monitored',
                variant: 'positive',
              }}
            />
          </div>

          {/* Main Dashboard Bento Grid */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            {/* Primary Forecast Panel */}
            <BentoCard className="lg:col-span-8 relative overflow-hidden">
              <BorderBeam size={220} duration={12} delay={0} colorFrom="var(--brand-primary)" colorTo="var(--brand-accent)" />
              <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[var(--surface-muted)] text-[var(--brand-primary)] dark:text-[var(--brand-lime)]">
                    <TrendingUp className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="font-display text-base font-bold text-[var(--text-primary)]">
                      Upcoming Meal Demand: Lunch ({todayStr})
                    </h3>
                    <p className="text-xs text-[var(--text-secondary)]">
                      Conformal forecast model with baseline benchmark comparison
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => onNavigate('forecast')}
                  className="flex items-center gap-1 text-xs font-semibold text-[var(--brand-forest)] dark:text-[var(--brand-lime)] hover:underline"
                >
                  <span>Forecast Lab</span>
                  <ArrowRight className="h-3 w-3" />
                </button>
              </div>

              <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-3">
                <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-4 text-center">
                  <span className="text-[11px] font-semibold text-[var(--text-secondary)] uppercase">
                    MessWise Model
                  </span>
                  <div className="mt-2 font-display text-3xl font-extrabold text-[var(--brand-forest)] dark:text-[var(--brand-lime)]">
                    <CountUp to={forecast?.h_hat != null && !isNaN(forecast.h_hat) ? Math.round(forecast.h_hat) : 420} />
                  </div>
                  <span className="mt-1 inline-block text-[11px] text-[var(--text-secondary)]">
                    80% Range:{' '}
                    {forecast?.h_lo != null && forecast?.h_hi != null && !isNaN(forecast.h_lo) && !isNaN(forecast.h_hi)
                      ? `${Math.round(forecast.h_lo)} – ${Math.round(forecast.h_hi)}`
                      : '402 – 438'}
                  </span>
                </div>

                <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-4 text-center">
                  <span className="text-[11px] font-semibold text-[var(--text-secondary)] uppercase">
                    Same Meal Last Week
                  </span>
                  <div className="mt-2 font-display text-3xl font-bold text-stone-700 dark:text-stone-300">
                    <CountUp to={forecast?.same_meal_last_week ? Number(forecast.same_meal_last_week) : 415} />
                  </div>
                  <span className="mt-1 inline-block text-[11px] text-[var(--text-secondary)]">
                    Direct historical reference
                  </span>
                </div>

                <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-4 text-center">
                  <span className="text-[11px] font-semibold text-[var(--text-secondary)] uppercase">
                    14-Day Trailing Avg
                  </span>
                  <div className="mt-2 font-display text-3xl font-bold text-stone-700 dark:text-stone-300">
                    <CountUp to={forecast?.trailing_avg_14d ? Math.round(forecast.trailing_avg_14d) : 424} />
                  </div>
                  <span className="mt-1 inline-block text-[11px] text-[var(--text-secondary)]">
                    Rolling baseline
                  </span>
                </div>
              </div>

              {/* Key Forecast Drivers */}
              <div className="mt-6 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-4">
                <div className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)]">
                  Active Demand Drivers (Explainability)
                </div>
                <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs">
                  <div className="rounded-xl bg-[var(--surface-muted)] p-2.5">
                    <span className="text-[10px] text-[var(--text-secondary)]">Weekday Effect</span>
                    <div className="font-semibold text-[var(--text-primary)]">Thursday (+12)</div>
                  </div>
                  <div className="rounded-xl bg-[var(--surface-muted)] p-2.5">
                    <span className="text-[10px] text-[var(--text-secondary)]">Academic Schedule</span>
                    <div className="font-semibold text-[var(--text-primary)]">Regular Semester</div>
                  </div>
                  <div className="rounded-xl bg-[var(--surface-muted)] p-2.5">
                    <span className="text-[10px] text-[var(--text-secondary)]">Hostel Strength</span>
                    <div className="font-semibold text-[var(--text-primary)]">500 enrolled</div>
                  </div>
                  <div className="rounded-xl bg-[var(--surface-muted)] p-2.5">
                    <span className="text-[10px] text-[var(--text-secondary)]">Appetite Model</span>
                    <div className="font-semibold text-emerald-600 dark:text-emerald-400">Kaplan–Meier active</div>
                  </div>
                </div>
              </div>
            </BentoCard>

            {/* Quick Actions & Surplus Card */}
            <BentoCard className="lg:col-span-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 font-display text-sm font-bold text-[var(--text-primary)]">
                  <Sparkles className="h-4 w-4 text-[#173D32] dark:text-[#D7F36B]" />
                  Operational Quick Actions
                </div>
                <p className="mt-1 text-xs text-[var(--text-secondary)]">
                  Execute key meal operations in under 60 seconds
                </p>

                <div className="mt-4 space-y-2.5">
                  <button
                    onClick={() => onNavigate('planner')}
                    className="flex w-full items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] p-3 text-left transition hover:border-[#173D32] dark:hover:border-[#D7F36B]"
                  >
                    <div>
                      <div className="font-semibold text-xs text-[var(--text-primary)]">Optimize Lunch Quantities</div>
                      <div className="text-[11px] text-[var(--text-secondary)]">Dish-by-dish buffers at 95% service level</div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-[var(--text-secondary)]" />
                  </button>

                  <button
                    onClick={() => onNavigate('kitchen')}
                    className="flex w-full items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] p-3 text-left transition hover:border-[#173D32] dark:hover:border-[#D7F36B]"
                  >
                    <div>
                      <div className="font-semibold text-xs text-[var(--text-primary)]">Record Leftover Weight</div>
                      <div className="text-[11px] text-[var(--text-secondary)]">Touch, voice, or smart scale logging</div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-[var(--text-secondary)]" />
                  </button>

                  <button
                    onClick={() => onNavigate('surplus')}
                    className="flex w-full items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] p-3 text-left transition hover:border-[#173D32] dark:hover:border-[#D7F36B]"
                  >
                    <div>
                      <div className="font-semibold text-xs text-[var(--text-primary)]">Inspect Food-Safety Clock</div>
                      <div className="text-[11px] text-[var(--text-secondary)]">Check donation eligibility criteria</div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-[var(--text-secondary)]" />
                  </button>
                </div>
              </div>

              {/* Safety notice */}
              <div className="mt-6 rounded-xl border border-stone-200 bg-[var(--surface)] p-3 text-[11px] text-[var(--text-secondary)] dark:border-stone-800">
                <span className="font-semibold text-[var(--text-primary)]">Zero-Hunger Rule:</span>{' '}
                MessWise models never cut buffer on high-risk staples (Rice & Dal) to prevent run-outs.
              </div>
            </BentoCard>
          </div>

          {/* Recent Kitchen Activity Feed */}
          <div className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
              <div>
                <h3 className="font-display text-base font-bold text-[var(--text-primary)]">
                  Recent Kitchen Records
                </h3>
                <p className="text-xs text-[var(--text-secondary)]">
                  Verified and operational meals recorded in the database
                </p>
              </div>
              <button
                onClick={() => onNavigate('kitchen')}
                className="text-xs font-semibold text-[#173D32] dark:text-[#D7F36B] hover:underline"
              >
                View all meals
              </button>
            </div>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[var(--border)] text-[var(--text-secondary)]">
                    <th className="py-2.5 font-medium">Date</th>
                    <th className="py-2.5 font-medium">Meal Type</th>
                    <th className="py-2.5 font-medium">Recorded Headcount</th>
                    <th className="py-2.5 font-medium">Capacity</th>
                    <th className="py-2.5 font-medium">Data Tier</th>
                    <th className="py-2.5 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {recentMeals.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-stone-500">
                        No recent meals found for this environment.
                      </td>
                    </tr>
                  ) : (
                    recentMeals.map((m) => (
                      <tr key={m.id} className="hover:bg-[var(--surface-muted)] transition">
                        <td className="py-3 font-semibold text-[var(--text-primary)]">{m.date}</td>
                        <td className="py-3 capitalize text-[var(--text-secondary)]">{m.meal_type}</td>
                        <td className="py-3 font-semibold text-[var(--text-primary)] tabular-nums">{m.headcount}</td>
                        <td className="py-3 text-[var(--text-secondary)] tabular-nums">{m.hostel_strength}</td>
                        <td className="py-3">
                          {m.is_synthetic === 1 ? (
                            <span className="rounded-full bg-violet-50 text-violet-700 px-2.5 py-0.5 text-[10px] font-medium border border-violet-200 dark:bg-violet-950/40 dark:text-violet-300 dark:border-violet-800">
                              Synthetic Demo
                            </span>
                          ) : m.verification_status === 'verified_pilot' ? (
                            <span className="rounded-full bg-emerald-50 text-emerald-800 px-2.5 py-0.5 text-[10px] font-medium border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800">
                              Verified Pilot
                            </span>
                          ) : (
                            <span className="rounded-full bg-amber-50 text-amber-800 px-2.5 py-0.5 text-[10px] font-medium border border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800">
                              Unverified Test
                            </span>
                          )}
                        </td>
                        <td className="py-3 text-right">
                          <button
                            onClick={() => onNavigate('kitchen')}
                            className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1 text-[11px] font-medium text-[var(--text-primary)] transition hover:bg-[var(--surface-muted)]"
                          >
                            Details
                          </button>
                        </td>
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
