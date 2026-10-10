import React, { createContext, useContext, useEffect, useState } from 'react';

export type UserRole = 'manager' | 'cook' | 'auditor' | 'student';
export type AppLanguage = 'en' | 'te' | 'hi';

interface RoleContextType {
  role: UserRole;
  setRole: (r: UserRole) => void;
  language: AppLanguage;
  setLanguage: (lang: AppLanguage) => void;
  messId: string;
}

const RoleContext = createContext<RoleContextType | undefined>(undefined);

export const RoleProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [role, setRoleState] = useState<UserRole>(() => {
    return (localStorage.getItem('messwise_role') as UserRole) || 'manager';
  });

  const [language, setLanguageState] = useState<AppLanguage>(() => {
    return (localStorage.getItem('messwise_lang') as AppLanguage) || 'en';
  });

  const messId = 'default_mess';

  useEffect(() => {
    localStorage.setItem('messwise_role', role);
  }, [role]);

  useEffect(() => {
    localStorage.setItem('messwise_lang', language);
  }, [language]);

  return (
    <RoleContext.Provider
      value={{
        role,
        setRole: setRoleState,
        language,
        setLanguage: setLanguageState,
        messId,
      }}
    >
      {children}
    </RoleContext.Provider>
  );
};

export const useRole = () => {
  const ctx = useContext(RoleContext);
  if (!ctx) throw new Error('useRole must be used within RoleProvider');
  return ctx;
};
