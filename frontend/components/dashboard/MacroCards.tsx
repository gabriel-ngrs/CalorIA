"use client";

import { Flame, Dumbbell, Zap, Droplets } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
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
    Icon: Flame,
    color: "#f97316",
    bgColor: "bg-orange-500/10",
    iconColor: "text-orange-500",
    decimals: 0,
    hoverBorder: "hover:border-orange-500/40",
    hoverShadow: "hover:shadow-orange-500/10",
  },
  {
    label: "Proteína",
    key: "total_protein",
    unit: "g",
    Icon: Dumbbell,
    color: "#22c55e",
    bgColor: "bg-green-500/10",
    iconColor: "text-green-500",
    decimals: 1,
    hoverBorder: "hover:border-green-500/40",
    hoverShadow: "hover:shadow-green-500/10",
  },
  {
    label: "Carboidrato",
    key: "total_carbs",
    unit: "g",
    Icon: Zap,
    color: "#eab308",
    bgColor: "bg-yellow-500/10",
    iconColor: "text-yellow-500",
    decimals: 1,
    hoverBorder: "hover:border-yellow-500/40",
    hoverShadow: "hover:shadow-yellow-500/10",
  },
  {
    label: "Gordura",
    key: "total_fat",
    unit: "g",
    Icon: Droplets,
    color: "#7CA2B2",
    bgColor: "bg-sky-400/10",
    iconColor: "text-sky-400",
    decimals: 1,
    hoverBorder: "hover:border-sky-400/40",
    hoverShadow: "hover:shadow-sky-400/10",
  },
] as const;

export function MacroCards({ nutrition, user }: Props) {
  const calorieGoal = user?.calorie_goal ?? 2000;

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {macros.map(({ label, key, unit, Icon, color, bgColor, iconColor, decimals, hoverBorder, hoverShadow }) => {
        const value = nutrition[key];
        const pct =
          key === "total_calories" ? Math.min((value / calorieGoal) * 100, 100) : null;

        return (
          <Card
            key={key}
            className={cn(
              "transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl",
              hoverBorder,
              hoverShadow
            )}
          >
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                <span className={`flex items-center justify-center w-7 h-7 rounded-lg ${bgColor}`}>
                  <Icon className={`h-4 w-4 ${iconColor}`} />
                </span>
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
