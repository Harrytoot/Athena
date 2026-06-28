"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { getToken, setToken, clearToken, isLoggedIn, login, register, getMe } from "@/lib/auth";
import type { TokenResponse, UserResponse } from "@/types/auth";

interface UseAuthReturn {
  user: UserResponse | null;
  token: string | null;
  loggedIn: boolean;
  loading: boolean;
  loginAction: (username: string, password: string) => Promise<TokenResponse>;
  registerAction: (username: string, email: string, password: string, displayName: string) => Promise<TokenResponse>;
  logout: () => void;
}

export function useAuth(): UseAuthReturn {
  const router = useRouter();
  const [token, setTokenState] = useState<string | null>(null);
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedToken = getToken();
    setTokenState(storedToken);

    if (storedToken) {
      getMe()
        .then(setUser)
        .catch(() => {
          clearToken();
          setTokenState(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const loginAction = useCallback(
    async (username: string, password: string) => {
      const res = await login(username, password);
      setToken(res.accessToken);
      setTokenState(res.accessToken);
      try {
        const userData = await getMe();
        setUser(userData);
      } catch {
        // user fetch is best-effort
      }
      router.push("/dashboard");
      return res;
    },
    [router],
  );

  const registerAction = useCallback(
    async (username: string, email: string, password: string, displayName: string) => {
      const res = await register(username, email, password, displayName);
      setToken(res.accessToken);
      setTokenState(res.accessToken);
      router.push("/dashboard");
      return res;
    },
    [router],
  );

  const logout = useCallback(() => {
    clearToken();
    setTokenState(null);
    setUser(null);
    router.push("/login");
  }, [router]);

  return {
    user,
    token,
    loggedIn: isLoggedIn(),
    loading,
    loginAction,
    registerAction,
    logout,
  };
}
