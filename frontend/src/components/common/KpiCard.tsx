import React from 'react';
import { LucideIcon } from 'lucide-react';
import { CountUp } from '@/components/animations/CountUp';

interface KpiCardProps {
  title: string;
  value: string | number;
  unit?: string;
  subtitle?: string;
  icon?: LucideIcon;
  badge?: {
    text: string;
    variant: 'positive' | 'negative' | 'neutral' | 'accent';
  };
  tooltip?: string;
  className?: string;
  decimals?: number;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  unit,
  subtitle,
  icon: Icon,
  badge,
  className = '',
  decimals,
}) => {
  const badgeStyles = {
    positive: 'bg-emerald-50 text-emerald-800 border-emerald-300 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800',
    negative: 'bg-red-50 text-red-800 border-red-300 dark:bg-red-950/60 dark:text-red-300 dark:border-red-800',
    neutral: 'bg-stone-100 text-stone-800 border-stone-300 dark:bg-stone-800 dark:text-stone-300 dark:border-stone-700',
    accent: 'bg-[#D7F36B]/30 text-[#0E241D] border-[#D7F36B]/60 dark:bg-[#D7F36B]/15 dark:text-[#D7F36B] dark:border-[#D7F36B]/30 font-bold',
  };

  const isNumeric = typeof value === 'number' || (!isNaN(Number(value)) && value !== '' && typeof value === 'string' && !value.includes('—'));
  const numValue = typeof value === 'number' ? value : Number(value);

  // Auto-detect decimals if not provided
  const detectedDecimals = decimals !== undefined ? decimals : (typeof value === 'string' && value.includes('.') ? value.split('.')[1].length : 0);

  return (
    <div
      className={`glow-card rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-xs transition-all duration-300 hover:border-[#184436]/40 dark:hover:border-[#D7F36B]/40 hover:-translate-y-1 ${className}`}
    >
      <div className="flex items-start justify-between">
        <span className="text-xs font-semibold tracking-wider uppercase text-[var(--text-secondary)]">
          {title}
        </span>
        {Icon && (
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--surface-muted)] text-[var(--brand-primary)] dark:text-[#D7F36B] transition-transform duration-200 hover:scale-105">
            <Icon className="h-4.5 w-4.5" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline gap-1.5">
        <span className="font-display text-3xl font-extrabold tracking-tight text-[var(--text-primary)] tabular-nums">
          {isNumeric && !isNaN(numValue) ? (
            <CountUp to={numValue} decimals={detectedDecimals} duration={1.4} />
          ) : (
            value
          )}
        </span>
        {unit && (
          <span className="text-sm font-semibold text-[var(--text-secondary)]">
            {unit}
          </span>
        )}
      </div>

      <div className="mt-2.5 flex items-center gap-2">
        {badge && (
          <span
            className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${badgeStyles[badge.variant]}`}
          >
            {badge.text}
          </span>
        )}
        {subtitle && (
          <span className="text-xs text-[var(--text-secondary)] leading-tight">
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
};
