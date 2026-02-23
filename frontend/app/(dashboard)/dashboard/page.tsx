"use client";

import { Droplets } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { MacroCards } from "@/components/dashboard/MacroCards";
import { MacroPieChart } from "@/components/dashboard/MacroPieChart";
import { CaloriesBarChart } from "@/components/dashboard/CaloriesBarChart";
import { useDashboardToday, useMacrosChart } from "@/lib/hooks/useDashboard";
import { useMe } from "@/lib/hooks/useProfile";
import type { MealType } from "@/types";

const MEAL_LABELS: Record<MealType, string> = {
  breakfast: "Café da manhã",
  lunch: "Almoço",
  dinner: "Jantar",
  snack: "Lanche",
};

const MEAL_EMOJIS: Record<MealType, string> = {
  breakfast: "☀️",
  lunch: "🍽️",
  dinner: "🌙",
  snack: "🍎",
};

export default function DashboardPage() {
  const { data: dashboard, isLoading } = useDashboardToday();
  const { data: macros } = useMacrosChart(7);
  const { data: user } = useMe();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      </div>
    );
  }

  if (!dashboard) return null;

  const today = new Date().toLocaleDateString("pt-BR", {
    weekday: "long",
    day: "2-digit",
    month: "long",
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold capitalize">{today}</h1>
        <p className="text-muted-foreground text-sm">Resumo do seu dia</p>
      </div>

      <MacroCards nutrition={dashboard.nutrition} user={user} />

      <div className="grid gap-4 md:grid-cols-3">
        {/* Hidratação */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-1.5">
              <Droplets className="h-4 w-4 text-blue-500" />
              Hidratação
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {dashboard.hydration.total_ml}
              <span className="text-sm font-normal text-muted-foreground ml-1">ml</span>
            </p>
            <div className="mt-2 flex gap-0.5">
              {[...Array(10)].map((_, i) => (
                <div
                  key={i}
                  className={`h-2 flex-1 rounded-full ${
                    i < Math.floor((dashboard.hydration.total_ml / 2000) * 10)
                      ? "bg-blue-500"
                      : "bg-muted"
                  }`}
                />
              ))}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {Math.min((dashboard.hydration.total_ml / 2000) * 100, 100).toFixed(0)}% da meta (2000 ml)
            </p>
          </CardContent>
        </Card>

        {/* Humor */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">😊 Humor do dia</CardTitle>
          </CardHeader>
          <CardContent>
            {dashboard.mood ? (
              <>
                <div className="flex gap-4">
                  <div>
                    <p className="text-xs text-muted-foreground">Energia</p>
                    <p className="text-2xl font-bold">{dashboard.mood.energy_level}/5</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Humor</p>
                    <p className="text-2xl font-bold">{dashboard.mood.mood_level}/5</p>
                  </div>
                </div>
                {dashboard.mood.notes && (
                  <p className="text-xs text-muted-foreground mt-2 italic">
                    &ldquo;{dashboard.mood.notes}&rdquo;
                  </p>
                )}
              </>
            ) : (
              <p className="text-sm text-muted-foreground">Não registrado hoje</p>
            )}
          </CardContent>
        </Card>

        {/* Peso */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">⚖️ Peso atual</CardTitle>
          </CardHeader>
          <CardContent>
            {dashboard.latest_weight ? (
              <>
                <p className="text-2xl font-bold">
                  {dashboard.latest_weight.weight_kg}
                  <span className="text-sm font-normal text-muted-foreground ml-1">kg</span>
                </p>
                {user?.weight_goal && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Meta: {user.weight_goal} kg (
                    {(dashboard.latest_weight.weight_kg - user.weight_goal > 0 ? "+" : "")}
                    {(dashboard.latest_weight.weight_kg - user.weight_goal).toFixed(1)} kg)
                  </p>
                )}
              </>
            ) : (
              <p className="text-sm text-muted-foreground">Sem registro de peso</p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <MacroPieChart nutrition={dashboard.nutrition} />
        {macros && <CaloriesBarChart data={macros} calorieGoal={user?.calorie_goal ?? undefined} />}
      </div>

      {/* Refeições do dia */}
      {dashboard.nutrition.meals.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Refeições de hoje</CardTitle>
          </CardHeader>
          <CardContent className="divide-y">
            {dashboard.nutrition.meals.map((meal, i) => {
              const totalCal = meal.items.reduce((s, it) => s + it.calories, 0);
              return (
                <div key={i} className="py-2 flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium">
                      {MEAL_EMOJIS[meal.meal_type]} {MEAL_LABELS[meal.meal_type]}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {meal.items.map((it) => it.food_name).join(", ")}
                    </p>
                  </div>
                  <p className="text-sm font-semibold text-orange-600">
                    {totalCal.toFixed(0)} kcal
                  </p>
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
