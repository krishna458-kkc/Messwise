import React from 'react';
import { LucideIcon } from 'lucide-react';
import { useEnvironment } from '@/context/EnvironmentContext';
import { StatusBadge } from './StatusBadge';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  icon?: LucideIcon;
  badgeText?: string;
  actions?: React.ReactNode;
  children?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  icon: Icon,
  badgeText,
  actions,
  children,
}) => {
  const { isSynthetic, isVerifiedPilot } = useEnvironment();

  const getEnvBadge = () => {
    if (isSynthetic === 1) {
      return <StatusBadge variant="synthetic" dot>Synthetic Demo</StatusBadge>;
    }
    if (isVerifiedPilot) {
      return <StatusBadge variant="real" dot>Verified Pilot</StatusBadge>;
    }
    return <StatusBadge variant="unverified" dot>Unverified Test</StatusBadge>;
  };

  return (
    <div className="mb-6 flex flex-col gap-4 border-b border-[var(--border)] pb-5 md:flex-row md:items-center md:justify-between">
      <div className="flex items-start gap-3.5">
        {Icon && (
          <div className="mt-1 flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[#173D32] text-[#D7F36B] shadow-sm dark:bg-[#183028]">
            <Icon className="h-5 w-5" />
          </div>
        )}
        <div>
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="font-display text-2xl font-bold tracking-tight text-[var(--text-primary)] md:text-3xl">
              {title}
            </h1>
            {badgeText && (
              <span className="rounded-full bg-[var(--surface-muted)] px-2.5 py-0.5 text-xs font-medium text-[var(--text-secondary)]">
                {badgeText}
              </span>
            )}
            {getEnvBadge()}
          </div>
          {subtitle && (
            <p className="mt-1 text-sm text-[var(--text-secondary)] max-w-2xl leading-relaxed">
              {subtitle}
            </p>
          )}
          {children}
        </div>
      </div>

      {actions && (
        <div className="flex flex-wrap items-center gap-2.5 self-start md:self-auto">
          {actions}
        </div>
      )}
    </div>
  );
};
