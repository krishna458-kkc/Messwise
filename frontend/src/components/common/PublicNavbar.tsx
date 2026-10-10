import React, { useState } from 'react';
import { useTheme } from '@/context/ThemeContext';
import { Sun, Moon, ArrowRight, Menu, X } from 'lucide-react';

interface PublicNavbarProps {
  onOpenApp: () => void;
}

export const PublicNavbar: React.FC<PublicNavbarProps> = ({ onOpenApp }) => {
  const { theme, toggleTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { label: 'Workflow', href: '#workflow' },
    { label: 'Intelligence', href: '#features' },
    { label: 'Interactive Demo', href: '#demo' },
    { label: 'Methodology & Trust', href: '#methodology' },
    { label: 'Stakeholders', href: '#stakeholders' },
  ];

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-[var(--border)] bg-[var(--background)]/80 backdrop-blur-md transition-colors">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        {/* Brand */}
        <a href="#" className="flex items-center gap-3 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#173D32] p-1.5 shadow-sm transition group-hover:scale-105 dark:bg-[#183028]">
            <img src="/favicon.svg" alt="MessWise" className="h-full w-full" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-display text-xl font-bold tracking-tight text-[#173D32] dark:text-[#D7F36B]">
                MessWise
              </span>
              <span className="rounded-full bg-[#D7F36B]/20 px-2 py-0.5 text-[10px] font-semibold text-[#173D32] dark:bg-[#D7F36B]/10 dark:text-[#D7F36B]">
                Closed-Loop
              </span>
            </div>
            <p className="hidden text-[10px] text-[var(--text-secondary)] sm:block">
              Institutional Kitchen Intelligence
            </p>
          </div>
        </a>

        {/* Desktop Links */}
        <div className="hidden items-center gap-6 md:flex">
          {navLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="text-xs font-medium text-[var(--text-secondary)] transition hover:text-[var(--text-primary)]"
            >
              {link.label}
            </a>
          ))}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] transition hover:text-[var(--text-primary)] hover:border-[var(--brand-primary)]"
          >
            {theme === 'dark' ? <Sun className="h-4 w-4 text-[#D7F36B]" /> : <Moon className="h-4 w-4" />}
          </button>

          <button
            onClick={onOpenApp}
            className="hidden items-center gap-2 rounded-xl bg-[#173D32] px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-[#102C24] dark:bg-[#D7F36B] dark:text-[#102C24] dark:hover:bg-[#C5E552] sm:flex"
          >
            Launch Workspace
            <ArrowRight className="h-3.5 w-3.5" />
          </button>

          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--border)] md:hidden"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="border-b border-[var(--border)] bg-[var(--surface)] px-4 py-4 md:hidden">
          <div className="flex flex-col gap-3">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className="py-1 text-sm font-medium text-[var(--text-secondary)]"
              >
                {link.label}
              </a>
            ))}
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                onOpenApp();
              }}
              className="mt-2 flex items-center justify-center gap-2 rounded-xl bg-[#173D32] py-2.5 text-xs font-semibold text-white dark:bg-[#D7F36B] dark:text-[#102C24]"
            >
              Launch Workspace
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}
    </nav>
  );
};
