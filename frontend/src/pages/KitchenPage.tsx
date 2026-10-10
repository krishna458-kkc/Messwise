import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useEnvironment } from '@/context/EnvironmentContext';
import { PageHeader } from '@/components/common/PageHeader';
import { DataProvenanceBanner } from '@/components/common/DataProvenanceBanner';
import { Dish, Meal } from '@/lib/types';
import {
  UtensilsCrossed,
  CheckCircle2,
  AlertTriangle,
  Mic,
  Camera,
  FileSpreadsheet,
  Plus,
  Trash2,
  Save,
  HelpCircle,
  Clock,
} from 'lucide-react';

export const KitchenPage: React.FC = () => {
  const { isSynthetic, refreshSummary } = useEnvironment();
  const [dishes, setDishes] = useState<Dish[]>([]);
  const [recentMeals, setRecentMeals] = useState<Meal[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Form State
  const [mealDate, setMealDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [mealType, setMealType] = useState<string>('lunch');
  const [headcount, setHeadcount] = useState<number>(420);
  const [hostelStrength, setHostelStrength] = useState<number>(500);
  const [isExamDay, setIsExamDay] = useState<boolean>(false);
  const [isHoliday, setIsHoliday] = useState<boolean>(false);

  // Dish log entries
  const [dishRows, setDishRows] = useState<
    Array<{
      dish_id: number;
      cooked_qty: number;
      leftover_qty: number;
      unit: string;
      ran_out: boolean;
      waste_reason: string;
    }>
  >([]);

  // Feedback states
  const [validationError, setValidationError] = useState<string | null>(null);
  const [successReceipt, setSuccessReceipt] = useState<{
    mealId: number;
    headcount: number;
    totalCooked: number;
    totalLeftover: number;
  } | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Helper modals
  const [voiceModalOpen, setVoiceModalOpen] = useState(false);
  const [voiceText, setVoiceText] = useState('');
  const [photoModalOpen, setPhotoModalOpen] = useState(false);

  useEffect(() => {
    async function loadKitchenData() {
      try {
        const [dRes, mRes] = await Promise.all([
          api.getDishes(),
          api.getMeals(isSynthetic, 5),
        ]);
        setDishes(dRes.dishes || []);
        setRecentMeals(mRes.meals || []);

        // Initialize with default dishes if empty
        if (dRes.dishes && dRes.dishes.length > 0 && dishRows.length === 0) {
          const defaults = dRes.dishes.slice(0, 3).map((d) => ({
            dish_id: d.id,
            cooked_qty: 60.0,
            leftover_qty: 4.5,
            unit: d.unit || 'kg',
            ran_out: false,
            waste_reason: 'Normal Plate Remainder',
          }));
          setDishRows(defaults);
        }
      } catch (err) {
        console.error('Failed to load kitchen initial data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadKitchenData();
  }, [isSynthetic]);

  const addDishRow = () => {
    if (dishes.length === 0) return;
    const nextDish = dishes[dishRows.length % dishes.length];
    setDishRows([
      ...dishRows,
      {
        dish_id: nextDish.id,
        cooked_qty: 50.0,
        leftover_qty: 0.0,
        unit: nextDish.unit || 'kg',
        ran_out: false,
        waste_reason: 'None',
      },
    ]);
  };

  const removeDishRow = (idx: number) => {
    setDishRows(dishRows.filter((_, i) => i !== idx));
  };

  const handleDishChange = (index: number, field: string, value: any) => {
    const updated = [...dishRows];
    updated[index] = { ...updated[index], [field]: value };
    setDishRows(updated);
  };

  const handleVoiceSimulate = () => {
    // Simulates voice parsing for English, Telugu, Hindi kitchen voice logging
    if (dishRows.length > 0) {
      const updated = [...dishRows];
      updated[0].cooked_qty = 65.0;
      updated[0].leftover_qty = 5.2;
      setDishRows(updated);
    }
    setVoiceModalOpen(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    setSuccessReceipt(null);

    // Rigorous Validation
    if (headcount <= 0) {
      setValidationError('Attendance headcount must be greater than zero.');
      return;
    }
    if (headcount > hostelStrength * 1.5) {
      setValidationError(`Headcount (${headcount}) cannot exceed 150% of hostel strength (${hostelStrength}).`);
      return;
    }
    if (dishRows.length === 0) {
      setValidationError('At least one dish record must be added to log the meal.');
      return;
    }

    for (let i = 0; i < dishRows.length; i++) {
      const row = dishRows[i];
      const dName = dishes.find((d) => d.id === row.dish_id)?.name || `Dish #${i + 1}`;
      if (row.cooked_qty <= 0) {
        setValidationError(`Cooked quantity for ${dName} must be positive.`);
        return;
      }
      if (row.leftover_qty < 0) {
        setValidationError(`Leftover quantity for ${dName} cannot be negative.`);
        return;
      }
      if (row.leftover_qty > row.cooked_qty) {
        setValidationError(`Leftover quantity for ${dName} (${row.leftover_qty} ${row.unit}) cannot exceed cooked quantity (${row.cooked_qty} ${row.unit}).`);
        return;
      }
    }

    setSubmitting(true);
    try {
      // 1. Log Meal
      const mealRes = await api.logMeal({
        date: mealDate,
        meal_type: mealType,
        headcount,
        hostel_strength: hostelStrength,
        is_exam_day: isExamDay,
        is_holiday: isHoliday,
        source: 'manual',
        is_synthetic: 0, // Operational test entry
      });

      const newMealId = mealRes.meal.id;

      // 2. Log Dishes
      let totalC = 0;
      let totalL = 0;
      for (const row of dishRows) {
        totalC += row.cooked_qty;
        totalL += row.leftover_qty;
        await api.logDish({
          meal_id: newMealId,
          dish_id: row.dish_id,
          cooked_qty: row.cooked_qty,
          leftover_qty: row.leftover_qty,
          unit: row.unit,
          ran_out: row.ran_out ? 1 : 0,
          waste_reason: row.waste_reason,
          is_synthetic: 0,
        });
      }

      setSuccessReceipt({
        mealId: newMealId,
        headcount,
        totalCooked: Math.round(totalC * 10) / 10,
        totalLeftover: Math.round(totalL * 10) / 10,
      });

      await refreshSummary();
      // Reload recent meals
      const mRes = await api.getMeals(0, 5);
      setRecentMeals(mRes.meals || []);
    } catch (err: any) {
      console.error('Failed to log meal:', err);
      setValidationError(err.message || 'Server error while logging meal');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Kitchen Logging"
        subtitle="Touch-friendly, rapid measurement capture for meal attendance and dish-by-dish leftovers."
        icon={UtensilsCrossed}
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => setVoiceModalOpen(true)}
              className="flex items-center gap-1.5 rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5 text-xs font-semibold text-[var(--text-primary)] transition hover:bg-[var(--surface-muted)]"
            >
              <Mic className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
              Voice Logger
            </button>
            <button
              onClick={() => setPhotoModalOpen(true)}
              className="flex items-center gap-1.5 rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5 text-xs font-semibold text-[var(--text-primary)] transition hover:bg-[var(--surface-muted)]"
            >
              <Camera className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400" />
              Photo Estimate
            </button>
          </div>
        }
      />

      <DataProvenanceBanner />

      {/* Success Receipt Banner */}
      {successReceipt && (
        <div className="mb-6 rounded-2xl border border-emerald-300 bg-emerald-50/90 p-5 text-emerald-950 dark:border-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-200">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-6 w-6 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <div>
                <h3 className="font-display text-base font-bold text-emerald-900 dark:text-emerald-100">
                  Meal Recorded Successfully (ID #{successReceipt.mealId})
                </h3>
                <p className="mt-1 text-xs">
                  Logged attendance: <strong>{successReceipt.headcount} students</strong> • Cooked: <strong>{successReceipt.totalCooked} kg</strong> • Leftover: <strong>{successReceipt.totalLeftover} kg</strong>
                </p>
                <div className="mt-2 text-[11px] text-emerald-800/90 dark:text-emerald-300">
                  Provenance status: <span className="font-semibold underline">🟡 Unverified Test Entry (Non-Pilot)</span>. Requires supervisory audit protocol for promotion to verified pilot evidence.
                </div>
              </div>
            </div>
            <button
              onClick={() => setSuccessReceipt(null)}
              className="rounded-lg border border-emerald-400 bg-white px-2.5 py-1 text-xs font-medium text-emerald-900 dark:border-emerald-700 dark:bg-emerald-900 dark:text-emerald-100"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Validation Error Banner */}
      {validationError && (
        <div className="mb-6 rounded-2xl border border-red-300 bg-red-50 p-4 text-xs text-red-900 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          <div className="flex items-center gap-2 font-semibold">
            <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-400" />
            Kitchen Input Validation Failed:
          </div>
          <p className="mt-1 ml-6">{validationError}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Stage 1: Meal Context Panel */}
        <div className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
          <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-[#173D32] dark:text-[#D7F36B]">
                Stage 1 of 2
              </span>
              <h3 className="font-display text-base font-bold text-[var(--text-primary)]">
                Meal & Attendance Context
              </h3>
            </div>
            <span className="text-xs text-[var(--text-secondary)]">
              Manual Operational Entry
            </span>
          </div>

          <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <label className="block text-xs font-semibold text-[var(--text-secondary)]">Meal Date</label>
              <input
                type="date"
                value={mealDate}
                onChange={(e) => setMealDate(e.target.value)}
                required
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
              <label className="block text-xs font-semibold text-[var(--text-secondary)]">
                Recorded Attendance Headcount
              </label>
              <input
                type="number"
                min={1}
                max={1500}
                value={headcount}
                onChange={(e) => setHeadcount(parseInt(e.target.value, 10) || 0)}
                required
                className="mt-1.5 w-full rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs font-semibold text-[var(--text-primary)] focus:outline-hidden"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--text-secondary)]">
                Hostel Dining Capacity
              </label>
              <input
                type="number"
                min={50}
                max={2000}
                value={hostelStrength}
                onChange={(e) => setHostelStrength(parseInt(e.target.value, 10) || 0)}
                required
                className="mt-1.5 w-full rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs font-semibold text-[var(--text-primary)] focus:outline-hidden"
              />
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-4 pt-2">
            <label className="flex items-center gap-2 text-xs text-[var(--text-secondary)] cursor-pointer">
              <input
                type="checkbox"
                checked={isExamDay}
                onChange={(e) => setIsExamDay(e.target.checked)}
                className="rounded accent-[#173D32] dark:accent-[#D7F36B]"
              />
              <span>Exam Day (Reduced Attendance)</span>
            </label>
            <label className="flex items-center gap-2 text-xs text-[var(--text-secondary)] cursor-pointer">
              <input
                type="checkbox"
                checked={isHoliday}
                onChange={(e) => setIsHoliday(e.target.checked)}
                className="rounded accent-[#173D32] dark:accent-[#D7F36B]"
              />
              <span>Campus Holiday / Weekend Outing</span>
            </label>
          </div>
        </div>

        {/* Stage 2: Dish Cooked & Leftover Quantities */}
        <div className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
          <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-[#173D32] dark:text-[#D7F36B]">
                Stage 2 of 2
              </span>
              <h3 className="font-display text-base font-bold text-[var(--text-primary)]">
                Dish Preparation & Leftover Quantities
              </h3>
            </div>
            <button
              type="button"
              onClick={addDishRow}
              className="flex items-center gap-1.5 rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-1.5 text-xs font-semibold text-[var(--text-primary)] transition hover:border-[#173D32] dark:hover:border-[#D7F36B]"
            >
              <Plus className="h-3.5 w-3.5" />
              Add Dish
            </button>
          </div>

          <div className="mt-5 space-y-4">
            {dishRows.map((row, idx) => (
              <div
                key={idx}
                className="flex flex-col gap-3 rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-4 sm:flex-row sm:items-center"
              >
                {/* Dish Selector */}
                <div className="flex-1">
                  <label className="block text-[11px] font-semibold text-[var(--text-secondary)]">Dish Item</label>
                  <select
                    value={row.dish_id}
                    onChange={(e) => handleDishChange(idx, 'dish_id', parseInt(e.target.value, 10))}
                    className="mt-1 w-full rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-xs font-semibold text-[var(--text-primary)] focus:outline-hidden"
                  >
                    {dishes.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name} ({d.category} • {d.unit})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Cooked Qty */}
                <div className="w-full sm:w-28">
                  <label className="block text-[11px] font-semibold text-[var(--text-secondary)]">Cooked ({row.unit})</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={row.cooked_qty}
                    onChange={(e) => handleDishChange(idx, 'cooked_qty', parseFloat(e.target.value) || 0)}
                    className="mt-1 w-full rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-xs font-bold text-[var(--text-primary)] tabular-nums focus:outline-hidden"
                  />
                </div>

                {/* Leftover Qty */}
                <div className="w-full sm:w-28">
                  <label className="block text-[11px] font-semibold text-[var(--text-secondary)]">Leftover ({row.unit})</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={row.leftover_qty}
                    onChange={(e) => handleDishChange(idx, 'leftover_qty', parseFloat(e.target.value) || 0)}
                    className="mt-1 w-full rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-xs font-bold text-emerald-600 dark:text-emerald-400 tabular-nums focus:outline-hidden"
                  />
                </div>

                {/* Ran out toggle */}
                <div className="flex items-center sm:pt-4">
                  <label className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)] cursor-pointer">
                    <input
                      type="checkbox"
                      checked={row.ran_out}
                      onChange={(e) => handleDishChange(idx, 'ran_out', e.target.checked)}
                      className="rounded accent-red-600"
                    />
                    <span className="font-semibold text-red-600 dark:text-red-400">Ran Out</span>
                  </label>
                </div>

                {/* Reason tag */}
                <div className="flex-1">
                  <label className="block text-[11px] font-semibold text-[var(--text-secondary)]">Waste Reason</label>
                  <select
                    value={row.waste_reason}
                    onChange={(e) => handleDishChange(idx, 'waste_reason', e.target.value)}
                    className="mt-1 w-full rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-xs font-medium text-[var(--text-primary)] focus:outline-hidden"
                  >
                    <option value="Normal Plate Remainder">Normal Plate Remainder</option>
                    <option value="Rain / Weather Disruption">Rain / Weather Disruption</option>
                    <option value="Recipe Overproduction">Recipe Overproduction</option>
                    <option value="Low Student Turnout">Low Student Turnout</option>
                    <option value="Hostel Event Elsewhere">Hostel Event Elsewhere</option>
                  </select>
                </div>

                {/* Remove button */}
                {dishRows.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeDishRow(idx)}
                    className="mt-3 sm:mt-4 p-2 text-stone-400 hover:text-red-600 transition"
                    title="Remove dish"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            ))}
          </div>

          <div className="mt-6 flex justify-end border-t border-[var(--border)] pt-5">
            <button
              type="submit"
              disabled={submitting}
              className="flex items-center gap-2 rounded-2xl bg-[#173D32] px-8 py-3 text-sm font-semibold text-white shadow-md transition hover:bg-[#102C24] disabled:opacity-50 dark:bg-[#D7F36B] dark:text-[#102C24]"
            >
              <Save className="h-4 w-4" />
              {submitting ? 'Validating & Persisting...' : 'Submit Kitchen Log'}
            </button>
          </div>
        </div>
      </form>

      {/* Voice Logger Helper Modal */}
      {voiceModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
              <div className="flex items-center gap-2 font-display text-sm font-bold text-[var(--text-primary)]">
                <Mic className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                Multilingual Voice Kitchen Logger
              </div>
              <button onClick={() => setVoiceModalOpen(false)} className="text-stone-400 hover:text-[var(--text-primary)]">
                ✕
              </button>
            </div>
            <p className="mt-3 text-xs text-[var(--text-secondary)] leading-relaxed">
              Speak cooking quantities in English, Hindi, or Telugu transliteration (e.g. <em>"annam 65 kilolu vandamu, 5 kilolu migilindi"</em>). Audio is parsed and discarded immediately; raw audio is never stored permanently.
            </p>

            <div className="mt-4 rounded-xl border border-stone-200 bg-[var(--surface-muted)] p-4 text-center">
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-800 animate-pulse">
                <Mic className="h-6 w-6" />
              </div>
              <div className="mt-2 text-xs font-semibold text-[var(--text-primary)]">Listening for kitchen cues...</div>
              <div className="mt-1 text-[11px] text-stone-500">Detected Language: English / Telugu Transliteration</div>
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <button
                onClick={() => setVoiceModalOpen(false)}
                className="rounded-xl border border-[var(--border)] px-4 py-2 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleVoiceSimulate}
                className="rounded-xl bg-[#173D32] px-4 py-2 text-xs font-semibold text-white dark:bg-[#D7F36B] dark:text-[#102C24]"
              >
                Apply Parsed Quantities
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Photo Estimation Modal */}
      {photoModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
              <div className="flex items-center gap-2 font-display text-sm font-bold text-[var(--text-primary)]">
                <Camera className="h-4 w-4 text-sky-600 dark:text-sky-400" />
                Calibrated Leftover Bin Photo Estimator
              </div>
              <button onClick={() => setPhotoModalOpen(false)} className="text-stone-400 hover:text-[var(--text-primary)]">
                ✕
              </button>
            </div>
            <p className="mt-3 text-xs text-[var(--text-secondary)] leading-relaxed">
              Provides heuristic fill-fraction estimation from calibrated standardized mess bins. <strong>Honesty Notice:</strong> Heuristic estimation is advisory only; manual scale measurements remain the gold standard.
            </p>
            <div className="mt-4 rounded-xl border border-dashed border-[var(--border)] p-6 text-center text-xs text-[var(--text-secondary)]">
              <Camera className="mx-auto h-8 w-8 text-stone-400 mb-2" />
              Upload bin photo for volume heuristic check
            </div>
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setPhotoModalOpen(false)}
                className="rounded-xl border border-[var(--border)] px-4 py-2 text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
