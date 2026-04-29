import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import api from "@/lib/api";
import { toast } from "sonner";
import {
  useWeightLogs,
  useLogWeight,
  useHydrationToday,
  useHydrationHistory,
  useLogHydration,
  useMoodLogs,
  useLogMood,
} from "@/lib/hooks/useLogs";

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

const mockWeightLog = {
  id: 1,
  weight_kg: 74.5,
  date: "2026-03-15",
  notes: null,
  created_at: "2026-03-15T08:00:00Z",
};

const mockHydrationToday = {
  date: "2026-03-15",
  total_ml: 1500,
  entries: [
    {
      id: 1,
      amount_ml: 300,
      date: "2026-03-15",
      time: "08:00",
      created_at: "2026-03-15T08:00:00Z",
    },
  ],
};

const mockHydrationLog = {
  id: 2,
  amount_ml: 500,
  date: "2026-03-15",
  time: "10:00",
  created_at: "2026-03-15T10:00:00Z",
};

const mockMoodLog = {
  id: 1,
  date: "2026-03-15",
  energy_level: 4,
  mood_level: 3,
  notes: null,
  created_at: "2026-03-15T09:00:00Z",
};

beforeEach(() => {
  jest.clearAllMocks();
});

// ─── useWeightLogs ────────────────────────────────────────────────────────────

describe("useWeightLogs", () => {
  it("busca registros de peso de /api/v1/weight", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: [mockWeightLog] });

    const { result } = renderHook(() => useWeightLogs(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/weight");
    expect(result.current.data).toEqual([mockWeightLog]);
  });
});

// ─── useLogWeight ─────────────────────────────────────────────────────────────

describe("useLogWeight", () => {
  it("faz POST em /api/v1/weight com o payload correto", async () => {
    mockedApi.post.mockResolvedValueOnce({ data: mockWeightLog });

    const { result } = renderHook(() => useLogWeight(), {
      wrapper: createWrapper(),
    });

    const payload = { weight_kg: 74.5, date: "2026-03-15" };

    await act(async () => {
      await result.current.mutateAsync(payload);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.post).toHaveBeenCalledWith("/api/v1/weight", payload);
  });

  it("chama toast.success após registrar peso", async () => {
    mockedApi.post.mockResolvedValueOnce({ data: mockWeightLog });

    const { result } = renderHook(() => useLogWeight(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({ weight_kg: 74.5, date: "2026-03-15" });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedToast.success).toHaveBeenCalledWith(
      "Peso registrado",
      expect.objectContaining({ description: "74.5 kg salvo com sucesso." })
    );
  });
});

// ─── useHydrationToday ────────────────────────────────────────────────────────

describe("useHydrationToday", () => {
  it("busca hidratação de hoje de /api/v1/hydration/today", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: mockHydrationToday });

    const { result } = renderHook(() => useHydrationToday(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/hydration/today");
    expect(result.current.data).toEqual(mockHydrationToday);
  });
});

// ─── useHydrationHistory ──────────────────────────────────────────────────────

describe("useHydrationHistory", () => {
  it("busca histórico de hidratação com days=7 por padrão", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: [mockHydrationToday] });

    const { result } = renderHook(() => useHydrationHistory(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith(
      "/api/v1/hydration/history?days=7"
    );
    expect(result.current.data).toEqual([mockHydrationToday]);
  });

  it("usa o valor de days fornecido", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: [mockHydrationToday] });

    const { result } = renderHook(() => useHydrationHistory(30), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith(
      "/api/v1/hydration/history?days=30"
    );
  });
});

// ─── useLogHydration ──────────────────────────────────────────────────────────

describe("useLogHydration", () => {
  it("faz POST em /api/v1/hydration com o payload correto", async () => {
    mockedApi.post.mockResolvedValueOnce({ data: mockHydrationLog });

    const { result } = renderHook(() => useLogHydration(), {
      wrapper: createWrapper(),
    });

    const payload = { amount_ml: 500, date: "2026-03-15", time: "10:00" };

    await act(async () => {
      await result.current.mutateAsync(payload);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.post).toHaveBeenCalledWith("/api/v1/hydration", payload);
  });

  it("chama toast.success após registrar água", async () => {
    mockedApi.post.mockResolvedValueOnce({ data: mockHydrationLog });

    const { result } = renderHook(() => useLogHydration(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({
        amount_ml: 500,
        date: "2026-03-15",
        time: "10:00",
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedToast.success).toHaveBeenCalledWith(
      "Água registrada",
      expect.objectContaining({ description: "+500 ml adicionados." })
    );
  });
});

// ─── useMoodLogs ──────────────────────────────────────────────────────────────

describe("useMoodLogs", () => {
  it("busca registros de humor de /api/v1/mood", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: [mockMoodLog] });

    const { result } = renderHook(() => useMoodLogs(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/mood");
    expect(result.current.data).toEqual([mockMoodLog]);
  });
});

// ─── useLogMood ───────────────────────────────────────────────────────────────

describe("useLogMood", () => {
  it("faz POST em /api/v1/mood com o payload correto", async () => {
    mockedApi.post.mockResolvedValueOnce({ data: mockMoodLog });

    const { result } = renderHook(() => useLogMood(), {
      wrapper: createWrapper(),
    });

    const payload = {
      date: "2026-03-15",
      energy_level: 4,
      mood_level: 3,
    };

    await act(async () => {
      await result.current.mutateAsync(payload);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.post).toHaveBeenCalledWith("/api/v1/mood", payload);
  });

  it("chama toast.success após registrar humor", async () => {
    mockedApi.post.mockResolvedValueOnce({ data: mockMoodLog });

    const { result } = renderHook(() => useLogMood(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({
        date: "2026-03-15",
        energy_level: 4,
        mood_level: 3,
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedToast.success).toHaveBeenCalledWith(
      "Humor registrado",
      expect.objectContaining({
        description: "Energia 4/5 · Humor 3/5",
      })
    );
  });
});
