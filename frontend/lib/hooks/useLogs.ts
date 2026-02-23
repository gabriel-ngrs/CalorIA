import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { HydrationDaySummary, HydrationLog, MoodLog, WeightLog } from "@/types";

// ─── Weight ──────────────────────────────────────────────────────────────────

export function useWeightLogs() {
  return useQuery<WeightLog[]>({
    queryKey: ["weight"],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/weight");
      return data;
    },
  });
}

export function useLogWeight() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { weight_kg: number; date: string; notes?: string }) => {
      const { data } = await api.post("/api/v1/weight", payload);
      return data as WeightLog;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["weight"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

// ─── Hydration ───────────────────────────────────────────────────────────────

export function useHydrationToday() {
  return useQuery<HydrationDaySummary>({
    queryKey: ["hydration", "today"],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/hydration/today");
      return data;
    },
  });
}

export function useLogHydration() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { amount_ml: number; date: string; time: string }) => {
      const { data } = await api.post("/api/v1/hydration", payload);
      return data as HydrationLog;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["hydration"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

// ─── Mood ────────────────────────────────────────────────────────────────────

export function useMoodLogs() {
  return useQuery<MoodLog[]>({
    queryKey: ["mood"],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/mood");
      return data;
    },
  });
}

export function useLogMood() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      date: string;
      energy_level: number;
      mood_level: number;
      notes?: string;
    }) => {
      const { data } = await api.post("/api/v1/mood", payload);
      return data as MoodLog;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["mood"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
