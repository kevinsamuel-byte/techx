"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { UserState } from "@/lib/types";

export function useCareerState() {
  const router = useRouter();
  const [token, setToken] = useState<string>("");
  const [state, setState] = useState<UserState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const stored = localStorage.getItem("pcn_token") || "";
    if (!stored) {
      router.replace("/login");
      return;
    }
    setToken(stored);
  }, [router]);

  const refresh = useCallback(async (sessionToken?: string) => {
    const activeToken = sessionToken || token;
    if (!activeToken) return;
    setLoading(true);
    try {
      const snapshot = await api.getState(activeToken);
      setState(snapshot);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch state");
      localStorage.removeItem("pcn_token");
      router.replace("/login");
    } finally {
      setLoading(false);
    }
  }, [router, token]);

  useEffect(() => {
    if (token) {
      refresh(token);
    }
  }, [token, refresh]);

  return { token, state, setState, loading, error, refresh };
}
