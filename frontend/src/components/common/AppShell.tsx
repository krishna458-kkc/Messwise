import React, { useState } from 'react';
import { useTheme } from '@/context/ThemeContext';
import { useEnvironment } from '@/context/EnvironmentContext';
import { useRole, UserRole, AppLanguage } from '@/context/RoleContext';
import {
  LayoutDashboard,
  LineChart,
  UtensilsCrossed,
  Calculator,
  BarChart3,
  Leaf,
  Clock,
  PlayCircle,
  FileText,
  ChevronLeft,
  ChevronRight,
  Sun,
  Moon,
  ExternalLink,
  Database,
  Menu,
  X,
} from 'lucide-react';

export type AppTab =
  | 'dashboard'
  | 'forecast'
  | 'kitchen'
  | 'planner'
  | 'intelligence'
  | 'impact'
  | 'surplus'
  | 'simulator'
  | 'reports';

interface AppShellProps {
  currentTab: AppTab;
  onSelectTab: (tab: AppTab) => void;
  onExitToLanding: () => void;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  currentTab,
  onSelectTab,
  onExitToLanding,
  children,
}) => {
  const { theme, toggleTheme } = useTheme();
  const { isSynthetic, setIsSynthetic, isVerifiedPilot, badgeLabel } = useEnvironment();
  const { role, setRole, language, setLanguage } = useRole();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  const navItems: Array<{ id: AppTab; label: string; icon: React.FC<{ className?: string }>; tag?: string }> = [
    { id: 'dashboard', label: 'Command Center', icon: LayoutDashboard },
    { id: 'forecast', label: 'Forecast Lab', icon: LineChart, tag: '80% Band' },
    { id: 'kitchen', label: 'Kitchen Logging', icon: UtensilsCrossed, tag: 'Touch' },
    { id: 'planner', label: 'Dish Planner', icon: Calculator, tag: 'Optimizer' },
    { id: 'intelligence', label: 'Waste Intelligence', icon: BarChart3 },
    { id: 'impact', label: 'Sustainability & ESG', icon: Leaf, tag: 'CO₂e' },
    { id: 'surplus', label: 'Surplus Routing', icon: Clock, tag: 'Safety' },
    { id: 'simulator', label: 'Counterfactual Replay', icon: PlayCircle, tag: 'Blind' },
    { id: 'reports', label: 'Reports & Governance', icon: FileText, tag: 'E2' },
  ];

  const handleNavClick = (tab: AppTab) => {
    onSelectTab(tab);
    setMobileDrawerOpen(false);
  };

  return (
    <div className="flex min-h-screen bg-[var(--background)] text-[var(--text-primary)] transition-colors">
      {/* Desktop Sidebar */}
      <aside
        className={`hidden md:flex flex-col border-r border-[var(--border)] bg-[var(--surface)] transition-all duration-300 ${
          collapsed ? 'w-20' : 'w-64'
        }`}
      >
        {/* Brand & collapse */}
        <div className="flex h-16 items-center justify-between border-b border-[var(--border)] px-4">
          <div className="flex items-center gap-3 overflow-hidden cursor-pointer" onClick={onExitToLanding}>
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-[#173D32] p-1.5 shadow-sm dark:bg-[#183028]">
              <img src="/favicon.svg" alt="MessWise" className="h-full w-full" />
            </div>
            {!collapsed && (
              <div className="truncate">
                <span className="font-display text-lg font-bold tracking-tight text-[#173D32] dark:text-[#D7F36B]">
                  MessWise
                </span>
                <span className="block text-[10px] text-[var(--text-secondary)] font-medium">
                  Workspace
                </span>
              </div>
            )}
          </div>
          <button
            onClick={() => setCollapsed(!collapsed)}
            aria-label="Toggle sidebar"
            className="flex h-7 w-7 items-center justify-center rounded-lg border border-[var(--border)] text-[var(--text-secondary)] transition hover:text-[var(--text-primary)]"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        {/* Navigation items */}
        <nav className="flex-1 space-y-1.5 overflow-y-auto px-3 py-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-xs font-semibold transition ${
                  isActive
                    ? 'bg-[#173D32] text-white shadow-xs dark:bg-[#D7F36B] dark:text-[#102C24]'
                    : 'text-[var(--text-secondary)] hover:bg-[var(--surface-muted)] hover:text-[var(--text-primary)]'
                }`}
                title={collapsed ? item.label : undefined}
              >
                <Icon className={`h-4 w-4 shrink-0 ${isActive ? 'text-white dark:text-[#102C24]' : 'text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]'}`} />
                {!collapsed && (
                  <div className="flex flex-1 items-center justify-between overflow-hidden">
                    <span className="truncate">{item.label}</span>
                    {item.tag && (
                      <span
                        className={`rounded-md px-1.5 py-0.5 text-[9px] font-medium ${
                          isActive
                            ? 'bg-white/20 text-white dark:bg-black/10 dark:text-[#102C24]'
                            : 'bg-[var(--surface-muted)] text-[var(--text-secondary)]'
                        }`}
                      >
                        {item.tag}
                      </span>
                    )}
                  </div>
                )}
              </button>
            );
          })}
        </nav>

        {/* Environment Selector in Sidebar Footer */}
        {!collapsed ? (
          <div className="border-t border-[var(--border)] p-3">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] p-2.5">
              <div className="flex items-center justify-between text-[11px] font-semibold text-[var(--text-primary)]">
                <span className="flex items-center gap-1.5">
                  <Database className="h-3.5 w-3.5 text-[#173D32] dark:text-[#D7F36B]" />
                  Active Target
                </span>
                <span className="text-[10px] text-[var(--text-secondary)]">
                  {isSynthetic === 1 ? 'Demo' : 'Operational'}
                </span>
              </div>
              <div className="mt-2 flex gap-1.5">
                <button
                  onClick={() => setIsSynthetic(1)}
                  className={`flex-1 rounded-lg py-1 text-[10px] font-semibold transition ${
                    isSynthetic === 1
                      ? 'bg-[#173D32] text-white dark:bg-[#D7F36B] dark:text-[#102C24]'
                      : 'bg-[var(--surface)] text-[var(--text-secondary)] border border-[var(--border)]'
                  }`}
                >
                  Synthetic (28)
                </button>
                <button
                  onClick={() => setIsSynthetic(0)}
                  className={`flex-1 rounded-lg py-1 text-[10px] font-semibold transition ${
                    isSynthetic === 0
                      ? 'bg-[#173D32] text-white dark:bg-[#D7F36B] dark:text-[#102C24]'
                      : 'bg-[var(--surface)] text-[var(--text-secondary)] border border-[var(--border)]'
                  }`}
                >
                  {isVerifiedPilot ? 'Pilot' : 'Test (Unverified)'}
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="border-t border-[var(--border)] p-3 flex justify-center">
            <button
              onClick={() => setIsSynthetic(isSynthetic === 1 ? 0 : 1)}
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--surface-muted)] text-[var(--brand-primary)]"
              title={`Switch Data Target (Currently: ${isSynthetic === 1 ? 'Synthetic' : 'Operational'})`}
            >
              <Database className="h-4 w-4" />
            </button>
          </div>
        )}
      </aside>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Header */}
        <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-[var(--border)] bg-[var(--surface)]/90 px-4 backdrop-blur-md sm:px-6">
          <div className="flex items-center gap-3">
            {/* Mobile menu trigger */}
            <button
              onClick={() => setMobileDrawerOpen(!mobileDrawerOpen)}
              className="flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--border)] md:hidden"
            >
              {mobileDrawerOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>

            {/* Breadcrumb / active page title */}
            <div className="flex items-center gap-2">
              <span className="hidden font-display text-sm font-semibold text-[var(--text-secondary)] sm:inline">
                MessWise
              </span>
              <span className="hidden text-stone-400 sm:inline">/</span>
              <span className="font-display text-sm font-bold text-[var(--text-primary)]">
                {navItems.find((n) => n.id === currentTab)?.label}
              </span>
            </div>
          </div>

          {/* Right Header Controls */}
          <div className="flex items-center gap-2.5">
            {/* Environment Badge Pill */}
            <div className="hidden lg:flex items-center">
              <span
                className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${
                  isSynthetic === 1
                    ? 'border-violet-300 bg-violet-50 text-violet-900 dark:border-violet-800 dark:bg-violet-950/50 dark:text-violet-300'
                    : isVerifiedPilot
                    ? 'border-emerald-300 bg-emerald-50 text-emerald-900 dark:border-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300'
                    : 'border-amber-300 bg-amber-50 text-amber-900 dark:border-amber-800 dark:bg-amber-950/50 dark:text-amber-300'
                }`}
              >
                <span
                  className={`h-2 w-2 rounded-full ${
                    isSynthetic === 1
                      ? 'bg-violet-500'
                      : isVerifiedPilot
                      ? 'bg-emerald-500'
                      : 'bg-amber-500'
                  }`}
                />
                {badgeLabel}
              </span>
            </div>

            {/* Role Persona Selector */}
            <div className="relative">
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as UserRole)}
                className="h-8 rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-2.5 text-xs font-semibold text-[var(--text-primary)] focus:outline-hidden"
                aria-label="Active Persona"
              >
                <option value="manager">Manager</option>
                <option value="cook">Kitchen Cook</option>
                <option value="auditor">Campus Auditor</option>
                <option value="student">Student</option>
              </select>
            </div>

            {/* Language Selector */}
            <div className="relative">
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value as AppLanguage)}
                className="h-8 rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-2 text-xs font-semibold text-[var(--text-primary)] focus:outline-hidden"
                aria-label="Interface Language"
              >
                <option value="en">EN</option>
                <option value="te">తెలుగు (TE)</option>
                <option value="hi">हिन्दी (HI)</option>
              </select>
            </div>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              aria-label="Toggle theme"
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] text-[var(--text-secondary)] transition hover:text-[var(--text-primary)]"
            >
              {theme === 'dark' ? <Sun className="h-4 w-4 text-[#D7F36B]" /> : <Moon className="h-4 w-4" />}
            </button>

            {/* Exit to Public Landing */}
            <button
              onClick={onExitToLanding}
              className="hidden sm:flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1 text-xs font-medium text-[var(--text-secondary)] transition hover:bg-[var(--surface-muted)] hover:text-[var(--text-primary)]"
            >
              <span>Landing</span>
              <ExternalLink className="h-3 w-3" />
            </button>
          </div>
        </header>

        {/* Mobile Navigation Drawer */}
        {mobileDrawerOpen && (
          <div className="border-b border-[var(--border)] bg-[var(--surface)] p-4 md:hidden">
            <nav className="grid grid-cols-2 gap-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleNavClick(item.id)}
                    className={`flex items-center gap-2 rounded-xl p-2.5 text-xs font-semibold ${
                      isActive
                        ? 'bg-[#173D32] text-white dark:bg-[#D7F36B] dark:text-[#102C24]'
                        : 'border border-[var(--border)] text-[var(--text-secondary)]'
                    }`}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span className="truncate">{item.label}</span>
                  </button>
                );
              })}
            </nav>
            <div className="mt-4 flex items-center justify-between border-t border-[var(--border)] pt-3">
              <span className="text-xs text-[var(--text-secondary)]">Data Mode:</span>
              <button
                onClick={() => setIsSynthetic(isSynthetic === 1 ? 0 : 1)}
                className="rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-1 text-xs font-semibold"
              >
                {isSynthetic === 1 ? '🧪 Synthetic' : '🟡 Operational'}
              </button>
            </div>
          </div>
        )}

        {/* Page Content Body */}
        <main className="flex-1 overflow-y-auto px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-7xl">{children}</div>
        </main>
      </div>
    </div>
  );
};
