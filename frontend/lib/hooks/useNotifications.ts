"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { AppNotification } from "@/types";

export function useNotifications(limit = 20) {
  return useQuery<AppNotification[]>({
    queryKey: ["notifications", limit],
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/notifications?limit=${limit}`);
      return data;
    },
    refetchInterval: 30_000, // poll every 30s
    staleTime: 15_000,
  });
}

export function useUnreadCount() {
  return useQuery<{ count: number }>({
    queryKey: ["notifications", "unread-count"],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/notifications/unread-count");
      return data;
    },
    refetchInterval: 30_000,
    staleTime: 15_000,
  });
}

export function useMarkNotificationRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.patch(`/api/v1/notifications/${id}/read`);
      return data as AppNotification;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

export function useMarkAllRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await api.post("/api/v1/notifications/read-all");
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}
