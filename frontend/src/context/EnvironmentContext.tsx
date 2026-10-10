import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { EnvironmentSummary } from '@/lib/types';

interface EnvironmentContextType {
  isSynthetic: number;
  setIsSynthetic: (val: number) => void;
  summary: EnvironmentSummary | null;
  loading: boolean;
  refreshSummary: () => Promise<void>;
  isVerifiedPilot: boolean;
  isUnverifiedTest: boolean;
  badgeLabel: string;
}

const EnvironmentContext = createContext<EnvironmentContextType | undefined>(undefined);

export const EnvironmentProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isSynthetic, setIsSyntheticState] = useState<number>(() => {
    const saved = localStorage.getItem('messwise_env_choice');
    return saved !== null ? parseInt(saved, 10) : 1; // Default to synthetic demo data
  });
  const [summary, setSummary] = useState<EnvironmentSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const refreshSummary = async () => {
    try {
      const data = await api.getEnvironmentSummary();
      setSummary(data);
    } catch (err) {
      console.error('Failed to load environment summary:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshSummary();
  }, []);

  const setIsSynthetic = (val: number) => {
    setIsSyntheticState(val);
    localStorage.setItem('messwise_env_choice', String(val));
  };

  const isVerifiedPilot = summary?.is_verified_pilot ?? false;
  const isUnverifiedTest = isSynthetic === 0 && !isVerifiedPilot;

  let badgeLabel = '🧪 Synthetic Benchmark Data';
  if (isSynthetic === 0) {
    if (isVerifiedPilot) {
      badgeLabel = `🟢 Verified Pilot Data (${summary?.verified_pilot_meals_count || 0} meals)`;
    } else {
      badgeLabel = `🟡 Unverified Test Entries (${summary?.unverified_test_meals_count || 0} manual test entries — Non-Pilot)`;
    }
  } else {
    badgeLabel = `🧪 Synthetic Demo Data (${summary?.synthetic_meals_count || 0} demonstration meals)`;
  }

  return (
    <EnvironmentContext.Provider
      value={{
        isSynthetic,
        setIsSynthetic,
        summary,
        loading,
        refreshSummary,
        isVerifiedPilot,
        isUnverifiedTest,
        badgeLabel,
      }}
    >
      {children}
    </EnvironmentContext.Provider>
  );
};

export const useEnvironment = () => {
  const ctx = useContext(EnvironmentContext);
  if (!ctx) throw new Error('useEnvironment must be used within EnvironmentProvider');
  return ctx;
};
