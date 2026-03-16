import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Reminder, ReminderType } from "@/types";

export type ReminderPayload = {
  type: ReminderType;
  time: string;
  days_of_week: number[];
  message?: string;
};

export function useReminders() {
  return useQuery<Reminder[]>({
    queryKey: ["reminders"],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/reminders");
      return data;
    },
  });
}

export function useCreateReminder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ReminderPayload) => {
      const { data } = await api.post("/api/v1/reminders", payload);
      return data as Reminder;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reminders"] }),
  });
}

export function useCreateRemindersBatch() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payloads: ReminderPayload[]) => {
      const { data } = await api.post("/api/v1/reminders/batch", payloads);
      return data as Reminder[];
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reminders"] }),
  });
}

export function useToggleReminder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.patch(`/api/v1/reminders/${id}/toggle`);
      return data as Reminder;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reminders"] }),
  });
}

export function useDeleteReminder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/v1/reminders/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reminders"] }),
  });
}
