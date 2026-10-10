import React from 'react';
import { LucideIcon, Inbox } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon: Icon = Inbox,
  action,
}) => {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-[var(--border)] p-10 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--surface-muted)] text-[var(--brand-primary)] dark:text-[#D7F36B]">
        <Icon className="h-6 w-6" />
      </div>
      <h3 className="mt-3 font-display text-base font-semibold text-[var(--text-primary)]">
        {title}
      </h3>
      <p className="mt-1 text-sm text-[var(--text-secondary)] max-w-sm">
        {description}
      </p>
      {action && (
        <button
          onClick={action.onClick}
          className="btn-primary mt-4 text-xs py-2 px-4"
        >
          {action.label}
        </button>
      )}
    </div>
  );
};
