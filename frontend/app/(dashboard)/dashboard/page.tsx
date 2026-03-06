"use client";

import { AlertTriangle, Droplets, Smile, Scale, UtensilsCrossed } from "lucide-react";
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
  morning_snack: "Lanche da manhã",
  lunch: "Almoço",
  afternoon_snack: "Lanche da tarde",
  dinner: "Jantar",
  supper: "Ceia",
  snack: "Lanche",
  pre_workout: "Pré-treino",
  post_workout: "Pós-treino",
  supplement: "Suplemento",
};

const MEAL_COLORS: Record<MealType, string> = {
  breakfast: "text-amber-500",
  morning_snack: "text-yellow-400",
  lunch: "text-orange-500",
  afternoon_snack: "text-green-500",
  dinner: "text-indigo-400",
  supper: "text-violet-400",
  snack: "text-teal-400",
  pre_workout: "text-red-500",
  post_workout: "text-blue-500",
  supplement: "text-purple-400",
};

export default function DashboardPage() {
  const { data: dashboard, isLoading, isError } = useDashboardToday();
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

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3 text-center">
        <AlertTriangle className="h-12 w-12 text-destructive/70" />
        <h2 className="text-xl font-semibold">Erro ao carregar dados</h2>
        <p className="text-muted-foreground text-sm max-w-xs">
          Não foi possível conectar ao servidor. Tente recarregar a página.
        </p>
      </div>
    );
  }

  const isEmpty =
    !dashboard ||
    (dashboard.nutrition.meals_count === 0 &&
      dashboard.hydration.total_ml === 0 &&
      !dashboard.mood &&
      !dashboard.latest_weight);

  if (isEmpty) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3 text-center">
        <UtensilsCrossed className="h-12 w-12 text-muted-foreground/40" />
        <h2 className="text-xl font-semibold">Nenhum dado para hoje</h2>
        <p className="text-muted-foreground text-sm max-w-xs">
          Registre sua primeira refeição pelo Telegram, WhatsApp ou pela página de Refeições.
        </p>
      </div>
    );
  }

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
            <CardTitle className="text-sm flex items-center gap-1.5">
              <Smile className="h-4 w-4 text-yellow-400" />
              Humor do dia
            </CardTitle>
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
            <CardTitle className="text-sm flex items-center gap-1.5">
              <Scale className="h-4 w-4 text-primary" />
              Peso atual
            </CardTitle>
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
                    <p className="text-sm font-medium flex items-center gap-1.5">
                      <span className={`inline-block h-2 w-2 rounded-full bg-current ${MEAL_COLORS[meal.meal_type]}`} />
                      {MEAL_LABELS[meal.meal_type]}
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
