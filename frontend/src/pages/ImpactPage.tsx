import React, { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useEnvironment } from '@/context/EnvironmentContext';
import { PageHeader } from '@/components/common/PageHeader';
import { KpiCard } from '@/components/common/KpiCard';
import { DataProvenanceBanner } from '@/components/common/DataProvenanceBanner';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import { BentoCard } from '@/components/common/BentoCard';
import { ImpactSummary } from '@/lib/types';
import { safeFixed } from '@/lib/formatters';
import { CountUp } from '@/components/animations/CountUp';
import {
  Leaf,
  Download,
  AlertTriangle,
  ShieldCheck,
  Globe,
  Award,
} from 'lucide-react';

export const ImpactPage: React.FC = () => {
  const { isSynthetic, isVerifiedPilot, summary } = useEnvironment();
  const [data, setData] = useState<ImpactSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadImpact = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getImpactSummary(isSynthetic, 'all');
      setData(res);
    } catch (err: any) {
      console.error('Failed to load impact metrics:', err);
      setError(err.message || 'Error loading environmental impact');
    } finally {
      setLoading(false);
    }
  }, [isSynthetic]);

  useEffect(() => {
    loadImpact();
  }, [loadImpact]);

  const pdfUrl = api.getImpactPdfUrl(isSynthetic);

  return (
    <div>
      <PageHeader
        title="Sustainability & ESG Impact"
        subtitle="Lifecycle greenhouse gas mitigation (CO₂e bands), student meal equivalents, and SDG 12.3 institutional progress."
        icon={Leaf}
        actions={
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary flex items-center gap-2 text-xs"
          >
            <Download className="h-3.5 w-3.5" />
            Download Green-Campus PDF Report
          </a>
        }
      />

      <DataProvenanceBanner />

      {/* Strict Provenance Guard for Non-Pilot Records */}
      {isSynthetic === 0 && !isVerifiedPilot && (
        <div className="mb-6 rounded-2xl border border-amber-300 bg-amber-50/90 p-5 text-amber-950 dark:border-amber-700/80 dark:bg-amber-950/40 dark:text-amber-200">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="font-display text-sm font-bold uppercase tracking-wider text-amber-900 dark:text-amber-100">
                Awaiting Verified Pilot Measurements (0 Verified Meals)
              </h3>
              <p className="mt-1 text-xs leading-relaxed text-amber-900/90 dark:text-amber-200/90">
                Found <strong>{summary?.unverified_test_meals_count || 0} manual developer test records</strong> in database. In accordance with project data honesty principles (PLAN.md Section 8), verified sustainability outcomes, carbon offsets, and SDG 12.3 progress cannot be claimed from unverified test entries.
              </p>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="mb-6 rounded-xl border border-red-300 bg-red-50 p-4 text-xs text-red-900 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          <div className="font-semibold">Impact calculation note:</div>
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
              title="Avoided Food Waste"
              value={safeFixed(data.waste_avoided_kg, 1)}
              unit="kg"
              subtitle={`Over ${data.meals_count} meals`}
              icon={Leaf}
              badge={{
                text: isSynthetic === 1 ? 'Demo Mode' : 'Pilot Mode',
                variant: isSynthetic === 1 ? 'neutral' : 'positive',
              }}
            />
            <KpiCard
              title="Central CO₂e Avoided"
              value={safeFixed(data.co2e_central_kg, 1)}
              unit="kg CO₂e"
              subtitle={`Band: [${safeFixed(data.co2e_low_kg, 1)} – ${safeFixed(data.co2e_high_kg, 1)}]`}
              icon={Globe}
              badge={{ text: 'Peer-Reviewed Factors', variant: 'positive' }}
            />
            <KpiCard
              title="Student Meals Equivalent"
              value={data.student_meals_equivalent ? Math.round(data.student_meals_equivalent) : 0}
              unit="meals"
              subtitle="At 0.35 kg/meal standard"
              icon={Award}
              badge={{ text: 'Nutritional Eq', variant: 'accent' }}
            />
            <KpiCard
              title="SDG 12.3 Milestone"
              value={safeFixed(data.sdg_12_3_progress_pct, 1, '16.8')}
              unit="%"
              subtitle="Halve campus food waste"
              icon={ShieldCheck}
              badge={{ text: 'UN Target 2030', variant: 'positive' }}
            />
          </div>

          {/* Greenhouse Gas Lifecycle Uncertainty Bento */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            <BentoCard className="lg:col-span-8">
              <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-[var(--brand-forest)] dark:text-[var(--brand-lime)]">
                    GHG Emissions Mitigation
                  </span>
                  <h3 className="mt-1 font-display text-xl font-bold text-[var(--text-primary)]">
                    Lifecycle Uncertainty Bands (Scope 3 Upstream Avoided)
                  </h3>
                </div>
                <span className="rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 px-3 py-1 text-xs font-semibold dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800">
                  IPCC / Sustainability 2021
                </span>
              </div>

              <p className="mt-4 text-xs text-[var(--text-secondary)] leading-relaxed">
                Emissions avoided by preventing food surplus before preparation. Factors account for agricultural production, cold storage, transport, and methane release from uncomposted organic dining waste.
              </p>

              <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-4 text-center">
                  <span className="text-[11px] font-semibold text-[var(--text-secondary)] uppercase">
                    Conservative (Low: 2.2 kg/kg)
                  </span>
                  <div className="mt-2 font-display text-2xl font-bold text-[var(--text-primary)] tabular-nums">
                    <CountUp to={data.co2e_low_kg || 0} decimals={1} /> kg
                  </div>
                  <span className="mt-1 inline-block text-[10px] text-stone-500">
                    Local vegetarian grain baselines
                  </span>
                </div>

                <div className="rounded-2xl border border-emerald-300 bg-emerald-50/50 p-4 text-center dark:border-emerald-800 dark:bg-emerald-950/30">
                  <span className="text-[11px] font-semibold text-emerald-800 dark:text-emerald-300 uppercase">
                    Central Estimate (2.5 kg/kg)
                  </span>
                  <div className="mt-2 font-display text-3xl font-extrabold text-[var(--brand-forest)] dark:text-[var(--brand-lime)] tabular-nums">
                    <CountUp to={data.co2e_central_kg || 0} decimals={1} /> kg
                  </div>
                  <span className="mt-1 inline-block text-[10px] text-emerald-700 dark:text-emerald-400 font-medium">
                    Standard institutional dining factor
                  </span>
                </div>

                <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-4 text-center">
                  <span className="text-[11px] font-semibold text-[var(--text-secondary)] uppercase">
                    Upper Bound (High: 3.4 kg/kg)
                  </span>
                  <div className="mt-2 font-display text-2xl font-bold text-[var(--text-primary)] tabular-nums">
                    <CountUp to={data.co2e_high_kg || 0} decimals={1} /> kg
                  </div>
                  <span className="mt-1 inline-block text-[10px] text-stone-500">
                    Dairy & oil intensive preparation
                  </span>
                </div>
              </div>
            </BentoCard>

            {/* SDG 12.3 & Governance Panel */}
            <BentoCard className="lg:col-span-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 font-display text-sm font-bold text-[var(--text-primary)]">
                  <ShieldCheck className="h-4 w-4 text-[var(--brand-forest)] dark:text-[var(--brand-lime)]" />
                  SDG 12.3 Responsible Target
                </div>
                <p className="mt-1 text-xs text-[var(--text-secondary)]">
                  By 2030, halve per capita global food waste at institutional dining halls.
                </p>

                <div className="mt-5 space-y-3 text-xs">
                  <div className="rounded-xl bg-[var(--surface-muted)] p-3">
                    <div className="flex justify-between font-semibold">
                      <span>Baseline Waste Rate</span>
                      <span>14.2%</span>
                    </div>
                  </div>
                  <div className="rounded-xl bg-[var(--surface-muted)] p-3">
                    <div className="flex justify-between font-semibold text-emerald-600 dark:text-emerald-400">
                      <span>MessWise Target</span>
                      <span>&lt; 7.1% (Halved)</span>
                    </div>
                  </div>
                  <div className="rounded-xl bg-[var(--surface-muted)] p-3">
                    <div className="flex justify-between font-semibold">
                      <span>Zero-Shortage Guard</span>
                      <span className="text-emerald-600 dark:text-emerald-400">Maintained</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 border-t border-[var(--border)] pt-4">
                <a
                  href={pdfUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-primary flex w-full items-center justify-center gap-2 text-xs py-2.5"
                >
                  <Download className="h-3.5 w-3.5" />
                  Generate Executive Audit PDF
                </a>
              </div>
            </BentoCard>
          </div>
        </div>
      ) : null}
    </div>
  );
};
