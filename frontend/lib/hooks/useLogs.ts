import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
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
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["weight"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Peso registrado", { description: `${data.weight_kg} kg salvo com sucesso.` });
    },
    onError: () => toast.error("Erro ao registrar peso"),
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

export function useHydrationHistory(days = 7) {
  return useQuery<HydrationDaySummary[]>({
    queryKey: ["hydration", "history", days],
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/hydration/history?days=${days}`);
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
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["hydration"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Água registrada", { description: `+${data.amount_ml} ml adicionados.` });
    },
    onError: () => toast.error("Erro ao registrar hidratação"),
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
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["mood"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Humor registrado", {
        description: `Energia ${data.energy_level}/5 · Humor ${data.mood_level}/5`,
      });
    },
    onError: () => toast.error("Erro ao registrar humor"),
  });
}
