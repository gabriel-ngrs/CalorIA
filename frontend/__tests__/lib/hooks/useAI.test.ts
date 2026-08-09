import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import api from "@/lib/api";
import {
  useDailyInsight,
  useWeeklyInsight,
  useAskQuestion,
  useChatHistory,
  useMealSuggestion,
  useEatingPatterns,
  useNutritionalAlerts,
  useGoalAdjustment,
  useMonthlyReport,
} from "@/lib/hooks/useAI";

jest.mock("@/lib/api", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  },
}));

const mockedApi = api as jest.Mocked<typeof api>;

// Cliente compartilhado permite testar persistência do cache entre remontagens
// (simulando navegar para fora e voltar — AC-C1).
const makeClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 30 * 60 * 1000 },
      mutations: { retry: false },
    },
  });

const wrapperFor = (queryClient: QueryClient) =>
  ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);

const createWrapper = () => wrapperFor(makeClient());

const mockInsightResponse = {
  type: "daily",
  content: "Você atingiu sua meta de proteínas hoje. Continue assim!",
  generated_at: "2026-03-15T20:00:00Z",
};

const mockMealSuggestion = {
  meal_type: "dinner",
  suggestion: "Frango grelhado com batata doce e brócolis",
  estimated_calories: 500,
  reason: "Refeição rica em proteína para recuperação muscular.",
};

const mockMonthlyReport = {
  month: 3,
  year: 2026,
  summary: "Mês com bom controle calórico",
  avg_calories: 1850,
  avg_protein: 90,
  avg_carbs: 220,
  avg_fat: 60,
  weight_change: -1.5,
};

const mockEatingPattern = { analysis: "Você come mais à noite.", frequent_foods: ["arroz"] };
const mockAlerts = { days_analyzed: 14, alerts: [], analysis: "Tudo certo." };
const mockGoalAdjustment = {
  adjustment_recommended: false,
  weight_trend_kg_per_week: null,
  current_calorie_goal: 2000,
  suggested_calorie_goal: null,
  suggestion: "Mantenha o ritmo.",
};

beforeEach(() => {
  jest.clearAllMocks();
});

// ─── Insights migrados para useQuery (opt-in + cache persistente) ─────────────
//
// Controle de custo Groq (FR-C1): nenhuma query pode disparar no mount; só via
// refetch() no clique. O cache sobrevive à navegação (AC-C1).

describe("useDailyInsight (useQuery opt-in)", () => {
  it("NÃO dispara fetch no mount (opt-in — controle de custo)", () => {
    const { result } = renderHook(() => useDailyInsight(), {
      wrapper: createWrapper(),
    });

    // Sem clique/refetch, o queryFn nunca roda no mount.
    expect(result.current.isFetching).toBe(false);
    expect(mockedApi.post).not.toHaveBeenCalled();
    expect(result.current.data).toBeUndefined();
  });

  it("busca e cacheia o insight ao chamar refetch()", async () => {
    mockedApi.post.mockResolvedValueOnce({ data: mockInsightResponse });

    const { result } = renderHook(() => useDailyInsight(), {
      wrapper: createWrapper(),
    });

    let refetched;
    await act(async () => {
      refetched = await result.current.refetch();
    });

    expect(mockedApi.post).toHaveBeenCalledWith("/api/v1/ai/insights", {
      type: "daily",
    });
    expect(refetched!.data).toEqual(mockInsightResponse);
  });

  it("mantém o insight ao remontar o hook (navegar e voltar — AC-C1)", async () => {
    mockedApi.post.mockResolvedValueOnce({ data: mockInsightResponse });
    const client = makeClient();
    const wrapper = wrapperFor(client);

    const first = renderHook(() => useDailyInsight(), { wrapper });
    await act(async () => {
      await first.result.current.refetch();
    });

    // Desmonta (sai da página) e monta de novo (volta) no mesmo QueryClient.
    first.unmount();
    const second = renderHook(() => useDailyInsight(), { wrapper });

    // Dado servido do cache no mount, sem novo fetch (post chamado 1x só).
    await waitFor(() => expect(second.result.current.data).toEqual(mockInsightResponse));
    expect(mockedApi.post).toHaveBeenCalledTimes(1);
    expect(second.result.current.isFetching).toBe(false);
  });
});

describe("useWeeklyInsight (useQuery opt-in)", () => {
  it("não dispara no mount e busca via refetch com type='weekly'", async () => {
    const weeklyResponse = { ...mockInsightResponse, type: "weekly" };
    mockedApi.post.mockResolvedValueOnce({ data: weeklyResponse });

    const { result } = renderHook(() => useWeeklyInsight(), {
      wrapper: createWrapper(),
    });

    expect(mockedApi.post).not.toHaveBeenCalled();

    let refetched;
    await act(async () => {
      refetched = await result.current.refetch();
    });

    expect(mockedApi.post).toHaveBeenCalledWith("/api/v1/ai/insights", {
      type: "weekly",
    });
    expect(refetched!.data).toEqual(weeklyResponse);
  });
});

