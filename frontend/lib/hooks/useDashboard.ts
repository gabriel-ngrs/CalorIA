import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  DashboardToday,
  WeeklySummary,
  WeightChartPoint,
  WeeklyMacroPoint,
} from "@/types";

export function useDashboardToday() {
  return useQuery<DashboardToday>({
    queryKey: ["dashboard", "today"],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/dashboard/today");
      return data;
    },
  });
}

export function useWeeklySummary() {
  return useQuery<WeeklySummary>({
    queryKey: ["dashboard", "weekly"],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/dashboard/weekly");
      return data;
    },
  });
}

export function useWeightChart(days = 30) {
  return useQuery<WeightChartPoint[]>({
    queryKey: ["dashboard", "weight-chart", days],
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/dashboard/weight-chart?days=${days}`);
      return data;
    },
  });
}

export function useMacrosChart(days = 7) {
  return useQuery<WeeklyMacroPoint[]>({
    queryKey: ["dashboard", "macros-chart", days],
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/dashboard/macros-chart?days=${days}`);
      return data;
    },
  });
}
