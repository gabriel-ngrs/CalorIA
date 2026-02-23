import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Reminder, ReminderChannel, ReminderType } from "@/types";

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
    mutationFn: async (payload: {
      type: ReminderType;
      time: string;
      channel: ReminderChannel;
      days_of_week: number[];
      message?: string;
    }) => {
      const { data } = await api.post("/api/v1/reminders", payload);
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
