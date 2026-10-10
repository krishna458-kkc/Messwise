import React, { useState } from 'react';
import { PublicNavbar } from '@/components/common/PublicNavbar';
import { PublicFooter } from '@/components/common/PublicFooter';
import { StaggerText } from '@/components/common/StaggerText';
import { BentoCard } from '@/components/common/BentoCard';
import {
  TrendingUp,
  Calculator,
  Utensils,
  Scale,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Users,
  Leaf,
  Clock,
  PlayCircle,
  BarChart2,
  Lock,
  Compass,
} from 'lucide-react';

interface LandingPageProps {
  onOpenApp: (tab?: string) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onOpenApp }) => {
  // Client-side interactive planning demonstration state
  const [demoTurnout, setDemoTurnout] = useState<number>(420);
  const [demoServiceLevel, setDemoServiceLevel] = useState<number>(95);

  // Dynamic illustrative calculations (safe client-side, zero database side-effects)
  const dalPerHeadKg = 0.15;
  const ricePerHeadKg = 0.18;
  const bufferMultipliers: Record<number, number> = { 90: 1.04, 95: 1.08, 99: 1.15 };
  const multiplier = bufferMultipliers[demoServiceLevel] || 1.08;

  const plannedDalKg = Math.round(demoTurnout * dalPerHeadKg * multiplier * 10) / 10;
  const plannedRiceKg = Math.round(demoTurnout * ricePerHeadKg * multiplier * 10) / 10;
  const legacyFixedDalKg = Math.round(500 * dalPerHeadKg * 1.15 * 10) / 10; // Old 100% capacity habit
  const avoidedSurplusKg = Math.max(0, Math.round((legacyFixedDalKg - plannedDalKg) * 10) / 10);

  return (
    <div className="min-h-screen bg-[var(--background)] transition-colors">
      <PublicNavbar onOpenApp={() => onOpenApp('dashboard')} />

      {/* Hero Section */}
      <section className="relative overflow-hidden aurora-bg px-4 pt-16 pb-20 sm:px-6 lg:px-8 lg:pt-24 lg:pb-32">
        <div className="mx-auto max-w-7xl">
          <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-12 lg:gap-8">
            {/* Left Copy */}
            <div className="lg:col-span-7">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-300 bg-emerald-50/80 px-3.5 py-1 text-xs font-semibold text-emerald-900 dark:border-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                Closed-Loop Food Operations Intelligence
              </div>

              <h1 className="mt-6 font-display text-4xl font-extrabold tracking-tight text-[#102C24] dark:text-[#F6F5EE] sm:text-5xl lg:text-6xl leading-[1.1]">
                <StaggerText text="Feed the right number." delay={0.1} />
                <br />
                <span className="text-[#173D32] dark:text-[#D7F36B]">
                  <StaggerText text="Waste less." delay={0.25} />
                </span>{' '}
                <StaggerText text="Serve everyone." delay={0.4} />
              </h1>

              <p className="mt-6 text-base text-[var(--text-secondary)] sm:text-lg max-w-xl leading-relaxed">
                MessWise forecasts meal demand with conformal uncertainty bands, plans quantities dish by dish at operator-chosen service levels, and learns from measured kitchen outcomes—helping institutional dining halls cut food waste without shortage risk.
              </p>

              {/* CTAs */}
              <div className="mt-8 flex flex-wrap items-center gap-4">
                <button
                  onClick={() => onOpenApp('dashboard')}
                  className="flex items-center gap-2.5 rounded-2xl bg-[#173D32] px-6 py-3.5 text-sm font-semibold text-white shadow-md transition hover:bg-[#102C24] hover:scale-[1.02] dark:bg-[#D7F36B] dark:text-[#102C24] dark:hover:bg-[#C5E552]"
                >
                  Launch Operational Workspace
                  <ArrowRight className="h-4 w-4" />
                </button>
                <a
                  href="#demo"
                  className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] px-6 py-3.5 text-sm font-semibold text-[var(--text-primary)] shadow-xs transition hover:bg-[var(--surface-muted)]"
                >
                  Explore Interactive Demo
                </a>
              </div>

              {/* Trust markers */}
              <div className="mt-10 flex flex-wrap items-center gap-6 text-xs text-[var(--text-secondary)]">
                <span className="flex items-center gap-1.5 font-medium">
                  <ShieldCheck className="h-4 w-4 text-[#173D32] dark:text-[#D7F36B]" />
                  Zero-Look-Ahead Guarantee
                </span>
                <span className="flex items-center gap-1.5 font-medium">
                  <CheckCircle2 className="h-4 w-4 text-[#173D32] dark:text-[#D7F36B]" />
                  Conformal 80% Intervals
                </span>
                <span className="flex items-center gap-1.5 font-medium">
                  <Scale className="h-4 w-4 text-[#173D32] dark:text-[#D7F36B]" />
                  Kaplan–Meier Appetite Learning
                </span>
              </div>
            </div>

            {/* Right: Custom Food Loop SVG Illustration & Preview */}
            <div className="lg:col-span-5">
              <div className="relative mx-auto max-w-md lg:max-w-none">
                <div className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xl dark:shadow-2xl">
                  {/* Food Intelligence Loop SVG */}
                  <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
                    <div className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full bg-emerald-500" />
                      <span className="font-display text-xs font-bold uppercase tracking-wider text-[var(--text-primary)]">
                        Continuous Operational Feedback
                      </span>
                    </div>
                    <span className="text-[10px] font-semibold text-[var(--text-secondary)]">
                      Closed Loop
                    </span>
                  </div>

                  <div className="relative my-6 flex items-center justify-center">
                    <svg viewBox="0 0 240 240" className="w-56 h-56">
                      {/* Outer circular loop */}
                      <circle
                        cx="120"
                        cy="120"
                        r="90"
                        fill="none"
                        stroke="currentColor"
                        className="text-stone-200 dark:text-stone-800"
                        strokeWidth="8"
                      />
                      <circle
                        cx="120"
                        cy="120"
                        r="90"
                        fill="none"
                        stroke="#D7F36B"
                        strokeWidth="8"
                        strokeDasharray="140 30"
                        strokeLinecap="round"
                        className="transition-all duration-1000"
                      />
                      {/* Center Hub */}
                      <circle cx="120" cy="120" r="45" fill="#173D32" />
                      <text
                        x="120"
                        y="116"
                        textAnchor="middle"
                        fill="#D7F36B"
                        fontSize="12"
                        fontWeight="bold"
                        fontFamily="Sora, sans-serif"
                      >
                        MessWise
                      </text>
                      <text
                        x="120"
                        y="132"
                        textAnchor="middle"
                        fill="#E7EEE5"
                        fontSize="9"
                        fontFamily="Inter, sans-serif"
                      >
                        AI ENGINE
                      </text>

                      {/* 5 Stage Nodes */}
                      {/* 1. Predict (Top) */}
                      <circle cx="120" cy="30" r="16" fill="#173D32" stroke="#D7F36B" strokeWidth="2" />
                      <text x="120" y="34" textAnchor="middle" fill="#FFFFFF" fontSize="9" fontWeight="bold">1</text>
                      {/* 2. Plan (Right Top) */}
                      <circle cx="205" cy="90" r="16" fill="#173D32" stroke="#D7F36B" strokeWidth="2" />
                      <text x="205" y="94" textAnchor="middle" fill="#FFFFFF" fontSize="9" fontWeight="bold">2</text>
                      {/* 3. Cook (Right Bottom) */}
                      <circle cx="175" cy="190" r="16" fill="#173D32" stroke="#D7F36B" strokeWidth="2" />
                      <text x="175" y="194" textAnchor="middle" fill="#FFFFFF" fontSize="9" fontWeight="bold">3</text>
                      {/* 4. Measure (Left Bottom) */}
                      <circle cx="65" cy="190" r="16" fill="#173D32" stroke="#D7F36B" strokeWidth="2" />
                      <text x="65" y="194" textAnchor="middle" fill="#FFFFFF" fontSize="9" fontWeight="bold">4</text>
                      {/* 5. Learn (Left Top) */}
                      <circle cx="35" cy="90" r="16" fill="#173D32" stroke="#D7F36B" strokeWidth="2" />
                      <text x="35" y="94" textAnchor="middle" fill="#FFFFFF" fontSize="9" fontWeight="bold">5</text>
                    </svg>
                  </div>

                  {/* Operational Preview Details */}
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="rounded-xl bg-[var(--surface-muted)] p-3">
                      <span className="text-[10px] font-medium text-[var(--text-secondary)]">Demand Forecast</span>
                      <div className="font-display text-base font-bold text-[var(--text-primary)]">
                        420 ± 18 <span className="text-xs font-normal text-stone-500">students</span>
                      </div>
                    </div>
                    <div className="rounded-xl bg-[var(--surface-muted)] p-3">
                      <span className="text-[10px] font-medium text-[var(--text-secondary)]">Service Level</span>
                      <div className="font-display text-base font-bold text-emerald-600 dark:text-emerald-400">
                        95.0% <span className="text-xs font-normal text-stone-500">zero runout</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section A: The 5-Stage Closed Loop */}
      <section id="workflow" className="border-t border-[var(--border)] py-20 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="text-center max-w-2xl mx-auto">
            <h2 className="font-display text-3xl font-bold tracking-tight text-[var(--text-primary)] sm:text-4xl">
              How MessWise Works: The 5-Stage Cycle
            </h2>
            <p className="mt-3 text-sm text-[var(--text-secondary)]">
              Preventing institutional food waste requires closing the operational information loop from prediction to kitchen reality.
            </p>
          </div>

          <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-5">
            {[
              {
                step: '01',
                title: 'Predict',
                icon: TrendingUp,
                desc: 'Forecasts upcoming meal headcount with rigorous 80% conformal uncertainty intervals and exam/holiday calendar cues.',
              },
              {
                step: '02',
                title: 'Plan',
                icon: Calculator,
                desc: 'Recommends per-dish cooking quantities at manager-chosen service levels (90%, 95%, 99%) using Newsvendor math.',
              },
              {
                step: '03',
                title: 'Cook',
                icon: Utensils,
                desc: 'Supports kitchen cooks with rapid touch/voice/photo logging, structured override reasons, and real-time guidance.',
              },
              {
                step: '04',
                title: 'Measure',
                icon: Scale,
                desc: 'Captures actual leftover quantities and run-out occurrences immediately after service in under 60 seconds.',
              },
              {
                step: '05',
                title: 'Learn',
                icon: Sparkles,
                desc: 'Updates per-head consumption rates using Kaplan–Meier estimators that prevent shortage-bias distortion.',
              },
            ].map((s) => {
              const Icon = s.icon;
              return (
                <div
                  key={s.step}
                  className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 transition hover:border-[#173D32]/40 dark:hover:border-[#D7F36B]/40"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-display text-xs font-bold text-[#173D32] dark:text-[#D7F36B]">
                      {s.step}
                    </span>
                    <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[var(--surface-muted)] text-[var(--brand-primary)] dark:text-[#D7F36B]">
                      <Icon className="h-4 w-4" />
                    </div>
                  </div>
                  <h3 className="mt-4 font-display text-lg font-bold text-[var(--text-primary)]">
                    {s.title}
                  </h3>
                  <p className="mt-2 text-xs leading-relaxed text-[var(--text-secondary)]">
                    {s.desc}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Section B: Bento Feature Grid */}
      <section id="features" className="border-t border-[var(--border)] bg-[var(--surface-muted)]/50 py-20 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="text-center max-w-2xl mx-auto">
            <span className="text-xs font-semibold uppercase tracking-wider text-[#173D32] dark:text-[#D7F36B]">
              Core Capabilities
            </span>
            <h2 className="mt-2 font-display text-3xl font-bold tracking-tight text-[var(--text-primary)] sm:text-4xl">
              Engineered for Institutional Kitchen Reality
            </h2>
            <p className="mt-3 text-sm text-[var(--text-secondary)]">
              Every feature solves a specific failure mode in university and hostel mess operations.
            </p>
          </div>

          <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-3">
            {/* Bento Card 1: Forecasting & Confidence */}
            <BentoCard className="md:col-span-2">
              <div className="flex items-center gap-3 text-[#173D32] dark:text-[#D7F36B]">
                <TrendingUp className="h-5 w-5" />
                <span className="text-xs font-bold uppercase tracking-wider">Module A: Demand Intelligence</span>
              </div>
              <h3 className="mt-3 font-display text-2xl font-bold text-[var(--text-primary)]">
                Conformal 80% Uncertainty Bands
              </h3>
              <p className="mt-2 text-sm text-[var(--text-secondary)] max-w-xl">
                Point predictions alone risk disastrous kitchen shortages. MessWise bounds each forecast within an explicit interval [h_lo, h_hi], comparing performance against same-meal last-week and 14-day trailing averages.
              </p>
              <div className="mt-6 flex flex-wrap gap-2 text-xs">
                <span className="rounded-lg bg-[var(--surface-muted)] px-3 py-1 font-medium">Ridge Regularization</span>
                <span className="rounded-lg bg-[var(--surface-muted)] px-3 py-1 font-medium">Holiday & Exam Adjustments</span>
                <span className="rounded-lg bg-[var(--surface-muted)] px-3 py-1 font-medium">Time-Ordered Historical Validation</span>
              </div>
            </BentoCard>

            {/* Bento Card 2: Per-Dish Newsvendor Optimizer */}
            <BentoCard>
              <div className="flex items-center gap-3 text-[#173D32] dark:text-[#D7F36B]">
                <Calculator className="h-5 w-5" />
                <span className="text-xs font-bold uppercase tracking-wider">Module B: Planning</span>
              </div>
              <h3 className="mt-3 font-display text-xl font-bold text-[var(--text-primary)]">
                Service-Level Slider
              </h3>
              <p className="mt-2 text-xs text-[var(--text-secondary)] leading-relaxed">
                Dial service reliability between 90%, 95%, and 99%. MessWise calculates the optimal buffer for each dish based on consumption variance and unit cost.
              </p>
              <div className="mt-5 rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] p-3 text-xs">
                <div className="flex justify-between font-semibold">
                  <span>95% Reliability</span>
                  <span className="text-emerald-600 dark:text-emerald-400">Optimal Buffer</span>
                </div>
                <div className="mt-1 text-[11px] text-[var(--text-secondary)]">
                  Prevents undercooking high-cost mains while curbing side dish surplus.
                </div>
              </div>
            </BentoCard>

            {/* Bento Card 3: Counterfactual Simulator & Blind Reveal */}
            <BentoCard>
              <div className="flex items-center gap-3 text-[#173D32] dark:text-[#D7F36B]">
                <PlayCircle className="h-5 w-5" />
                <span className="text-xs font-bold uppercase tracking-wider">Module E: Proof Engine</span>
              </div>
              <h3 className="mt-3 font-display text-xl font-bold text-[var(--text-primary)]">
                Blind Forecast Reveal
              </h3>
              <p className="mt-2 text-xs text-[var(--text-secondary)] leading-relaxed">
                Freeze historical decisions before meal cutoff time, lock the forecast cryptographically, and reveal actual attendance to audit savings with zero hindsight bias.
              </p>
            </BentoCard>

            {/* Bento Card 4: Food-Safety Routing Clock */}
            <BentoCard className="md:col-span-2">
              <div className="flex items-center gap-3 text-[#173D32] dark:text-[#D7F36B]">
                <Clock className="h-5 w-5" />
                <span className="text-xs font-bold uppercase tracking-wider">Module F: Food Safety</span>
              </div>
              <h3 className="mt-3 font-display text-2xl font-bold text-[var(--text-primary)]">
                Four-Hour Food-Safety Clock & Donation Routing
              </h3>
              <p className="mt-2 text-sm text-[var(--text-secondary)] max-w-xl">
                Surplus is routed safely or blocked definitively. When food exceeds 2 hours at ambient temperature or 4 hours total hold, donation eligibility is blocked automatically to protect vulnerable community recipients.
              </p>
              <div className="mt-6 flex flex-wrap gap-2 text-xs">
                <span className="rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 px-3 py-1 font-medium dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800">
                  Time-Temperature Gating
                </span>
                <span className="rounded-lg bg-stone-100 text-stone-700 px-3 py-1 font-medium dark:bg-stone-800 dark:text-stone-300">
                  Manager Authorization Required
                </span>
                <span className="rounded-lg bg-stone-100 text-stone-700 px-3 py-1 font-medium dark:bg-stone-800 dark:text-stone-300">
                  Zero Cooked Re-serving Rule
                </span>
              </div>
            </BentoCard>
          </div>
        </div>
      </section>

      {/* Section C: Interactive Planning Demonstration (Safe Client-Side) */}
      <section id="demo" className="border-t border-[var(--border)] py-20 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-5xl">
          <div className="text-center">
            <span className="rounded-full border border-stone-300 bg-stone-100 px-3 py-1 text-xs font-semibold text-stone-800 dark:border-stone-700 dark:bg-stone-800 dark:text-stone-200">
              Interactive Sandbox (Safe Client-Side Demo)
            </span>
            <h2 className="mt-3 font-display text-3xl font-bold tracking-tight text-[var(--text-primary)] sm:text-4xl">
              Experience the Planning Optimizer
            </h2>
            <p className="mt-2 text-sm text-[var(--text-secondary)]">
              Adjust student turnout and service level to see how dynamic planning eliminates overproduction.
            </p>
          </div>

          <div className="mt-12 rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 sm:p-8 shadow-sm">
            <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
              {/* Sliders */}
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-[var(--text-primary)]">Forecast Student Attendance:</span>
                    <span className="font-display text-sm text-[#173D32] dark:text-[#D7F36B] font-bold">
                      {demoTurnout} students
                    </span>
                  </div>
                  <input
                    type="range"
                    min={250}
                    max={550}
                    step={10}
                    value={demoTurnout}
                    onChange={(e) => setDemoTurnout(parseInt(e.target.value, 10))}
                    className="mt-2 w-full accent-[#173D32] dark:accent-[#D7F36B]"
                  />
                  <div className="flex justify-between text-[10px] text-[var(--text-secondary)]">
                    <span>250 (Exam/Vacation)</span>
                    <span>400 (Typical)</span>
                    <span>550 (Full Capacity)</span>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-[var(--text-primary)]">Target Service Reliability:</span>
                    <span className="font-display text-sm text-emerald-600 dark:text-emerald-400 font-bold">
                      {demoServiceLevel}% Zero-Shortage
                    </span>
                  </div>
                  <div className="mt-2 grid grid-cols-3 gap-2">
                    {[90, 95, 99].map((lvl) => (
                      <button
                        key={lvl}
                        onClick={() => setDemoServiceLevel(lvl)}
                        className={`rounded-xl py-2 text-xs font-semibold border transition ${
                          demoServiceLevel === lvl
                            ? 'border-[#173D32] bg-[#173D32] text-white dark:border-[#D7F36B] dark:bg-[#D7F36B] dark:text-[#102C24]'
                            : 'border-[var(--border)] bg-[var(--surface-muted)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                        }`}
                      >
                        {lvl}% Service
                      </button>
                    ))}
                  </div>
                </div>

                <div className="rounded-xl border border-stone-200 bg-stone-50 p-3.5 text-xs text-stone-700 dark:border-stone-800 dark:bg-stone-900 dark:text-stone-300">
                  <div className="font-semibold text-stone-900 dark:text-stone-100">Client-Side Guarantee:</div>
                  <p className="mt-0.5 leading-relaxed text-[11px]">
                    This sandbox evaluates locally in your browser. It does not write to the SQLite production database or alter historical training logs.
                  </p>
                </div>
              </div>

              {/* Live Output Card */}
              <div className="flex flex-col justify-between rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-6">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)]">
                      Optimized Cooking Quantities
                    </span>
                    <span className="rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 px-2.5 py-0.5 text-[10px] font-semibold">
                      Newsvendor Solved
                    </span>
                  </div>

                  <div className="mt-4 space-y-3">
                    <div className="flex items-center justify-between rounded-xl bg-[var(--surface)] p-3 text-xs">
                      <div>
                        <div className="font-semibold text-[var(--text-primary)]">Dal Tadka (Main Protein)</div>
                        <div className="text-[10px] text-[var(--text-secondary)]">Standard Portion: 150g / head</div>
                      </div>
                      <div className="text-right">
                        <div className="font-display text-base font-bold text-[#173D32] dark:text-[#D7F36B]">
                          {plannedDalKg} kg
                        </div>
                        <div className="text-[10px] text-stone-400 line-through">
                          Legacy: {legacyFixedDalKg} kg
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between rounded-xl bg-[var(--surface)] p-3 text-xs">
                      <div>
                        <div className="font-semibold text-[var(--text-primary)]">Steamed Basmati Rice</div>
                        <div className="text-[10px] text-[var(--text-secondary)]">Standard Portion: 180g / head</div>
                      </div>
                      <div className="text-right">
                        <div className="font-display text-base font-bold text-[#173D32] dark:text-[#D7F36B]">
                          {plannedRiceKg} kg
                        </div>
                        <div className="text-[10px] text-stone-400 line-through">
                          Legacy: 103.5 kg
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-6 border-t border-[var(--border)] pt-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[var(--text-secondary)]">Preventable Surplus Avoided:</span>
                    <span className="font-display text-lg font-bold text-emerald-600 dark:text-emerald-400">
                      ~{avoidedSurplusKg} kg avoided this meal
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section D: Trust & Methodology */}
      <section id="methodology" className="border-t border-[var(--border)] bg-[var(--surface-muted)]/40 py-20 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="text-center max-w-2xl mx-auto">
            <span className="text-xs font-semibold uppercase tracking-wider text-[#173D32] dark:text-[#D7F36B]">
              Methodology & Rigor
            </span>
            <h2 className="mt-2 font-display text-3xl font-bold tracking-tight text-[var(--text-primary)] sm:text-4xl">
              Three-Tier Data Honesty Architecture
            </h2>
            <p className="mt-3 text-sm text-[var(--text-secondary)]">
              MessWise never fabricates zero or positive savings claims without real verified evidence.
            </p>
          </div>

          <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="rounded-2xl border border-violet-200 bg-[var(--surface)] p-6 dark:border-violet-800/60">
              <span className="inline-block rounded-full bg-violet-100 text-violet-800 dark:bg-violet-950/60 dark:text-violet-300 px-3 py-1 text-xs font-semibold">
                Tier 1: Synthetic Benchmark
              </span>
              <h3 className="mt-4 font-display text-lg font-bold text-[var(--text-primary)]">
                28 Historical Demonstration Meals
              </h3>
              <p className="mt-2 text-xs leading-relaxed text-[var(--text-secondary)]">
                Generated strictly to validate statistical routines, Newsvendor solvers, and workflow mechanics during onboarding. Never presented as real-world institutional impact.
              </p>
            </div>

            <div className="rounded-2xl border border-amber-200 bg-[var(--surface)] p-6 dark:border-amber-800/60">
              <span className="inline-block rounded-full bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 px-3 py-1 text-xs font-semibold">
                Tier 2: Unverified Test Entries
              </span>
              <h3 className="mt-4 font-display text-lg font-bold text-[var(--text-primary)]">
                Operational Developer Entries
              </h3>
              <p className="mt-2 text-xs leading-relaxed text-[var(--text-secondary)]">
                Manual developer test records with <code>is_synthetic = 0</code> are strictly labeled <code>unverified_test</code>. They cannot generate carbon reduction claims or pass pilot evidence thresholds.
              </p>
            </div>

            <div className="rounded-2xl border border-emerald-200 bg-[var(--surface)] p-6 dark:border-emerald-800/60">
              <span className="inline-block rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 px-3 py-1 text-xs font-semibold">
                Tier 3: Verified Pilot Data
              </span>
              <h3 className="mt-4 font-display text-lg font-bold text-[var(--text-primary)]">
                Supervised Kitchen Measurements
              </h3>
              <p className="mt-2 text-xs leading-relaxed text-[var(--text-secondary)]">
                Only records authenticated with supervisory protocol and actual kitchen scales qualify as verified pilot data. Used to compute peer-reviewed CO₂e lifecycle bands and matched-pair reports.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Section E: Stakeholder Roles */}
      <section id="stakeholders" className="border-t border-[var(--border)] py-20 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="text-center max-w-2xl mx-auto">
            <h2 className="font-display text-3xl font-bold tracking-tight text-[var(--text-primary)] sm:text-4xl">
              Built for Every Dining Hall Stakeholder
            </h2>
            <p className="mt-3 text-sm text-[var(--text-secondary)]">
              Tailored workflows for each participant in institutional food operations.
            </p>
          </div>

          <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {[
              {
                role: 'Kitchen Cooks',
                desc: 'Fast, touch-friendly, multilingual voice and photo leftover logging in English, Hindi, and Telugu.',
                action: () => onOpenApp('kitchen'),
                actionLabel: 'Kitchen Mode',
              },
              {
                role: 'Mess Managers',
                desc: 'Service-level sliders, dish-by-dish buffer optimization, procurement lists, and surplus routing oversight.',
                action: () => onOpenApp('planner'),
                actionLabel: 'Planner Mode',
              },
              {
                role: 'Campus Auditors',
                desc: 'Immutable audit logs, cryptographic blind forecast verification, and matched-pair pilot governance.',
                action: () => onOpenApp('reports'),
                actionLabel: 'Audit & Reports',
              },
              {
                role: 'Students & Community',
                desc: 'Arrival check-ins, transparent waste impact wall, and food-safe surplus redistribution alerts.',
                action: () => onOpenApp('impact'),
                actionLabel: 'Impact Wall',
              },
            ].map((s) => (
              <div
                key={s.role}
                className="flex flex-col justify-between rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs"
              >
                <div>
                  <h3 className="font-display text-base font-bold text-[var(--text-primary)]">
                    {s.role}
                  </h3>
                  <p className="mt-2 text-xs leading-relaxed text-[var(--text-secondary)]">
                    {s.desc}
                  </p>
                </div>
                <button
                  onClick={s.action}
                  className="mt-6 flex items-center justify-between rounded-xl bg-[var(--surface-muted)] px-3.5 py-2 text-xs font-semibold text-[var(--brand-primary)] dark:text-[#D7F36B] transition hover:bg-[#173D32] hover:text-white dark:hover:bg-[#D7F36B] dark:hover:text-[#102C24]"
                >
                  <span>{s.actionLabel}</span>
                  <ArrowRight className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section F: Final CTA */}
      <section className="border-t border-[var(--border)] bg-[#173D32] text-white py-20 px-4 sm:px-6 lg:px-8 dark:bg-[#102C24]">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="font-display text-3xl font-extrabold tracking-tight sm:text-4xl text-white">
            Ready to eliminate institutional food waste?
          </h2>
          <p className="mt-4 text-sm text-stone-200 max-w-xl mx-auto leading-relaxed">
            Enter the operational workspace to explore live headcount forecasts, per-dish planning math, kitchen logging, and waste intelligence.
          </p>
          <div className="mt-8 flex justify-center gap-4">
            <button
              onClick={() => onOpenApp('dashboard')}
              className="flex items-center gap-2 rounded-2xl bg-[#D7F36B] px-8 py-3.5 text-sm font-bold text-[#102C24] shadow-lg transition hover:bg-[#C5E552] hover:scale-105"
            >
              Enter Operational Workspace
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </section>

      <PublicFooter onOpenApp={() => onOpenApp('dashboard')} />
    </div>
  );
};