describe("useEatingPatterns (useQuery opt-in)", () => {
  it("não dispara no mount e busca via refetch com days", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: mockEatingPattern });

    const { result } = renderHook(() => useEatingPatterns(30), {
      wrapper: createWrapper(),
    });

    expect(mockedApi.get).not.toHaveBeenCalled();

    let refetched;
    await act(async () => {
      refetched = await result.current.refetch();
    });

    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/ai/patterns", {
      params: { days: 30 },
    });
    expect(refetched!.data).toEqual(mockEatingPattern);
  });
});

describe("useNutritionalAlerts (useQuery opt-in)", () => {
  it("não dispara no mount e busca via refetch com days", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: mockAlerts });

    const { result } = renderHook(() => useNutritionalAlerts(14), {
      wrapper: createWrapper(),
    });

    expect(mockedApi.get).not.toHaveBeenCalled();

    let refetched;
    await act(async () => {
      refetched = await result.current.refetch();
    });

    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/ai/nutritional-alerts", {
      params: { days: 14 },
    });
    expect(refetched!.data).toEqual(mockAlerts);
  });
});

describe("useGoalAdjustment (useQuery opt-in)", () => {
  it("não dispara no mount e busca via refetch", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: mockGoalAdjustment });

    const { result } = renderHook(() => useGoalAdjustment(), {
      wrapper: createWrapper(),
    });

    expect(mockedApi.get).not.toHaveBeenCalled();

    let refetched;
    await act(async () => {
      refetched = await result.current.refetch();
    });

    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/ai/goal-adjustment");
    expect(refetched!.data).toEqual(mockGoalAdjustment);
  });
});

describe("useMonthlyReport (useQuery opt-in)", () => {
  it("não dispara no mount e busca via refetch com month/year", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: mockMonthlyReport });

    const { result } = renderHook(() => useMonthlyReport(3, 2026), {
      wrapper: createWrapper(),
    });

    expect(mockedApi.get).not.toHaveBeenCalled();

    let refetched;
    await act(async () => {
      refetched = await result.current.refetch();
    });

    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/ai/monthly-report", {
      params: { month: 3, year: 2026 },
    });
    expect(refetched!.data).toEqual(mockMonthlyReport);
  });
});

// ─── Hooks que seguem como mutation (fora do escopo de C.1) ───────────────────

describe("useAskQuestion", () => {
  it("faz POST em /api/v1/ai/insights com type='question' e a pergunta", async () => {
    const questionResponse = {
      ...mockInsightResponse,
      type: "question",
      content: "O frango grelhado tem em média 165 kcal por 100g.",
    };
    mockedApi.post.mockResolvedValueOnce({ data: questionResponse });

    const { result } = renderHook(() => useAskQuestion(), {
      wrapper: createWrapper(),
    });

    const question = "Quantas calorias tem 100g de frango grelhado?";

    await act(async () => {
      await result.current.mutateAsync(question);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.post).toHaveBeenCalledWith("/api/v1/ai/insights", {
      type: "question",
      question,
    });
    expect(result.current.data).toEqual(questionResponse);
  });
});

// ─── Histórico do chat web (B20 frontend) ────────────────────────────────────

describe("useChatHistory", () => {
  const mockConversation = {
    channel: "web",
    messages: [
      { role: "user", content: "Posso comer pizza?", timestamp: "2026-03-15T20:00:00Z" },
      { role: "model", content: "Com moderação, sim.", timestamp: "2026-03-15T20:00:01Z" },
    ],
  };

  it("carrega o histórico de /api/v1/ai/conversations no mount (AC-C3)", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: mockConversation });

    const { result } = renderHook(() => useChatHistory(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/ai/conversations");
    expect(result.current.data).toEqual(mockConversation);
    expect(result.current.data?.messages).toHaveLength(2);
  });
});

describe("useAskQuestion (invalidação do histórico)", () => {
  it("invalida ['ai','conversations'] ao concluir para recarregar o histórico", async () => {
    mockedApi.post.mockResolvedValueOnce({
      data: { type: "question", content: "resposta" },
    });
    const client = makeClient();
    const spy = jest.spyOn(client, "invalidateQueries");

    const { result } = renderHook(() => useAskQuestion(), {
      wrapper: wrapperFor(client),
    });

    await act(async () => {
      await result.current.mutateAsync("Posso comer pizza?");
    });

    expect(spy).toHaveBeenCalledWith({ queryKey: ["ai", "conversations"] });
  });
});

describe("useMealSuggestion", () => {
  it("faz GET em /api/v1/ai/suggest-meal e retorna sugestão", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: mockMealSuggestion });

    const { result } = renderHook(() => useMealSuggestion(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync();
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/ai/suggest-meal");
    expect(result.current.data).toEqual(mockMealSuggestion);
  });
});
