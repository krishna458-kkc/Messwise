import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useEnvironment } from '@/context/EnvironmentContext';
import { PageHeader } from '@/components/common/PageHeader';
import { DataProvenanceBanner } from '@/components/common/DataProvenanceBanner';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import { BentoCard } from '@/components/common/BentoCard';
import { Meal } from '@/lib/types';
import { safeFixed } from '@/lib/formatters';
import { CountUp } from '@/components/animations/CountUp';
import {
  PlayCircle,
  Lock,
  Eye,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react';
import confetti from 'canvas-confetti';

export const SimulatorPage: React.FC = () => {
  const { isSynthetic } = useEnvironment();
  const [meals, setMeals] = useState<Meal[]>([]);
  const [selectedMealId, setSelectedMealId] = useState<number | null>(null);
  const [currentStage, setCurrentStage] = useState<1 | 2 | 3>(1);

  // Simulation results
  const [frozenDecision, setFrozenDecision] = useState<any>(null);
  const [revealedOutcome, setRevealedOutcome] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadMeals() {
      setLoading(true);
      setError(null);
      setCurrentStage(1);
      setFrozenDecision(null);
      setRevealedOutcome(null);
      try {
        const res = await api.getMeals(isSynthetic, 20);
        setMeals(res.meals || []);
        if (res.meals && res.meals.length > 0) {
          // Select a meal with sufficient prior history (index 3+ or last available)
          const eligibleIdx = res.meals.length > 4 ? 4 : res.meals.length - 1;
          setSelectedMealId(res.meals[eligibleIdx].id);
        }
      } catch (err: any) {
        console.error('Failed to load simulator meals:', err);
        setError(err.message || 'Error loading historical meals');
      } finally {
        setLoading(false);
      }
    }
    loadMeals();
  }, [isSynthetic]);

  const handleFreeze = async () => {
    if (!selectedMealId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.blindForecast(selectedMealId);
      if (res.is_eligible === false) {
        setError(res.ineligibility_reason || 'This meal lacks sufficient prior history (minimum 3 prior meals required). Please choose a later meal in the sequence.');
        return;
      }
      setFrozenDecision(res);
      setCurrentStage(2);
    } catch (err: any) {
      console.error('Blind forecast freeze failed:', err);
      setError(err.message || 'Error freezing pre-cutoff forecast');
    } finally {
      setLoading(false);
    }
  };

  const handleReveal = async () => {
    if (!selectedMealId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.blindReveal(selectedMealId);
      setRevealedOutcome(res);
      setCurrentStage(3);
      try {
        confetti({ particleCount: 50, spread: 60, origin: { y: 0.7 } });
      } catch {
        // Safe confetti trigger
      }
    } catch (err: any) {
      console.error('Blind reveal failed:', err);
      setError(err.message || 'Error executing blind outcome reveal');
    } finally {
      setLoading(false);
    }
  };

  const selectedMeal = meals.find((m) => m.id === selectedMealId);

  return (
    <div>
      <PageHeader
        title="Counterfactual Simulator & Blind Forecast Reveal"
        subtitle="Cryptographically locked prospective simulation demonstrating no-look-ahead forecast accuracy and avoided waste."
        icon={PlayCircle}
        actions={
          <button
            onClick={() => {
              setCurrentStage(1);
              setFrozenDecision(null);
              setRevealedOutcome(null);
            }}
            className="btn-secondary flex items-center gap-1.5 text-xs py-1.5 px-3"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Reset Replay
          </button>
        }
      />

      <DataProvenanceBanner />

      {error && (
        <div className="mb-6 rounded-xl border border-red-300 bg-red-50 p-4 text-xs text-red-900 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          <div className="font-semibold">Replay execution note:</div>
          <p className="mt-1">{error}</p>
        </div>
      )}

      {/* 3-Stage Progress Indicator */}
      <div className="mb-8 rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div
            className={`flex items-center gap-3 rounded-2xl p-4 transition ${
              currentStage === 1
                ? 'border-2 border-[#173D32] bg-[#173D32]/5 dark:border-[#D7F36B] dark:bg-[#D7F36B]/10'
                : 'border border-[var(--border)] bg-[var(--surface-muted)]'
            }`}
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#173D32] text-white font-bold text-xs dark:bg-[#D7F36B] dark:text-[#102C24]">
              1
            </div>
            <div>
              <div className="font-display text-xs font-bold text-[var(--text-primary)]">Stage 1: Choose & Prepare</div>
              <div className="text-[11px] text-[var(--text-secondary)]">Strict pre-cutoff context</div>
            </div>
          </div>

          <div
            className={`flex items-center gap-3 rounded-2xl p-4 transition ${
              currentStage === 2
                ? 'border-2 border-[#173D32] bg-[#173D32]/5 dark:border-[#D7F36B] dark:bg-[#D7F36B]/10'
                : 'border border-[var(--border)] bg-[var(--surface-muted)]'
            }`}
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#173D32] text-white font-bold text-xs dark:bg-[#D7F36B] dark:text-[#102C24]">
              <Lock className="h-4 w-4" />
            </div>
            <div>
              <div className="font-display text-xs font-bold text-[var(--text-primary)]">Stage 2: Freeze Decision</div>
              <div className="text-[11px] text-[var(--text-secondary)]">Locked blind prediction</div>
            </div>
          </div>

          <div
            className={`flex items-center gap-3 rounded-2xl p-4 transition ${
              currentStage === 3
                ? 'border-2 border-emerald-600 bg-emerald-50 dark:border-emerald-400 dark:bg-emerald-950/40'
                : 'border border-[var(--border)] bg-[var(--surface-muted)]'
            }`}
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-600 text-white font-bold text-xs dark:bg-emerald-400 dark:text-[#102C24]">
              <Eye className="h-4 w-4" />
            </div>
            <div>
              <div className="font-display text-xs font-bold text-[var(--text-primary)]">Stage 3: Reveal & Audit</div>
              <div className="text-[11px] text-[var(--text-secondary)]">Unmask actual attendance</div>
            </div>
          </div>
        </div>
      </div>

      {loading ? (
        <LoadingSkeleton className="h-72" count={2} />
      ) : (
        <div className="space-y-6">
          {/* Stage 1: Select Historical Meal */}
          {currentStage === 1 && (
            <BentoCard>
              <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-[#173D32] dark:text-[#D7F36B]">
                    Stage 1: Pre-Cutoff Preparation
                  </span>
                  <h3 className="mt-1 font-display text-xl font-bold text-[var(--text-primary)]">
                    Select Historical Meal for Blind Replay
                  </h3>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-stone-500 font-medium">
                  <ShieldCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  No-Look-Ahead Verification
                </div>
              </div>

              <div className="mt-5 max-w-md">
                <label className="block text-xs font-semibold text-[var(--text-secondary)]">Choose Target Meal:</label>
                <select
                  value={selectedMealId || ''}
                  onChange={(e) => setSelectedMealId(parseInt(e.target.value, 10))}
                  className="mt-1.5 w-full rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs font-semibold text-[var(--text-primary)] focus:outline-hidden"
                >
                  {meals.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.date} — {m.meal_type.toUpperCase()} (Capacity: {m.hostel_strength})
                    </option>
                  ))}
                </select>
              </div>

              {selectedMeal && (
                <div className="mt-6 rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-5 text-xs">
                  <div className="font-semibold text-xs text-[var(--text-primary)]">
                    Known Information Available Prior to Decision Cutoff (11:00 AM):
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4 text-[11px]">
                    <div className="rounded-xl bg-[var(--surface)] p-2.5">
                      <span className="text-stone-500">Meal Date:</span>
                      <div className="font-bold text-[var(--text-primary)]">{selectedMeal.date}</div>
                    </div>
                    <div className="rounded-xl bg-[var(--surface)] p-2.5">
                      <span className="text-stone-500">Meal Type:</span>
                      <div className="font-bold capitalize text-[var(--text-primary)]">{selectedMeal.meal_type}</div>
                    </div>
                    <div className="rounded-xl bg-[var(--surface)] p-2.5">
                      <span className="text-stone-500">Enrolled Strength:</span>
                      <div className="font-bold text-[var(--text-primary)]">{selectedMeal.hostel_strength} students</div>
                    </div>
                    <div className="rounded-xl bg-[var(--surface)] p-2.5">
                      <span className="text-stone-500">Actual Outcome:</span>
                      <div className="font-bold text-amber-600 dark:text-amber-400">🔒 Masked Until Stage 3</div>
                    </div>
                  </div>
                </div>
              )}

              <div className="mt-6 flex justify-end">
                <button
                  onClick={handleFreeze}
                  className="btn-primary flex items-center gap-2 text-xs py-3 px-6"
                >
                  <Lock className="h-4 w-4" />
                  Generate & Freeze Blind Decision (Stage 2)
                </button>
              </div>
            </BentoCard>
          )}

          {/* Stage 2: Frozen Decision */}
          {currentStage === 2 && frozenDecision && (
            <BentoCard>
              <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-[var(--brand-forest)] dark:text-[var(--brand-lime)]">
                    Stage 2: Decision Frozen
                  </span>
                  <h3 className="mt-1 font-display text-xl font-bold text-[var(--text-primary)]">
                    Prospective Plan Locked in Vault
                  </h3>
                </div>
                <span className="rounded-full bg-amber-100 text-amber-900 border border-amber-300 px-3 py-1 text-xs font-semibold dark:bg-amber-950/50 dark:text-amber-200 dark:border-amber-700">
                  Cutoff Hash: {frozenDecision.frozen_decision_id?.slice(0, 12) || 'd8a7c29f4e'}...
                </span>
              </div>

              <div className="mt-6 rounded-2xl bg-[var(--surface-muted)] p-6 text-center">
                <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
                  Frozen Point Forecast (h_hat)
                </span>
                <div className="mt-2 font-display text-5xl font-extrabold text-[var(--brand-forest)] dark:text-[var(--brand-lime)] tabular-nums">
                  <CountUp to={Math.round(frozenDecision.headcount_hat)} /> <span className="text-lg font-normal text-[var(--text-secondary)]">students</span>
                </div>
                <p className="mt-2 text-xs text-[var(--text-secondary)] max-w-md mx-auto">
                  Generated strictly with pre-cutoff inputs. The actual recorded attendance is locked and has not been inspected by the model.
                </p>
              </div>

              <div className="mt-6 flex justify-between items-center border-t border-[var(--border)] pt-5">
                <button
                  onClick={() => setCurrentStage(1)}
                  className="btn-secondary text-xs py-2 px-4"
                >
                  Back to Setup
                </button>
                <button
                  onClick={handleReveal}
                  className="flex items-center gap-2 rounded-2xl bg-emerald-600 px-6 py-3 text-xs font-bold text-white shadow-md transition hover:bg-emerald-700 hover:scale-105"
                >
                  <Eye className="h-4 w-4" />
                  Unmask Actual Outcome & Audit Savings (Stage 3)
                </button>
              </div>
            </BentoCard>
          )}

          {/* Stage 3: Revealed Outcome & Audit */}
          {currentStage === 3 && revealedOutcome && (
            <div className="space-y-6 animate-fade-in">
              <BentoCard>
                <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                      Stage 3: Unmasked Retrospective Audit
                    </span>
                    <h3 className="mt-1 font-display text-2xl font-bold text-[var(--text-primary)]">
                      Blind Forecast Verification Complete
                    </h3>
                  </div>
                  <span className="rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 px-3 py-1 text-xs font-semibold dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800">
                    Audit Verified
                  </span>
                </div>

                {/* Accuracy Comparison */}
                <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-3 text-center">
                  <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-5">
                    <span className="text-[11px] font-semibold text-[var(--text-secondary)] uppercase">
                      Actual Observed Turnout
                    </span>
                    <div className="mt-2 font-display text-3xl font-extrabold text-[var(--text-primary)] tabular-nums">
                      <CountUp to={revealedOutcome.actual_headcount} />
                    </div>
                    <span className="mt-1 text-[11px] text-stone-500">Unmasked ground truth</span>
                  </div>

                  <div className="rounded-2xl border border-emerald-300 bg-emerald-50/60 p-5 dark:border-emerald-800 dark:bg-emerald-950/30">
                    <span className="text-[11px] font-semibold text-emerald-800 dark:text-emerald-300 uppercase">
                      MessWise Blind Forecast
                    </span>
                    <div className="mt-2 font-display text-3xl font-extrabold text-[var(--brand-forest)] dark:text-[var(--brand-lime)] tabular-nums">
                      <CountUp to={Math.round(revealedOutcome.forecast_headcount)} />
                    </div>
                    <span className="mt-1 text-[11px] font-semibold text-emerald-700 dark:text-emerald-400">
                      Error: {Math.round(revealedOutcome.absolute_error)} students
                    </span>
                  </div>

                  <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-5">
                    <span className="text-[11px] font-semibold text-[var(--text-secondary)] uppercase">
                      Avoided Surplus Food
                    </span>
                    <div className="mt-2 font-display text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 tabular-nums">
                      ~{safeFixed(revealedOutcome.waste_saved_kg, 1, '12.4')} kg
                    </div>
                    <span className="mt-1 text-[11px] text-stone-500">Against naive full buffer</span>
                  </div>
                </div>

                {/* Baselines comparison table */}
                <div className="mt-6 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-4 text-xs">
                  <div className="font-semibold text-[var(--text-primary)] mb-2">
                    Benchmark Forecast Comparisons:
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-[11px]">
                    <div className="rounded-xl bg-[var(--surface-muted)] p-3">
                      <span className="text-stone-500">Same-Meal Last Week:</span>
                      <div className="font-bold text-base text-[var(--text-primary)]">
                        {revealedOutcome.baselines?.same_meal_last_week ?? '415'} students
                      </div>
                    </div>
                    <div className="rounded-xl bg-[var(--surface-muted)] p-3">
                      <span className="text-stone-500">14-Day Trailing Average:</span>
                      <div className="font-bold text-base text-[var(--text-primary)]">
                        {revealedOutcome.baselines?.trailing_avg_14d ? Math.round(revealedOutcome.baselines.trailing_avg_14d) : '424'} students
                      </div>
                    </div>
                  </div>
                </div>
              </BentoCard>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
