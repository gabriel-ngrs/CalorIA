import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import api from "@/lib/api";
import {
  useDailyInsight,
  useWeeklyInsight,
  useAskQuestion,
  useMealSuggestion,
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

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
};

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

beforeEach(() => {
  jest.clearAllMocks();
});

// ─── useDailyInsight ──────────────────────────────────────────────────────────

describe("useDailyInsight", () => {
  it("faz POST em /api/v1/ai/insights com { type: 'daily' }", async () => {
    mockedApi.post.mockResolvedValueOnce({ data: mockInsightResponse });

    const { result } = renderHook(() => useDailyInsight(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync();
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.post).toHaveBeenCalledWith("/api/v1/ai/insights", {
      type: "daily",
    });
    expect(result.current.data).toEqual(mockInsightResponse);
  });
});

// ─── useWeeklyInsight ─────────────────────────────────────────────────────────

describe("useWeeklyInsight", () => {
  it("faz POST em /api/v1/ai/insights com { type: 'weekly' }", async () => {
    const weeklyResponse = { ...mockInsightResponse, type: "weekly" };
    mockedApi.post.mockResolvedValueOnce({ data: weeklyResponse });

    const { result } = renderHook(() => useWeeklyInsight(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync();
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.post).toHaveBeenCalledWith("/api/v1/ai/insights", {
      type: "weekly",
    });
    expect(result.current.data).toEqual(weeklyResponse);
  });
});

// ─── useAskQuestion ───────────────────────────────────────────────────────────

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

// ─── useMealSuggestion ────────────────────────────────────────────────────────

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

// ─── useMonthlyReport ─────────────────────────────────────────────────────────

describe("useMonthlyReport", () => {
  it("faz GET em /api/v1/ai/monthly-report com parâmetros de mês e ano", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: mockMonthlyReport });

    const { result } = renderHook(() => useMonthlyReport(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({ month: 3, year: 2026 });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/ai/monthly-report", {
      params: { month: 3, year: 2026 },
    });
    expect(result.current.data).toEqual(mockMonthlyReport);
  });
});
