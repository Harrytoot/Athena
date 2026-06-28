"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface UseAsyncState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

interface UseAsyncReturn<T> extends UseAsyncState<T> {
  execute: (...args: unknown[]) => Promise<T | null>;
  reset: () => void;
}

export function useAsync<T>(
  asyncFn: (...args: unknown[]) => Promise<T>,
  immediate = false,
): UseAsyncReturn<T> {
  const [state, setState] = useState<UseAsyncState<T>>({
    data: null,
    loading: immediate,
    error: null,
  });

  const mountedRef = useRef(true);
  const asyncFnRef = useRef(asyncFn);
  asyncFnRef.current = asyncFn;

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (immediate) {
      asyncFnRef
        .current()
        .then((data) => {
          if (mountedRef.current) setState({ data, loading: false, error: null });
        })
        .catch((error) => {
          if (mountedRef.current) setState({ data: null, loading: false, error: error as Error });
        });
    }
  }, [immediate]);

  const execute = useCallback(async (...args: unknown[]) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await asyncFnRef.current(...args);
      if (mountedRef.current) setState({ data, loading: false, error: null });
      return data;
    } catch (error) {
      if (mountedRef.current) setState({ data: null, loading: false, error: error as Error });
      return null;
    }
  }, []);

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return { ...state, execute, reset };
}
