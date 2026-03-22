import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import api from "@/lib/api";
import {
  useMe,
  useProfile,
  useUpdateProfile,
  useUpdateMe,
} from "@/lib/hooks/useProfile";

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

const mockUser = {
  id: 1,
  name: "Gabriel",
  email: "gabriel@caloria.com",
  calorie_goal: 2000,
  weight_goal: 70,
  water_goal_ml: 2000,
  goal_type: "maintain",
  profile: null,
  created_at: "2026-01-01T00:00:00Z",
};

const mockProfile = {
  id: 1,
  user_id: 1,
  age: 30,
  height_cm: 175,
  weight_kg: 74.5,
  activity_level: "moderate",
  dietary_restrictions: [],
  created_at: "2026-01-01T00:00:00Z",
};

beforeEach(() => {
  jest.clearAllMocks();
});

// ─── useMe ────────────────────────────────────────────────────────────────────

describe("useMe", () => {
  it("busca o usuário atual de /api/v1/auth/me", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: mockUser });

    const { result } = renderHook(() => useMe(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/auth/me");
    expect(result.current.data).toEqual(mockUser);
  });

  it("inicia a query em estado de carregamento", () => {
    mockedApi.get.mockResolvedValue({ data: mockUser });

    const { result } = renderHook(() => useMe(), {
      wrapper: createWrapper(),
    });

    // staleTime alto impede refetch automático, mas a query ainda carrega na montagem
    expect(result.current.isPending).toBe(true);
  });
});

// ─── useProfile ───────────────────────────────────────────────────────────────

describe("useProfile", () => {
  it("busca o perfil de /api/v1/users/me/profile", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: mockProfile });

    const { result } = renderHook(() => useProfile(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/users/me/profile");
    expect(result.current.data).toEqual(mockProfile);
  });
});

// ─── useUpdateProfile ─────────────────────────────────────────────────────────

describe("useUpdateProfile", () => {
  it("faz PUT em /api/v1/users/me/profile com o payload", async () => {
    mockedApi.put.mockResolvedValueOnce({ data: mockProfile });

    const { result } = renderHook(() => useUpdateProfile(), {
      wrapper: createWrapper(),
    });

    const payload = { height_cm: 176, activity_level: "moderately_active" as const };

    await act(async () => {
      await result.current.mutateAsync(payload);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.put).toHaveBeenCalledWith(
      "/api/v1/users/me/profile",
      payload
    );
  });
});

// ─── useUpdateMe ──────────────────────────────────────────────────────────────

describe("useUpdateMe", () => {
  it("faz PATCH em /api/v1/users/me com o payload", async () => {
    mockedApi.patch.mockResolvedValueOnce({ data: mockUser });

    const { result } = renderHook(() => useUpdateMe(), {
      wrapper: createWrapper(),
    });

    const payload = { name: "Gabriel Silva", calorie_goal: 2200 };

    await act(async () => {
      await result.current.mutateAsync(payload);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.patch).toHaveBeenCalledWith("/api/v1/users/me", payload);
  });
});
