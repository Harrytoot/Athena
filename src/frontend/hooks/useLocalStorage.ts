"use client";

import { useCallback, useEffect, useState } from "react";

export function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  const [storedValue, setStoredValue] = useState<T>(initialValue);

  useEffect(() => {
    try {
      const item = typeof window !== "undefined" ? localStorage.getItem(key) : null;
      if (item) {
        setStoredValue(JSON.parse(item));
      }
    } catch {
      // parse error, use initial
    }
  }, [key]);

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      setStoredValue((prev) => {
        const nextValue = value instanceof Function ? value(prev) : value;
        if (typeof window !== "undefined") {
          localStorage.setItem(key, JSON.stringify(nextValue));
        }
        return nextValue;
      });
    },
    [key],
  );

  const removeValue = useCallback(() => {
    if (typeof window !== "undefined") {
      localStorage.removeItem(key);
    }
    setStoredValue(initialValue);
  }, [key, initialValue]);

  return [storedValue, setValue, removeValue];
}
