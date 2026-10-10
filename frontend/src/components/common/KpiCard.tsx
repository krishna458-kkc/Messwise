import React from 'react';
import { LucideIcon } from 'lucide-react';

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
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  unit,
  subtitle,
  icon: Icon,
  badge,
  className = '',
}) => {
  const badgeStyles = {
    positive: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-300 dark:border-emerald-800',
    negative: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/50 dark:text-red-300 dark:border-red-800',
    neutral: 'bg-stone-100 text-stone-700 border-stone-200 dark:bg-stone-800 dark:text-stone-300 dark:border-stone-700',
    accent: 'bg-[#D7F36B]/20 text-[#173D32] border-[#D7F36B]/40 dark:bg-[#D7F36B]/10 dark:text-[#D7F36B] dark:border-[#D7F36B]/30',
  };

  return (
    <div
      className={`glow-card rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-xs transition-all duration-200 hover:border-[#173D32]/30 dark:hover:border-[#D7F36B]/30 ${className}`}
    >
      <div className="flex items-start justify-between">
        <span className="text-xs font-medium tracking-wide uppercase text-[var(--text-secondary)]">
          {title}
        </span>
        {Icon && (
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--surface-muted)] text-[var(--brand-primary)] dark:text-[#D7F36B]">
            <Icon className="h-4 w-4" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline gap-1.5">
        <span className="font-display text-3xl font-bold tracking-tight text-[var(--text-primary)] tabular-nums">
          {value}
        </span>
        {unit && (
          <span className="text-sm font-medium text-[var(--text-secondary)]">
            {unit}
          </span>
        )}
      </div>

      <div className="mt-2.5 flex items-center gap-2">
        {badge && (
          <span
            className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold ${badgeStyles[badge.variant]}`}
          >
            {badge.text}
          </span>
        )}
        {subtitle && (
          <span className="text-xs text-[var(--text-secondary)]">
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
};
