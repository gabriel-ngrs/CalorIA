"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import type { NutritionSummary, User } from "@/types";

interface Props {
  nutrition: NutritionSummary;
  user: User | undefined;
}

const macros = [
  {
    label: "Calorias",
    key: "total_calories",
    unit: "kcal",
    icon: "🔥",
    color: "#f97316",
    glow: "rgba(249,115,22,0.25)",
  },
  {
    label: "Proteína",
    key: "total_protein",
    unit: "g",
    icon: "💪",
    color: "#22c55e",
    glow: "rgba(34,197,94,0.22)",
  },
  {
    label: "Carboidrato",
    key: "total_carbs",
    unit: "g",
    icon: "⚡",
    color: "#eab308",
    glow: "rgba(234,179,8,0.22)",
  },
  {
    label: "Gordura",
    key: "total_fat",
    unit: "g",
    icon: "🫧",
    color: "#3b82f6",
    glow: "rgba(59,130,246,0.22)",
  },
] as const;

export function MacroCards({ nutrition, user }: Props) {
  const calorieGoal = user?.calorie_goal ?? 2000;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {macros.map(({ label, key, unit, icon, color, glow }) => {
        const value = nutrition[key];
        const pct =
          key === "total_calories" ? Math.min((value / calorieGoal) * 100, 100) : null;

        return (
          <Card
            key={key}
            className="relative overflow-hidden"
            style={{
              boxShadow: `0 4px 24px var(--glass-shadow), 0 0 0 1px var(--glass-border), 0 0 20px ${glow}`,
            }}
          >
            {/* Orbe decorativo de fundo */}
            <div
              className="absolute -top-6 -right-6 w-20 h-20 rounded-full opacity-15 pointer-events-none"
              style={{
                background: `radial-gradient(circle, ${color} 0%, transparent 70%)`,
                filter: "blur(8px)",
              }}
            />

            <CardHeader className="pb-2 relative">
              <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <span>{icon}</span>
                {label}
              </CardTitle>
            </CardHeader>

            <CardContent className="relative">
              <p className="text-3xl font-bold" style={{ color }}>
                {value.toFixed(key === "total_calories" ? 0 : 1)}
                <span className="text-sm font-normal text-muted-foreground ml-1">{unit}</span>
              </p>

              {pct !== null && (
                <>
                  <Progress value={pct} className="mt-3" />
                  <p className="text-xs text-muted-foreground mt-1.5">
                    {pct.toFixed(0)}% da meta ({calorieGoal} kcal)
                  </p>
                </>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
