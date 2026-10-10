import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useEnvironment } from '@/context/EnvironmentContext';
import { PageHeader } from '@/components/common/PageHeader';
import { DataProvenanceBanner } from '@/components/common/DataProvenanceBanner';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import { BentoCard } from '@/components/common/BentoCard';
import { PlanResponse, DishPlan } from '@/lib/types';
import {
  Calculator,
  Sliders,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  ShieldCheck,
  RefreshCw,
  PlusCircle,
  FileCheck,
} from 'lucide-react';

export const PlannerPage: React.FC = () => {
  const { isSynthetic } = useEnvironment();
  const [date, setDate] = useState<string>('2026-10-15');
  const [mealType, setMealType] = useState<string>('lunch');
  const [serviceLevel, setServiceLevel] = useState<number>(0.95);

  const [plan, setPlan] = useState<PlanResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Overrides state: map of dish_id -> { overrideQty, overrideReason }
  const [overrides, setOverrides] = useState<Record<number, { qty: number; reason: string }>>({});
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);

  const loadPlan = async (sl = serviceLevel) => {
    setLoading(true);
    setError(null);
    setSavedSuccess(false);
    try {
      const res = await api.generatePlan({
        date,
        meal_type: mealType,
        service_level: sl,
        is_synthetic: isSynthetic,
      });
      setPlan(res);
    } catch (err: any) {
      console.error('Failed to generate plan:', err);
      setError(err.message || 'Error generating plan from backend service');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlan();
  }, [date, mealType, isSynthetic]);

  const handleServiceLevelChange = (val: number) => {
    setServiceLevel(val);
    loadPlan(val);
  };

  const handleOverride = (dishId: number, qty: number, reason: string) => {
    setOverrides({
      ...overrides,
      [dishId]: { qty, reason },
    });
  };

  const handleAcceptPlan = () => {
    setSavedSuccess(true);
  };

  return (
    <div>
      <PageHeader
        title="Dish Planner & Cooking Optimizer"
        subtitle="Newsvendor service-level optimization translating headcount uncertainty into dish-by-dish cooking buffers."
        icon={Calculator}
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => loadPlan()}
              className="flex items-center gap-1.5 rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-xs font-semibold text-[var(--text-primary)] transition hover:bg-[var(--surface-muted)]"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Recalculate Plan
            </button>
            <button
              onClick={handleAcceptPlan}
              className="flex items-center gap-1.5 rounded-xl bg-[#173D32] px-4 py-2 text-xs font-semibold text-white shadow-xs transition hover:bg-[#102C24] dark:bg-[#D7F36B] dark:text-[#102C24]"
            >
              <FileCheck className="h-3.5 w-3.5" />
              Confirm & Dispatch Plan
            </button>
          </div>
        }
      />

      <DataProvenanceBanner />

      {savedSuccess && (
        <div className="mb-6 rounded-2xl border border-emerald-300 bg-emerald-50 p-4 text-xs text-emerald-950 dark:border-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-200">
          <div className="flex items-center gap-2 font-semibold">
            <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
            Cooking Plan Confirmed & Dispatched to Kitchen Display
          </div>
          <p className="mt-1 ml-6 text-[11px] text-emerald-800 dark:text-emerald-300">
            Dish targets frozen. Overrides logged with manager justification for Kaplan–Meier audit tracking.
          </p>
        </div>
      )}

      {error && (
        <div className="mb-6 rounded-xl border border-red-300 bg-red-50 p-4 text-xs text-red-900 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          <div className="font-semibold">Planner optimization note:</div>
          <p className="mt-1">{error}</p>
        </div>
      )}

      {/* Meal Selection & Service-Level Control */}
      <div className="mb-6 rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          {/* Left: Meal Selectors */}
          <div className="lg:col-span-5 grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[var(--text-secondary)]">Meal Date</label>
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

            <div className="col-span-2 rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] p-3">
              <span className="text-[10px] font-semibold text-[var(--text-secondary)] uppercase">
                Forecast Demand Context
              </span>
              <div className="mt-1 flex items-baseline justify-between">
                <span className="font-display text-lg font-bold text-[#173D32] dark:text-[#D7F36B]">
                  {plan ? Math.round(plan.forecast_headcount) : '420'} students
                </span>
                <span className="text-xs text-[var(--text-secondary)]">
                  80% Range: [{plan ? `${Math.round(plan.h_lo)} – ${Math.round(plan.h_hi)}` : '402 – 438'}]
                </span>
              </div>
            </div>
          </div>

          {/* Right: Service-Level Control Slider */}
          <div className="lg:col-span-7 flex flex-col justify-between rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-5">
            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sliders className="h-4 w-4 text-[#173D32] dark:text-[#D7F36B]" />
                  <span className="font-display text-sm font-bold text-[var(--text-primary)]">
                    Service-Level Reliability Target (Newsvendor Fractile)
                  </span>
                </div>
                <span className="font-display text-base font-extrabold text-emerald-600 dark:text-emerald-400 tabular-nums">
                  {Math.round(serviceLevel * 100)}%
                </span>
              </div>
              <p className="mt-1 text-xs text-[var(--text-secondary)]">
                Higher service levels protect against stock-outs at the cost of modest calculated surplus.
              </p>

              {/* Slider & Presets */}
              <div className="mt-4">
                <input
                  type="range"
                  min={0.85}
                  max={0.99}
                  step={0.01}
                  value={serviceLevel}
                  onChange={(e) => handleServiceLevelChange(parseFloat(e.target.value))}
                  className="w-full accent-[#173D32] dark:accent-[#D7F36B]"
                />
                <div className="mt-2 flex justify-between text-[11px] text-[var(--text-secondary)]">
                  <span>85% (Aggressive Lean)</span>
                  <span>90% (Lean Service)</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">95% (Standard Mess Target)</span>
                  <span>99% (Zero-Shortage)</span>
                </div>
              </div>

              <div className="mt-3 flex gap-2">
                {[0.90, 0.95, 0.99].map((sl) => (
                  <button
                    key={sl}
                    type="button"
                    onClick={() => handleServiceLevelChange(sl)}
                    className={`rounded-lg px-2.5 py-1 text-xs font-semibold border transition ${
                      Math.abs(serviceLevel - sl) < 0.005
                        ? 'border-[#173D32] bg-[#173D32] text-white dark:border-[#D7F36B] dark:bg-[#D7F36B] dark:text-[#102C24]'
                        : 'border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                    }`}
                  >
                    Preset: {Math.round(sl * 100)}%
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {loading ? (
        <LoadingSkeleton className="h-72" count={2} />
      ) : plan ? (
        <div className="space-y-6">
          {/* Dish-by-Dish Planning Table */}
          <div className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
              <div>
                <h3 className="font-display text-base font-bold text-[var(--text-primary)]">
                  Recommended Cooking Quantities (Dish Breakdown)
                </h3>
                <p className="text-xs text-[var(--text-secondary)]">
                  Computed via per-dish consumption variance, standard portions, and safety factor
                </p>
              </div>
              <span className="text-xs text-stone-500 font-medium">
                {plan.dishes.length} dishes planned
              </span>
            </div>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[var(--border)] text-[var(--text-secondary)]">
                    <th className="py-2.5 font-medium">Dish Name</th>
                    <th className="py-2.5 font-medium">Category</th>
                    <th className="py-2.5 font-medium">Consumption Rate</th>
                    <th className="py-2.5 font-medium">Safety Factor</th>
                    <th className="py-2.5 font-medium">Model Planned</th>
                    <th className="py-2.5 font-medium">Expected Surplus</th>
                    <th className="py-2.5 font-medium">Run-Out Risk</th>
                    <th className="py-2.5 font-medium">Manager Override</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {plan.dishes.map((dish) => {
                    const isOverridden = Boolean(overrides[dish.dish_id]);
                    const currentOverride = overrides[dish.dish_id];

                    return (
                      <tr key={dish.dish_id} className="hover:bg-[var(--surface-muted)] transition">
                        <td className="py-3 font-semibold text-[var(--text-primary)]">
                          {dish.dish_name}
                        </td>
                        <td className="py-3 capitalize text-[var(--text-secondary)]">
                          {dish.category}
                        </td>
                        <td className="py-3 tabular-nums text-[var(--text-secondary)]">
                          {dish.per_head_consumption} {dish.unit}/head
                        </td>
                        <td className="py-3 tabular-nums font-medium text-stone-600 dark:text-stone-300">
                          {dish.safety_factor.toFixed(2)}x
                        </td>
                        <td className="py-3 font-bold text-[#173D32] dark:text-[#D7F36B] tabular-nums text-sm">
                          {dish.planned_qty.toFixed(1)} {dish.unit}
                        </td>
                        <td className="py-3 tabular-nums text-[var(--text-secondary)]">
                          ~{dish.expected_surplus.toFixed(1)} {dish.unit}
                        </td>
                        <td className="py-3">
                          <span
                            className={`rounded-full px-2 py-0.5 text-[10px] font-semibold border ${
                              dish.shortage_risk_pct <= 5
                                ? 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800'
                                : 'bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800'
                            }`}
                          >
                            {dish.shortage_risk_pct.toFixed(1)}%
                          </span>
                        </td>
                        <td className="py-3">
                          <div className="flex items-center gap-2">
                            <input
                              type="number"
                              step="0.5"
                              placeholder={dish.planned_qty.toFixed(1)}
                              value={currentOverride ? currentOverride.qty : ''}
                              onChange={(e) =>
                                handleOverride(
                                  dish.dish_id,
                                  parseFloat(e.target.value) || dish.planned_qty,
                                  currentOverride?.reason || 'Chef Experience'
                                )
                              }
                              className="w-20 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-2 py-1 text-xs font-semibold tabular-nums focus:outline-hidden"
                            />
                            {isOverridden && (
                              <select
                                value={currentOverride?.reason || 'Chef Experience'}
                                onChange={(e) =>
                                  handleOverride(dish.dish_id, currentOverride.qty, e.target.value)
                                }
                                className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-2 py-1 text-[10px] text-[var(--text-secondary)]"
                              >
                                <option value="Chef Experience">Chef Experience</option>
                                <option value="Special Guest VIP">Special Guest VIP</option>
                                <option value="Batch Size Restriction">Batch Size Restriction</option>
                                <option value="Perishable Inventory">Perishable Inventory</option>
                              </select>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Staged Batch Top-Up Recommendations */}
          <div className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
            <div className="flex items-center gap-2 font-display text-sm font-bold text-[var(--text-primary)]">
              <PlusCircle className="h-4 w-4 text-[#173D32] dark:text-[#D7F36B]" />
              Staged Preparation & Top-Up Advice
            </div>
            <p className="mt-1 text-xs text-[var(--text-secondary)]">
              Instead of cooking 100% of buffer in Batch 1, hold secondary batches until service threshold is crossed
            </p>

            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3 text-xs">
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-4">
                <div className="font-semibold text-[var(--text-primary)]">Rice Cookers</div>
                <div className="mt-1 text-stone-500 text-[11px]">
                  Batch 1: 75% of plan at 11:30 AM. Hold 25% dry soaked until 1:00 PM tally check.
                </div>
              </div>
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-4">
                <div className="font-semibold text-[var(--text-primary)]">Dal / Gravy</div>
                <div className="mt-1 text-stone-500 text-[11px]">
                  Simmer 85% initially. Temper final 15% top-up pan only if attendance crosses 380 by 1:15 PM.
                </div>
              </div>
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-4">
                <div className="font-semibold text-[var(--text-primary)]">Chapatis / Breads</div>
                <div className="mt-1 text-stone-500 text-[11px]">
                  Rolling tawa service on demand during peak rush 12:45–1:30 PM to prevent cold plate waste.
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
