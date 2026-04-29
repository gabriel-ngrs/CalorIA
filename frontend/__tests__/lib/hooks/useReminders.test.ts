import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import api from "@/lib/api";
import {
  useReminders,
  useCreateReminder,
  useCreateRemindersBatch,
  useToggleReminder,
  useDeleteReminder,
} from "@/lib/hooks/useReminders";
import type { ReminderPayload } from "@/lib/hooks/useReminders";

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

const mockReminder = {
  id: 1,
  type: "meal",
  time: "08:00",
  days_of_week: [1, 2, 3, 4, 5],
  message: "Hora do café da manhã!",
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
};

const mockReminderPayload: ReminderPayload = {
  type: "meal",
  time: "08:00",
  days_of_week: [1, 2, 3, 4, 5],
  message: "Hora do café da manhã!",
};

beforeEach(() => {
  jest.clearAllMocks();
});

// ─── useReminders ─────────────────────────────────────────────────────────────

describe("useReminders", () => {
  it("busca lembretes de /api/v1/reminders", async () => {
    mockedApi.get.mockResolvedValueOnce({ data: [mockReminder] });

    const { result } = renderHook(() => useReminders(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/reminders");
    expect(result.current.data).toEqual([mockReminder]);
  });
});

// ─── useCreateReminder ────────────────────────────────────────────────────────

describe("useCreateReminder", () => {
  it("faz POST em /api/v1/reminders com o payload correto", async () => {
    mockedApi.post.mockResolvedValueOnce({ data: mockReminder });

    const { result } = renderHook(() => useCreateReminder(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync(mockReminderPayload);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.post).toHaveBeenCalledWith(
      "/api/v1/reminders",
      mockReminderPayload
    );
    expect(result.current.data).toEqual(mockReminder);
  });
});

// ─── useCreateRemindersBatch ──────────────────────────────────────────────────

describe("useCreateRemindersBatch", () => {
  it("faz POST em /api/v1/reminders/batch com array de payloads", async () => {
    const mockBatch = [mockReminder, { ...mockReminder, id: 2, time: "12:00" }];
    mockedApi.post.mockResolvedValueOnce({ data: mockBatch });

    const { result } = renderHook(() => useCreateRemindersBatch(), {
      wrapper: createWrapper(),
    });

    const payloads = [
      mockReminderPayload,
      { ...mockReminderPayload, time: "12:00" },
    ];

    await act(async () => {
      await result.current.mutateAsync(payloads);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.post).toHaveBeenCalledWith(
      "/api/v1/reminders/batch",
      payloads
    );
    expect(result.current.data).toEqual(mockBatch);
  });
});

// ─── useToggleReminder ────────────────────────────────────────────────────────

describe("useToggleReminder", () => {
  it("faz PATCH em /api/v1/reminders/{id}/toggle", async () => {
    const toggled = { ...mockReminder, is_active: false };
    mockedApi.patch.mockResolvedValueOnce({ data: toggled });

    const { result } = renderHook(() => useToggleReminder(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync(1);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.patch).toHaveBeenCalledWith(
      "/api/v1/reminders/1/toggle"
    );
    expect(result.current.data).toEqual(toggled);
  });
});

// ─── useDeleteReminder ────────────────────────────────────────────────────────

describe("useDeleteReminder", () => {
  it("faz DELETE em /api/v1/reminders/{id}", async () => {
    mockedApi.delete.mockResolvedValueOnce({ data: null });

    const { result } = renderHook(() => useDeleteReminder(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync(1);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.delete).toHaveBeenCalledWith("/api/v1/reminders/1");
  });
});
