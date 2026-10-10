import React, { useState } from 'react';
import { ThemeProvider } from '@/context/ThemeContext';
import { EnvironmentProvider } from '@/context/EnvironmentContext';
import { RoleProvider } from '@/context/RoleContext';
import { AppShell, AppTab } from '@/components/common/AppShell';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';

import { LandingPage } from '@/pages/LandingPage';
import { CommandCenter } from '@/pages/CommandCenter';
import { ForecastLab } from '@/pages/ForecastLab';
import { KitchenPage } from '@/pages/KitchenPage';
import { PlannerPage } from '@/pages/PlannerPage';
import { WasteIntelligencePage } from '@/pages/WasteIntelligencePage';
import { ImpactPage } from '@/pages/ImpactPage';
import { SurplusRoutingPage } from '@/pages/SurplusRoutingPage';
import { SimulatorPage } from '@/pages/SimulatorPage';
import { ReportsPage } from '@/pages/ReportsPage';

export function AppContent() {
  const [viewMode, setViewMode] = useState<'landing' | 'app'>('landing');
  const [currentTab, setCurrentTab] = useState<AppTab>('dashboard');

  const handleOpenApp = (tab?: string) => {
    if (tab && isValidTab(tab)) {
      setCurrentTab(tab as AppTab);
    }
    setViewMode('app');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleExitToLanding = () => {
    setViewMode('landing');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const isValidTab = (t: string): t is AppTab => {
    return [
      'dashboard',
      'forecast',
      'kitchen',
      'planner',
      'intelligence',
      'impact',
      'surplus',
      'simulator',
      'reports',
    ].includes(t);
  };

  if (viewMode === 'landing') {
    return (
      <ErrorBoundary fallbackTitle="Landing Page Display Issue" onReset={() => window.location.reload()}>
        <LandingPage onOpenApp={handleOpenApp} />
      </ErrorBoundary>
    );
  }

  return (
    <AppShell
      currentTab={currentTab}
      onSelectTab={setCurrentTab}
      onExitToLanding={handleExitToLanding}
    >
      <ErrorBoundary
        key={currentTab}
        fallbackTitle={`Unable to Display ${currentTab.toUpperCase()} View`}
        onReturnHome={() => setCurrentTab('dashboard')}
      >
        {currentTab === 'dashboard' && <CommandCenter onNavigate={(t) => handleOpenApp(t)} />}
        {currentTab === 'forecast' && <ForecastLab />}
        {currentTab === 'kitchen' && <KitchenPage />}
        {currentTab === 'planner' && <PlannerPage />}
        {currentTab === 'intelligence' && <WasteIntelligencePage />}
        {currentTab === 'impact' && <ImpactPage />}
        {currentTab === 'surplus' && <SurplusRoutingPage />}
        {currentTab === 'simulator' && <SimulatorPage />}
        {currentTab === 'reports' && <ReportsPage />}
      </ErrorBoundary>
    </AppShell>
  );
}

export default function App() {
  return (
    <ErrorBoundary fallbackTitle="MessWise System Application Issue">
      <ThemeProvider>
        <EnvironmentProvider>
          <RoleProvider>
            <AppContent />
          </RoleProvider>
        </EnvironmentProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
