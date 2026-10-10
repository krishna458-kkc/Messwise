import React from 'react';

export const PublicFooter: React.FC<{ onOpenApp: () => void }> = ({ onOpenApp }) => {
  return (
    <footer className="border-t border-[var(--border)] bg-[var(--surface-muted)] py-12 transition-colors">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#173D32] p-1 text-[#D7F36B] dark:bg-[#183028]">
                <img src="/favicon.svg" alt="MessWise" className="h-full w-full" />
              </div>
              <span className="font-display text-lg font-bold text-[#173D32] dark:text-[#D7F36B]">
                MessWise
              </span>
            </div>
            <p className="mt-3 text-xs leading-relaxed text-[var(--text-secondary)] max-w-md">
              A closed-loop AI food-operations intelligence platform for institutional dining halls. Helping kitchen teams predict meal turnout, plan quantities dish by dish, log leftovers in seconds, and eliminate food waste without risking shortages.
            </p>
            <div className="mt-4 flex items-center gap-2">
              <span className="rounded-full border border-emerald-300 bg-emerald-50 px-2.5 py-0.5 text-[11px] font-medium text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                Ethical AI & Data Honesty Compliant
              </span>
              <span className="rounded-full border border-stone-300 bg-stone-100 px-2.5 py-0.5 text-[11px] font-medium text-stone-700 dark:border-stone-700 dark:bg-stone-800 dark:text-stone-300">
                SDG 12.3 Aligned
              </span>
            </div>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-primary)]">
              Operational Workflow
            </h4>
            <ul className="mt-3 space-y-2 text-xs text-[var(--text-secondary)]">
              <li><button onClick={onOpenApp} className="hover:text-[var(--text-primary)]">Command Center</button></li>
              <li><button onClick={onOpenApp} className="hover:text-[var(--text-primary)]">Forecast Lab (80% Conformal)</button></li>
              <li><button onClick={onOpenApp} className="hover:text-[var(--text-primary)]">Kitchen Logging & Voice</button></li>
              <li><button onClick={onOpenApp} className="hover:text-[var(--text-primary)]">Planner & Newsvendor Optimizer</button></li>
              <li><button onClick={onOpenApp} className="hover:text-[var(--text-primary)]">Surplus Routing & Safety Clock</button></li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-primary)]">
              Methodology & Governance
            </h4>
            <ul className="mt-3 space-y-2 text-xs text-[var(--text-secondary)]">
              <li><a href="#methodology" className="hover:text-[var(--text-primary)]">Three-Tier Data Provenance</a></li>
              <li><a href="#methodology" className="hover:text-[var(--text-primary)]">Kaplan–Meier Appetite Learning</a></li>
              <li><a href="#methodology" className="hover:text-[var(--text-primary)]">Lifecycle CO₂e Uncertainty Bands</a></li>
              <li><button onClick={onOpenApp} className="hover:text-[var(--text-primary)]">Blind Forecast Verification</button></li>
              <li><button onClick={onOpenApp} className="hover:text-[var(--text-primary)]">Immutable Audit Trail</button></li>
            </ul>
          </div>
        </div>

        <div className="mt-10 flex flex-col items-center justify-between border-t border-[var(--border)] pt-6 text-xs text-[var(--text-secondary)] sm:flex-row">
          <p>© {new Date().getFullYear()} MessWise. Institutional Food Sustainability Platform.</p>
          <p className="mt-2 sm:mt-0">Built on FastAPI, SQLAlchemy, React & Vite. Powered by real kitchen physics.</p>
        </div>
      </div>
    </footer>
  );
};
