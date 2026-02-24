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
    decimals: 0,
  },
  {
    label: "Proteína",
    key: "total_protein",
    unit: "g",
    icon: "💪",
    color: "#22c55e",
    decimals: 1,
  },
  {
    label: "Carboidrato",
    key: "total_carbs",
    unit: "g",
    icon: "⚡",
    color: "#eab308",
    decimals: 1,
  },
  {
    label: "Gordura",
    key: "total_fat",
    unit: "g",
    icon: "🫧",
    color: "#7CA2B2",
    decimals: 1,
  },
] as const;

export function MacroCards({ nutrition, user }: Props) {
  const calorieGoal = user?.calorie_goal ?? 2000;

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {macros.map(({ label, key, unit, icon, color, decimals }) => {
        const value = nutrition[key];
        const pct =
          key === "total_calories" ? Math.min((value / calorieGoal) * 100, 100) : null;

        return (
          <Card key={key}>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <span className="text-sm">{icon}</span>
                {label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold" style={{ color }}>
                {value.toFixed(decimals)}
                <span className="text-xs font-normal text-muted-foreground ml-1">{unit}</span>
              </p>

              {pct !== null && (
                <div className="mt-2 space-y-1">
                  <Progress value={pct} />
                  <p className="text-xs text-muted-foreground">
                    {pct.toFixed(0)}% da meta · {calorieGoal} kcal
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
