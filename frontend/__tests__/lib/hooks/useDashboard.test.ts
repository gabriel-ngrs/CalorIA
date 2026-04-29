import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import api from "@/lib/api";
import {
  useDashboardToday,
  useWeeklySummary,
  useWeightChart,
  useMacrosChart,
} from "@/lib/hooks/useDashboard";

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

const mockDashboardToday = {
  date: "2026-03-15",
  nutrition: {
    total_calories: 1500,
    total_protein: 80,
    total_carbs: 200,
    total_fat: 50,
    total_fiber: 15,
    meals_count: 3,
    meals: [],
  },
  hydration: {
    date: "2026-03-15",
    total_ml: 1500,
    entries: [],
  },
  mood: null,
  latest_weight: null,
};

const mockWeeklySummary = {
  week_start: "2026-03-09",
  week_end: "2026-03-15",
  avg_calories: 1600,
  avg_protein: 85,
  avg_carbs: 210,
  avg_fat: 55,
  days_with_data: 5,
};

const mockWeightChartPoints = [
  { date: "2026-03-01", weight_kg: 75.0 },
  { date: "2026-03-08", weight_kg: 74.5 },
  { date: "2026-03-15", weight_kg: 74.0 },
];

const mockMacrosChartPoints = [
  { date: "2026-03-09", calories: 1500, protein: 80, carbs: 200, fat: 50 },
  { date: "2026-03-10", calories: 1600, protein: 85, carbs: 210, fat: 55 },
];

beforeEach(() => {
  jest.clearAllMocks();
});

// ─── useDashboardToday ────────────────────────────────────────────────────────

describe("useDashboardToday", () => {
  it("busca dados de /api/v1/dashboard/today", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: mockDashboardToday });

    const { result } = renderHook(() => useDashboardToday(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/dashboard/today");
    expect(result.current.data).toEqual(mockDashboardToday);
  });
});

// ─── useWeeklySummary ─────────────────────────────────────────────────────────

describe("useWeeklySummary", () => {
  it("busca dados de /api/v1/dashboard/weekly", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: mockWeeklySummary });

    const { result } = renderHook(() => useWeeklySummary(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/dashboard/weekly");
    expect(result.current.data).toEqual(mockWeeklySummary);
  });
});

// ─── useWeightChart ───────────────────────────────────────────────────────────

describe("useWeightChart", () => {
  it("busca dados de /api/v1/dashboard/weight-chart com days=30 por padrão", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: mockWeightChartPoints });

    const { result } = renderHook(() => useWeightChart(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith(
      "/api/v1/dashboard/weight-chart?days=30"
    );
    expect(result.current.data).toEqual(mockWeightChartPoints);
  });

  it("usa o valor de days fornecido na URL", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: mockWeightChartPoints });

    const { result } = renderHook(() => useWeightChart(60), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith(
      "/api/v1/dashboard/weight-chart?days=60"
    );
  });
});

// ─── useMacrosChart ───────────────────────────────────────────────────────────

describe("useMacrosChart", () => {
  it("busca dados de /api/v1/dashboard/macros-chart com days=7 por padrão", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: mockMacrosChartPoints });

    const { result } = renderHook(() => useMacrosChart(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith(
      "/api/v1/dashboard/macros-chart?days=7"
    );
    expect(result.current.data).toEqual(mockMacrosChartPoints);
  });

  it("usa o valor de days fornecido na URL", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: mockMacrosChartPoints });

    const { result } = renderHook(() => useMacrosChart(14), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith(
      "/api/v1/dashboard/macros-chart?days=14"
    );
  });
});
