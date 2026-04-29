import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { GoalType, User, UserProfile } from "@/types";

export function useMe() {
  return useQuery<User>({
    queryKey: ["me"],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/auth/me");
      return data;
    },
    staleTime: 15 * 60 * 1000, // 15 min — dados do usuário raramente mudam
  });
}

export function useProfile() {
  return useQuery<UserProfile>({
    queryKey: ["profile"],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/users/me/profile");
      return data;
    },
  });
}

export function useUpdateProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<UserProfile>) => {
      const { data } = await api.put("/api/v1/users/me/profile", payload);
      return data as UserProfile;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["profile"] });
      qc.invalidateQueries({ queryKey: ["me"] });
    },
  });
}

export function useUpdateMe() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { name?: string; calorie_goal?: number; weight_goal?: number; water_goal_ml?: number; goal_type?: GoalType }) => {
      const { data } = await api.patch("/api/v1/users/me", payload);
      return data as User;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["me"] }),
  });
}
