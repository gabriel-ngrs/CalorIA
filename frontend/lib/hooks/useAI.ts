import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  InsightResponse,
  MealSuggestion,
  EatingPattern,
  NutritionalAlertsResponse,
  GoalAdjustmentSuggestion,
  MonthlyReport,
  ConversationResponse,
} from "@/types";

// Controle de custo Groq (FR-C1): os insights nunca disparam sozinhos.
// `enabled: false` deixa a geração opt-in (só via refetch() no clique) e o
// cache sobrevive à navegação (staleTime infinito + gcTime alto), sem
// regenerar em foco/reconexão/remontagem.
const INSIGHT_QUERY_OPTIONS = {
  enabled: false,
  staleTime: Infinity,
  gcTime: 30 * 60 * 1000,
  refetchOnWindowFocus: false,
  refetchOnReconnect: false,
  refetchOnMount: false,
} as const;

export function useDailyInsight() {
  return useQuery<InsightResponse>({
    queryKey: ["ai", "daily"],
    queryFn: async () => {
      const { data } = await api.post("/api/v1/ai/insights", { type: "daily" });
      return data as InsightResponse;
    },
    ...INSIGHT_QUERY_OPTIONS,
  });
}

export function useWeeklyInsight() {
  return useQuery<InsightResponse>({
    queryKey: ["ai", "weekly"],
    queryFn: async () => {
      const { data } = await api.post("/api/v1/ai/insights", { type: "weekly" });
      return data as InsightResponse;
    },
    ...INSIGHT_QUERY_OPTIONS,
  });
}

// Histórico do chat web "Pergunte à IA". Diferente dos insights, é só leitura
// (não chama a IA/Groq), então carrega no mount para exibir o histórico ao abrir.
export function useChatHistory() {
  return useQuery<ConversationResponse>({
    queryKey: ["ai", "conversations"],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/ai/conversations");
      return data as ConversationResponse;
    },
    staleTime: 60 * 1000,
  });
}

export function useAskQuestion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (question: string) => {
      const { data } = await api.post("/api/v1/ai/insights", {
        type: "question",
        question,
      });
      return data as InsightResponse;
    },
    // O backend persiste o par pergunta/resposta; recarrega o histórico.
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ai", "conversations"] });
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
  return useQuery<EatingPattern>({
    queryKey: ["ai", "patterns", days],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/ai/patterns", { params: { days } });
      return data as EatingPattern;
    },
    ...INSIGHT_QUERY_OPTIONS,
  });
}

export function useNutritionalAlerts(days: number) {
  return useQuery<NutritionalAlertsResponse>({
    queryKey: ["ai", "nutritional-alerts", days],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/ai/nutritional-alerts", { params: { days } });
      return data as NutritionalAlertsResponse;
    },
    ...INSIGHT_QUERY_OPTIONS,
  });
}

export function useGoalAdjustment() {
  return useQuery<GoalAdjustmentSuggestion>({
    queryKey: ["ai", "goal-adjustment"],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/ai/goal-adjustment");
      return data as GoalAdjustmentSuggestion;
    },
    ...INSIGHT_QUERY_OPTIONS,
  });
}

export function useMonthlyReport(month: number, year: number) {
  return useQuery<MonthlyReport>({
    queryKey: ["ai", "monthly-report", month, year],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/ai/monthly-report", {
        params: { month, year },
      });
      return data as MonthlyReport;
    },
    ...INSIGHT_QUERY_OPTIONS,
  });
}
