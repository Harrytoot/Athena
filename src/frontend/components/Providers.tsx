"use client";

import type { ReactNode } from "react";
import { QueryProvider } from "@/lib/query-provider";
import { I18nProvider } from "@/lib/i18n/I18nProvider";
import { ErrorBoundary } from "@/components/ErrorBoundary";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary>
      <QueryProvider>
        <I18nProvider>{children}</I18nProvider>
      </QueryProvider>
    </ErrorBoundary>
  );
}
