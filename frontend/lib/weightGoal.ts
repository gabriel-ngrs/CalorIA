import type { GoalType } from "@/types";

/**
 * Lógica de "meta de peso" sensível ao objetivo do usuário (BUG 14).
 *
 * Antes a tela de Peso assumia sempre emagrecer (peso <= meta => atingida),
 * o que dava "Meta atingida!" indevido para quem quer ganhar massa. Aqui a
 * direção depende de `goalType`.
 */

/** Tolerância (kg) em torno da meta para objetivos de manutenção/recomposição. */
const MAINTAIN_TOLERANCE_KG = 1;

export interface WeightGoalStatus {
  /** Meta atingida na direção correta do objetivo. */
  reached: boolean;
  /** kg que faltam para a meta (0 se atingida). */
  remainingKg: number;
  /** Progresso 0..100 respeitando a direção do objetivo. */
  progressPct: number;
}

function clampPct(pct: number): number {
  return Math.min(Math.max(pct, 0), 100);
}

export function weightGoalStatus(params: {
  current: number;
  goal: number;
  start: number;
  goalType?: GoalType | null;
}): WeightGoalStatus {
  const { current, goal, start } = params;
  const goalType = params.goalType ?? "lose_weight";

  if (goalType === "gain_muscle") {
    const reached = current >= goal;
    const denom = goal - start;
    return {
      reached,
      remainingKg: reached ? 0 : goal - current,
      progressPct:
        denom <= 0 ? (reached ? 100 : 0) : clampPct(((current - start) / denom) * 100),
    };
  }

  if (goalType === "maintain" || goalType === "body_recomp") {
    const distance = Math.abs(current - goal);
    const startDistance = Math.abs(start - goal);
    const reached = distance <= MAINTAIN_TOLERANCE_KG;
    return {
      reached,
      remainingKg: reached ? 0 : distance,
      progressPct:
        startDistance === 0 ? 100 : clampPct((1 - distance / startDistance) * 100),
    };
  }

  // lose_weight (padrão)
  const reached = current <= goal;
  const denom = start - goal;
  return {
    reached,
    remainingKg: reached ? 0 : current - goal,
    progressPct:
      denom <= 0 ? (reached ? 100 : 0) : clampPct(((start - current) / denom) * 100),
  };
}
