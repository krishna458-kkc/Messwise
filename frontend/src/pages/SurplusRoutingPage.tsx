import React, { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useEnvironment } from '@/context/EnvironmentContext';
import { PageHeader } from '@/components/common/PageHeader';
import { DataProvenanceBanner } from '@/components/common/DataProvenanceBanner';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import { SurplusAlert } from '@/lib/types';
import { safeFixed } from '@/lib/formatters';
import { AnimatedList } from '@/components/animations/AnimatedList';
import {
  Clock,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Thermometer,
  RefreshCw,
} from 'lucide-react';

export const SurplusRoutingPage: React.FC = () => {
  const { isSynthetic } = useEnvironment();
  const [alerts, setAlerts] = useState<SurplusAlert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Safety logging state
  const [selectedAlertId, setSelectedAlertId] = useState<number | null>(null);
  const [tempC, setTempC] = useState<number>(65);
  const [hoursHeld, setHoursHeld] = useState<number>(1.5);
  const [decisionNotes, setDecisionNotes] = useState<string>('');

  const loadAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getSurplusAlerts(isSynthetic);
      setAlerts(res.alerts || []);
    } catch (err: any) {
      console.error('Failed to load surplus alerts:', err);
      setError(err.message || 'Error loading surplus alerts');
    } finally {
      setLoading(false);
    }
  }, [isSynthetic]);

  useEffect(() => {
    loadAlerts();
  }, [loadAlerts]);

  const handleRecordSafety = async (alertId: number) => {
    try {
      await api.recordSurplusSafety(alertId, {
        temperature_c: tempC,
        hours_since_cooking: hoursHeld,
      });
      await loadAlerts();
      setSelectedAlertId(null);
    } catch (err: any) {
      alert(`Safety logging failed: ${err.message}`);
    }
  };

  const handleDecision = async (alertId: number, decision: string) => {
    try {
      await api.recordSurplusDecision(alertId, decision, decisionNotes);
      await loadAlerts();
    } catch (err: any) {
      alert(`Decision recording failed: ${err.message}`);
    }
  };

  return (
    <div>
      <PageHeader
        title="Surplus Routing & Food-Safety Clock"
        subtitle="Time-temperature safety gating and responsible food donation dispatch."
        icon={Clock}
        actions={
          <button
            onClick={loadAlerts}
            className="btn-primary flex items-center gap-2 text-xs"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Check Active Clocks
          </button>
        }
      />

      <DataProvenanceBanner />

      {/* Food Safety Rules Banner */}
      <div className="mb-6 rounded-2xl border border-stone-200 bg-[var(--surface)] p-4 text-xs text-[var(--text-secondary)] shadow-xs dark:border-stone-800">
        <div className="flex items-start gap-3">
          <ShieldCheck className="h-5 w-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-[var(--text-primary)]">Strict Food-Safety Safeguards:</span>
            <p className="mt-0.5 leading-relaxed">
              Cooked leftovers must remain above 60°C (hot hold) or rapidly chilled below 5°C. Cooked items held at ambient room temperature for more than 2 hours are <strong>strictly ineligible for donation</strong> to protect community health. Re-serving cooked food to students is prohibited.
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-xl border border-red-300 bg-red-50 p-4 text-xs text-red-900 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          <div className="font-semibold">Surplus routing note:</div>
          <p className="mt-1">{error}</p>
        </div>
      )}

      {loading ? (
        <LoadingSkeleton className="h-64" count={2} />
      ) : (
        <div className="space-y-6">
          {/* Active Alerts List */}
          <div className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
              <div>
                <h3 className="font-display text-base font-bold text-[var(--text-primary)]">
                  Active Surplus Items & Safety Clocks
                </h3>
                <p className="text-xs text-[var(--text-secondary)]">
                  Monitored kitchen batches requiring time-temperature validation and manager dispatch
                </p>
              </div>
              <span className="text-xs font-semibold text-stone-500">
                {alerts.length} logged events
              </span>
            </div>

            <div className="mt-5 space-y-4">
              {alerts.length === 0 ? (
                <div className="py-10 text-center text-xs text-[var(--text-secondary)]">
                  No active surplus alerts in the database for this environment.
                </div>
              ) : (
                <AnimatedList className="space-y-4">
                  {alerts.map((alert) => {
                    const isSafe = alert.eligible_for_donation;
                    const isBlocked = alert.safety_status === 'blocked' || alert.safety_status === 'expired';

                    return (
                      <div
                        key={alert.id}
                        className="rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-5 transition hover:border-[var(--brand-forest)]/30 dark:hover:border-[var(--brand-lime)]/30"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                          <div>
                            <div className="flex items-center gap-2.5">
                              <h4 className="font-display text-base font-bold text-[var(--text-primary)]">
                                {alert.dish_name}
                              </h4>
                              <span className="rounded-full bg-[var(--surface)] border border-[var(--border)] px-2.5 py-0.5 text-xs font-semibold tabular-nums text-[var(--text-primary)]">
                                {safeFixed(alert.quantity_kg, 1)} kg
                              </span>
                              <span
                                className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase border ${
                                  isSafe
                                    ? 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800'
                                    : isBlocked
                                    ? 'bg-red-50 text-red-800 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800'
                                    : 'bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800'
                                }`}
                              >
                                {alert.safety_status}
                              </span>
                            </div>
                            <div className="mt-1 text-xs text-[var(--text-secondary)]">
                              Meal: {alert.meal_date} ({alert.meal_type}) • Logged at: {new Date(alert.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </div>
                          </div>

                          {/* Safety Clock & Temperature Display */}
                          <div className="flex items-center gap-3">
                            <div className="flex items-center gap-1.5 rounded-xl bg-[var(--surface)] border border-[var(--border)] px-3 py-1.5 text-xs">
                              <Thermometer className="h-4 w-4 text-orange-500" />
                              <span className="font-semibold tabular-nums">
                                {alert.temperature_c != null ? `${alert.temperature_c}°C` : 'Temp Pending'}
                              </span>
                            </div>

                            <div className="flex items-center gap-1.5 rounded-xl bg-[var(--surface)] border border-[var(--border)] px-3 py-1.5 text-xs">
                              <Clock className="h-4 w-4 text-sky-500 animate-pulse" />
                              <span className="font-semibold tabular-nums">
                                {alert.hours_since_cooking != null ? `${alert.hours_since_cooking}h hold` : 'Clock Pending'}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Action Bar for Manager */}
                        <div className="mt-4 flex flex-wrap items-center justify-between border-t border-[var(--border)] pt-3 text-xs">
                          <div className="text-[11px] text-[var(--text-secondary)]">
                            {isSafe ? (
                              <span className="text-emerald-700 dark:text-emerald-400 font-semibold flex items-center gap-1">
                                <CheckCircle2 className="h-3.5 w-3.5" />
                                Eligible for local audited redistribution
                              </span>
                            ) : (
                              <span className="text-red-700 dark:text-red-400 font-semibold flex items-center gap-1">
                                <XCircle className="h-3.5 w-3.5" />
                                Donation blocked: Safety window threshold exceeded
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => setSelectedAlertId(selectedAlertId === alert.id ? null : alert.id)}
                              className="btn-secondary text-xs py-1 px-3"
                            >
                              Log Temp & Hold Time
                            </button>

                            {isSafe && alert.decision !== 'approved_donation' && (
                              <button
                                onClick={() => handleDecision(alert.id, 'approved_donation')}
                                className="rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1 text-xs font-semibold shadow-xs transition"
                              >
                                Approve Donation
                              </button>
                            )}

                            <button
                              onClick={() => handleDecision(alert.id, 'composted')}
                              className="btn-secondary text-xs py-1 px-3"
                            >
                              Route to Compost
                            </button>
                          </div>
                        </div>

                        {/* Expandable Safety Log Panel */}
                        {selectedAlertId === alert.id && (
                          <div className="mt-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 text-xs">
                            <div className="font-semibold text-[var(--text-primary)]">
                              Record Inspection Reading for {alert.dish_name}
                            </div>
                            <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
                              <div>
                                <label className="block text-[11px] text-[var(--text-secondary)] font-medium">
                                  Core Temperature (°C)
                                </label>
                                <input
                                  type="number"
                                  value={tempC}
                                  onChange={(e) => setTempC(parseFloat(e.target.value) || 0)}
                                  className="mt-1 w-full rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-2.5 py-1.5 text-xs font-bold"
                                />
                              </div>
                              <div>
                                <label className="block text-[11px] text-[var(--text-secondary)] font-medium">
                                  Hours Held Since End of Service
                                </label>
                                <input
                                  type="number"
                                  step="0.5"
                                  value={hoursHeld}
                                  onChange={(e) => setHoursHeld(parseFloat(e.target.value) || 0)}
                                  className="mt-1 w-full rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-2.5 py-1.5 text-xs font-bold"
                                />
                              </div>
                              <div className="sm:col-span-2">
                                <label className="block text-[11px] text-[var(--text-secondary)] font-medium">
                                  Optional Dispatch / Routing Justification Note
                                </label>
                                <input
                                  type="text"
                                  placeholder="e.g. Verified by head cook, stored in insulated warmers"
                                  value={decisionNotes}
                                  onChange={(e) => setDecisionNotes(e.target.value)}
                                  className="mt-1 w-full rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-2.5 py-1.5 text-xs"
                                />
                              </div>
                            </div>
                            <div className="mt-3 flex justify-end gap-2">
                              <button
                                onClick={() => setSelectedAlertId(null)}
                                className="btn-secondary text-xs py-1 px-3"
                              >
                                Cancel
                              </button>
                              <button
                                onClick={() => handleRecordSafety(alert.id)}
                                className="btn-primary text-xs py-1 px-3"
                              >
                                Save Safety Inspection
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </AnimatedList>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
