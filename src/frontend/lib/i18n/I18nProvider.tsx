"use client";

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import type { Locale, TranslationDict } from "./translations";
import { translations } from "./translations";

interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: TranslationDict;
}

const I18nContext = createContext<I18nContextValue | null>(null);

const STORAGE_KEY = "athena_locale";

function getInitialLocale(): Locale {
  if (typeof window === "undefined") return "zh-CN";
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "en" || stored === "zh-CN") return stored;
  const browserLang = navigator.language;
  if (browserLang.startsWith("zh")) return "zh-CN";
  return "zh-CN";
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("zh-CN");

  useEffect(() => {
    setLocaleState(getInitialLocale());
  }, []);

  const setLocale = useCallback((newLocale: Locale) => {
    setLocaleState(newLocale);
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, newLocale);
    }
  }, []);

  const t = translations[locale];

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useTranslation(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error("useTranslation must be used within I18nProvider");
  }
  return ctx;
}
