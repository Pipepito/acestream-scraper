import React, { createContext, useCallback, useContext, useLayoutEffect, useMemo, useRef, useState } from 'react';
import i18n from '../i18n';
import type { ThemeMode } from '../theme';

export const interfaceIds = ['lime', 'coral', 'cyan'] as const;
export type InterfaceId = typeof interfaceIds[number];
export type AppLanguage = 'en' | 'es';
export interface Preferences { interface: InterfaceId; mode: ThemeMode; language: AppLanguage }
export const preferenceKeys = { interface: 'app-interface-v1', mode: 'app-theme-mode', language: 'app-language-v1' } as const;
type StorageFailure = 'read' | 'write' | null;
interface PreferencesValue extends Preferences {
  setPreference: <K extends keyof Preferences>(key: K, value: Preferences[K]) => void;
  storageFailure: StorageFailure;
  retryStorage: () => void;
}
const defaults: Preferences = { interface: 'cyan', mode: 'light', language: 'en' };
const Context = createContext<PreferencesValue>({ ...defaults, setPreference: () => undefined, storageFailure: null, retryStorage: () => undefined });
const known = (key: keyof Preferences, value: string | null): boolean => key === 'interface'
  ? interfaceIds.some(id => id === value) : key === 'mode' ? value === 'light' || value === 'dark' : value === 'en' || value === 'es';

export function readPreferences() {
  const value = { ...defaults };
  let failure: StorageFailure = null;
  if (typeof window === 'undefined') return { value, failure };
  value.mode = window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  value.language = navigator.language?.toLowerCase().startsWith('es') ? 'es' : 'en';
  for (const key of Object.keys(preferenceKeys) as Array<keyof Preferences>) {
    try {
      const stored = window.localStorage.getItem(preferenceKeys[key]);
      if (known(key, stored)) Object.assign(value, { [key]: stored });
    } catch { failure = 'read'; }
  }
  return { value, failure };
}

export function AppPreferencesProvider({ children }: { children: React.ReactNode }) {
  const [initial] = useState(readPreferences);
  const [preferences, setPreferences] = useState(initial.value);
  const current = useRef(preferences);
  const changed = useRef(new Set<keyof Preferences>());
  const [storageFailure, setFailure] = useState<StorageFailure>(initial.failure);
  const preserveAnchor = useCallback(() => {
    const focused = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const anchor = Array.from(document.querySelectorAll<HTMLElement>('[data-reading-anchor], main h1, main h2')).find(node => node.getBoundingClientRect().top >= 0);
    const top = anchor?.getBoundingClientRect().top;
    requestAnimationFrame(() => {
      if (focused?.isConnected && document.activeElement !== focused) focused.focus({ preventScroll: true });
      if (anchor?.isConnected && top !== undefined) window.scrollBy(0, anchor.getBoundingClientRect().top - top);
    });
  }, []);
  const persist = useCallback(() => {
    let failed = false;
    for (const key of Array.from(changed.current)) {
      try { localStorage.setItem(preferenceKeys[key], current.current[key]); }
      catch { failed = true; }
    }
    setFailure(failed ? 'write' : null);
  }, []);
  const setPreference = useCallback(<K extends keyof Preferences,>(key: K, value: Preferences[K]) => {
    preserveAnchor();
    changed.current.add(key);
    current.current = { ...current.current, [key]: value };
    setPreferences(current.current);
    persist();
  }, [persist, preserveAnchor]);
  const retryStorage = useCallback(() => {
    if (storageFailure === 'read') {
      const read = readPreferences();
      for (const key of Array.from(changed.current)) Object.assign(read.value, { [key]: current.current[key] });
      current.current = read.value;
      setPreferences(read.value);
      setFailure(read.failure);
      if (read.failure) return;
    }
    persist();
  }, [persist, storageFailure]);
  useLayoutEffect(() => {
    document.documentElement.lang = preferences.language;
    document.documentElement.dataset.interface = preferences.interface;
    document.documentElement.dataset.theme = preferences.mode;
    void i18n.changeLanguage(preferences.language);
  }, [preferences]);
  const context = useMemo(() => ({ ...preferences, setPreference, storageFailure, retryStorage }), [preferences, setPreference, storageFailure, retryStorage]);
  return <Context.Provider value={context}>{children}</Context.Provider>;
}
export const useAppPreferences = () => useContext(Context);
