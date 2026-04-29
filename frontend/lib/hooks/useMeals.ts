import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
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
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["meals"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      const totalCal = data.items.reduce((s: number, it: { calories: number }) => s + it.calories, 0);
      toast.success("Refeição salva!", {
        description: `${data.items.length} ${data.items.length === 1 ? "item" : "itens"} · ${totalCal.toFixed(0)} kcal`,
      });
    },
    onError: () => toast.error("Erro ao salvar refeição"),
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
      toast.success("Refeição removida");
    },
    onError: () => toast.error("Erro ao remover refeição"),
  });
}

export function useDeleteMealItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ mealId, itemId }: { mealId: number; itemId: number }) => {
      await api.delete(`/api/v1/meals/${mealId}/items/${itemId}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["meals"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: () => toast.error("Erro ao remover item"),
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

export function useAnalyzePhoto() {
  return useMutation({
    mutationFn: async ({ image_base64, mime_type }: { image_base64: string; mime_type: string }) => {
      const { data } = await api.post("/api/v1/ai/analyze-photo", { image_base64, mime_type });
      return data;
    },
  });
}
