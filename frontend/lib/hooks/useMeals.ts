import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Meal, MealCreate, MealUpdate } from "@/types";

export function useMeals(date?: string) {
  return useQuery<Meal[]>({
    queryKey: ["meals", date],
    queryFn: async () => {
      const params = date ? `?date=${date}` : "";
      const { data } = await api.get(`/api/v1/meals${params}`);
      return data;
    },
    // Usa os defaults globais (staleTime: 3min, refetchOnWindowFocus: false)
    // Mutations (create/update/delete) já invalidam o cache via onSuccess
  });
}

export function useMeal(id: number) {
  return useQuery<Meal>({
    queryKey: ["meals", id],
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/meals/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateMeal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: MealCreate) => {
      const { data } = await api.post("/api/v1/meals", body);
      return data as Meal;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["meals"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useUpdateMeal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: MealUpdate }) => {
      const { data: res } = await api.patch(`/api/v1/meals/${id}`, data);
      return res as Meal;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["meals"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useDeleteMeal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/v1/meals/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["meals"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useAnalyzeMeal() {
  return useMutation({
    mutationFn: async (description: string) => {
      const { data } = await api.post("/api/v1/ai/analyze-meal", { description });
      return data;
    },
  });
}
