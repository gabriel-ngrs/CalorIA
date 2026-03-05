import { useMutation } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  InsightResponse,
  MealSuggestion,
  EatingPattern,
  NutritionalAlertsResponse,
  GoalAdjustmentSuggestion,
  MonthlyReport,
} from "@/types";

export function useDailyInsight() {
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post("/api/v1/ai/insights", { type: "daily" });
      return data as InsightResponse;
    },
  });
}

export function useWeeklyInsight() {
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post("/api/v1/ai/insights", { type: "weekly" });
      return data as InsightResponse;
    },
  });
}

export function useAskQuestion() {
  return useMutation({
    mutationFn: async (question: string) => {
      const { data } = await api.post("/api/v1/ai/insights", {
        type: "question",
        question,
      });
      return data as InsightResponse;
    },
  });
}

export function useMealSuggestion() {
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.get("/api/v1/ai/suggest-meal");
      return data as MealSuggestion;
    },
  });
}

export function useEatingPatterns(days: number) {
  return useMutation({
    mutationFn: async (d: number) => {
      const { data } = await api.get("/api/v1/ai/patterns", { params: { days: d } });
      return data as EatingPattern;
    },
    onMutate: () => days,
  });
}

export function useNutritionalAlerts(days: number) {
  return useMutation({
    mutationFn: async (d: number) => {
      const { data } = await api.get("/api/v1/ai/nutritional-alerts", { params: { days: d } });
      return data as NutritionalAlertsResponse;
    },
    onMutate: () => days,
  });
}

export function useGoalAdjustment() {
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.get("/api/v1/ai/goal-adjustment");
      return data as GoalAdjustmentSuggestion;
    },
  });
}

export function useMonthlyReport() {
  return useMutation({
    mutationFn: async ({ month, year }: { month: number; year: number }) => {
      const { data } = await api.get("/api/v1/ai/monthly-report", {
        params: { month, year },
      });
      return data as MonthlyReport;
    },
  });
}
