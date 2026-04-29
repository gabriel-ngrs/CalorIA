"use client";

import { Flame, Dumbbell, Zap, Droplets } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import type { NutritionSummary, User } from "@/types";

interface Props {
  nutrition: NutritionSummary;
  user: User | undefined;
  onCaloriesClick?: () => void;
}

const macros = [
  {
    label: "Calorias",
    shortLabel: "Calorias",
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
    shortLabel: "Proteína",
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
    shortLabel: "Carbs",
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
    shortLabel: "Gordura",
    key: "total_fat",
    unit: "g",
    Icon: Droplets,
    color: "#EF4444",
    bgColor: "bg-red-500/10",
    iconColor: "text-red-500",
    decimals: 1,
    hoverBorder: "hover:border-red-500/40",
    hoverShadow: "hover:shadow-red-500/10",
  },
] as const;

export function MacroCards({ nutrition, user, onCaloriesClick }: Props) {
  const calorieGoal = user?.calorie_goal ?? 2000;

  // Metas estimadas por macro (proteína 30%, carbs 45%, gordura 25% do TDEE)
  const proteinGoal = Math.round((calorieGoal * 0.30) / 4);
  const carbsGoal = Math.round((calorieGoal * 0.45) / 4);
  const fatGoal = Math.round((calorieGoal * 0.25) / 9);

  const goals: Record<string, number> = {
    total_calories: calorieGoal,
    total_protein: proteinGoal,
    total_carbs: carbsGoal,
    total_fat: fatGoal,
  };

  return (
    <div className="grid grid-cols-2 gap-2.5 lg:grid-cols-4">
      {macros.map(({ label, shortLabel, key, unit, Icon, color, bgColor, iconColor, decimals, hoverBorder, hoverShadow }) => {
        const value = nutrition[key];
        const goal = goals[key];
        const pct = Math.min((value / goal) * 100, 100);

        const isCalories = key === "total_calories";
        return (
          <Card
            key={key}
            onClick={isCalories && onCaloriesClick ? onCaloriesClick : undefined}
            className={cn(
              "transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl",
              hoverBorder,
              hoverShadow,
              isCalories && onCaloriesClick && "cursor-pointer"
            )}
          >
            <CardHeader className="pb-1.5 pt-4 px-4">
              <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider flex items-center justify-center sm:justify-start gap-1.5">
                <span className={`flex items-center justify-center w-6 h-6 rounded-lg shrink-0 ${bgColor}`}>
                  <Icon className={`h-3.5 w-3.5 ${iconColor}`} />
                </span>
                <span className="sm:hidden">{shortLabel}</span>
                <span className="hidden sm:inline">{label}</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4 text-center sm:text-left">
              <p className="text-2xl font-black" style={{ color }}>
                {value.toFixed(decimals)}
                <span className="text-xs font-normal text-muted-foreground ml-1">{unit}</span>
              </p>

              <div className="mt-1.5 space-y-0.5">
                <Progress value={pct} indicatorColor={color} />
                <p className="text-xs text-muted-foreground text-left">
                  {pct.toFixed(0)}% · meta {goal}{unit}
                </p>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
