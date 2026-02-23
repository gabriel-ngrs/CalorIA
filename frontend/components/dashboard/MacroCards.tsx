"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import type { NutritionSummary, User } from "@/types";

interface Props {
  nutrition: NutritionSummary;
  user: User | undefined;
}

const macros = [
  { label: "Calorias", key: "total_calories", unit: "kcal", goal: "calorie_goal", color: "bg-orange-500" },
  { label: "Proteína", key: "total_protein", unit: "g", goal: null, color: "bg-red-500" },
  { label: "Carboidrato", key: "total_carbs", unit: "g", goal: null, color: "bg-yellow-500" },
  { label: "Gordura", key: "total_fat", unit: "g", goal: null, color: "bg-blue-500" },
] as const;

export function MacroCards({ nutrition, user }: Props) {
  const calorieGoal = user?.calorie_goal ?? 2000;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {macros.map(({ label, key, unit }) => {
        const value = nutrition[key];
        const pct = key === "total_calories" ? Math.min((value / calorieGoal) * 100, 100) : null;

        return (
          <Card key={key}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">
                {value.toFixed(key === "total_calories" ? 0 : 1)}
                <span className="text-sm font-normal text-muted-foreground ml-1">{unit}</span>
              </p>
              {pct !== null && (
                <>
                  <Progress value={pct} className="mt-2 h-1.5" />
                  <p className="text-xs text-muted-foreground mt-1">
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
