import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import api from "@/lib/api";
import { toast } from "sonner";
import {
  useMeals,
  useMeal,
  useCreateMeal,
  useDeleteMeal,
  useAnalyzeMeal,
  useAnalyzePhoto,
} from "@/lib/hooks/useMeals";

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
const mockedToast = toast as jest.Mocked<typeof toast>;

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

const mockMealItem = {
  id: 1,
  food_name: "Arroz",
  quantity: 200,
  unit: "g",
  calories: 260,
  protein: 4.8,
  carbs: 56.8,
  fat: 0.4,
  fiber: 0.5,
};

const mockMeal = {
  id: 1,
  meal_type: "lunch",
  date: "2026-03-15",
  source: "manual",
  notes: null,
  items: [mockMealItem],
};

beforeEach(() => {
  jest.clearAllMocks();
});

// ─── useMeals ────────────────────────────────────────────────────────────────

describe("useMeals", () => {
  it("busca refeições de /api/v1/meals ao montar", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: [mockMeal] });

    const { result } = renderHook(() => useMeals(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/meals");
    expect(result.current.data).toEqual([mockMeal]);
  });

  it("inclui parâmetro de data na URL quando fornecido", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: [mockMeal] });

    const { result } = renderHook(() => useMeals("2026-03-15"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/meals?date=2026-03-15");
  });
});

// ─── useMeal ─────────────────────────────────────────────────────────────────

describe("useMeal", () => {
  it("busca uma refeição pelo ID", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: mockMeal });

    const { result } = renderHook(() => useMeal(1), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/meals/1");
    expect(result.current.data).toEqual(mockMeal);
  });

  it("não faz requisição quando id é 0", () => {
    const { result } = renderHook(() => useMeal(0), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockedApi.get).not.toHaveBeenCalled();
  });
});

// ─── useCreateMeal ────────────────────────────────────────────────────────────

describe("useCreateMeal", () => {
  it("faz POST em /api/v1/meals com o corpo correto", async () => {
    mockedApi.post.mockResolvedValueOnce({ data: mockMeal });

    const { result } = renderHook(() => useCreateMeal(), {
      wrapper: createWrapper(),
    });

    const payload = { meal_type: "lunch", date: "2026-03-15", items: [] };

    await act(async () => {
      await result.current.mutateAsync(
        payload as Parameters<typeof result.current.mutateAsync>[0]
      );
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.post).toHaveBeenCalledWith("/api/v1/meals", payload);
  });

  it("chama toast.success após sucesso", async () => {
    mockedApi.post.mockResolvedValueOnce({ data: mockMeal });

    const { result } = renderHook(() => useCreateMeal(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({
        meal_type: "lunch",
        date: "2026-03-15",
        items: [],
      } as Parameters<typeof result.current.mutateAsync>[0]);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedToast.success).toHaveBeenCalledWith(
      "Refeição salva!",
      expect.objectContaining({ description: expect.any(String) })
    );
  });
});

// ─── useDeleteMeal ────────────────────────────────────────────────────────────

describe("useDeleteMeal", () => {
  it("faz DELETE em /api/v1/meals/{id}", async () => {
    mockedApi.delete.mockResolvedValueOnce({ data: null });

    const { result } = renderHook(() => useDeleteMeal(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync(1);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.delete).toHaveBeenCalledWith("/api/v1/meals/1");
  });

  it("chama toast.success após remover refeição", async () => {
    mockedApi.delete.mockResolvedValueOnce({ data: null });

    const { result } = renderHook(() => useDeleteMeal(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync(1);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedToast.success).toHaveBeenCalledWith("Refeição removida");
  });
});

// ─── useAnalyzeMeal ───────────────────────────────────────────────────────────

describe("useAnalyzeMeal", () => {
  it("faz POST em /api/v1/ai/analyze-meal com a descrição", async () => {
    const mockResponse = { items: [mockMealItem] };
    mockedApi.post.mockResolvedValueOnce({ data: mockResponse });

    const { result } = renderHook(() => useAnalyzeMeal(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync("Arroz com feijão");
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.post).toHaveBeenCalledWith("/api/v1/ai/analyze-meal", {
      description: "Arroz com feijão",
    });
    expect(result.current.data).toEqual(mockResponse);
  });
});

// ─── useAnalyzePhoto ──────────────────────────────────────────────────────────

describe("useAnalyzePhoto", () => {
  it("faz POST em /api/v1/ai/analyze-photo com base64 e mime_type", async () => {
    const mockResponse = { items: [mockMealItem] };
    mockedApi.post.mockResolvedValueOnce({ data: mockResponse });

    const { result } = renderHook(() => useAnalyzePhoto(), {
      wrapper: createWrapper(),
    });

    const payload = { image_base64: "abc123", mime_type: "image/jpeg" };

    await act(async () => {
      await result.current.mutateAsync(payload);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.post).toHaveBeenCalledWith(
      "/api/v1/ai/analyze-photo",
      payload
    );
    expect(result.current.data).toEqual(mockResponse);
  });
});
