"use client";

import { AlertTriangle, Droplets, Smile, Scale, UtensilsCrossed, Zap, TrendingDown, TrendingUp, Minus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
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

const MEAL_ACCENT: Record<MealType, { border: string; dot: string; cal: string }> = {
  breakfast:       { border: "border-l-amber-500",   dot: "bg-amber-500",   cal: "text-amber-500" },
  morning_snack:   { border: "border-l-yellow-400",  dot: "bg-yellow-400",  cal: "text-yellow-400" },
  lunch:           { border: "border-l-orange-500",  dot: "bg-orange-500",  cal: "text-orange-500" },
  afternoon_snack: { border: "border-l-green-500",   dot: "bg-green-500",   cal: "text-green-500" },
  dinner:          { border: "border-l-indigo-400",  dot: "bg-indigo-400",  cal: "text-indigo-400" },
  supper:          { border: "border-l-violet-400",  dot: "bg-violet-400",  cal: "text-violet-400" },
  snack:           { border: "border-l-teal-400",    dot: "bg-teal-400",    cal: "text-teal-400" },
  pre_workout:     { border: "border-l-red-500",     dot: "bg-red-500",     cal: "text-red-500" },
  post_workout:    { border: "border-l-blue-500",    dot: "bg-blue-500",    cal: "text-blue-500" },
  supplement:      { border: "border-l-purple-400",  dot: "bg-purple-400",  cal: "text-purple-400" },
};

const LEVEL_LABELS = ["Muito baixo", "Baixo", "Médio", "Alto", "Muito alto"];

function LevelDots({ value, color }: { value: number; color: string }) {
  return (
    <span className="flex gap-1">
      {[1, 2, 3, 4, 5].map((i) => (
        <span
          key={i}
          className={`inline-block w-2 h-2 rounded-full transition-colors ${i <= value ? color : "bg-muted"}`}
        />
      ))}
    </span>
  );
}

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

  const goalMl = user?.water_goal_ml ?? 2000;
  const hydPct = Math.min((dashboard.hydration.total_ml / goalMl) * 100, 100);

  const weightDelta = dashboard.latest_weight && user?.weight_goal
    ? dashboard.latest_weight.weight_kg - user.weight_goal
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold capitalize" suppressHydrationWarning>{today}</h1>
        <p className="text-muted-foreground text-sm">Resumo do seu dia</p>
      </div>

      {/* Macro cards */}
      <MacroCards nutrition={dashboard.nutrition} user={user} />

      {/* Linha secundária: Hidratação, Humor, Peso */}
      <div className="grid gap-4 md:grid-cols-3">

        {/* Hidratação */}
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-blue-500/40">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-1.5">
              <span className="flex items-center justify-center w-7 h-7 rounded-lg bg-blue-500/10">
                <Droplets className="h-4 w-4 text-blue-500" />
              </span>
              Hidratação
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-blue-500">
              {dashboard.hydration.total_ml}
              <span className="text-sm font-normal text-muted-foreground ml-1">ml</span>
            </p>
            <div className="mt-2 space-y-1">
              <Progress value={hydPct} indicatorColor="linear-gradient(90deg, #bfdbfe 0%, #3b82f6 100%)" />
              <p className="text-xs text-muted-foreground">
                {hydPct.toFixed(0)}% da meta · {goalMl} ml
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Humor */}
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-yellow-400/40">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-1.5">
              <span className="flex items-center justify-center w-7 h-7 rounded-lg bg-yellow-400/10">
                <Smile className="h-4 w-4 text-yellow-400" />
              </span>
              Humor do dia
            </CardTitle>
          </CardHeader>
          <CardContent>
            {dashboard.mood ? (
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                      <Zap className="h-3 w-3 text-orange-400" /> Energia
                    </p>
                    <div className="flex items-center gap-2">
                      <LevelDots value={dashboard.mood.energy_level} color="bg-orange-400" />
                      <span className="text-sm font-semibold">{dashboard.mood.energy_level}/5</span>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                      <Smile className="h-3 w-3 text-blue-400" /> Humor
                    </p>
                    <div className="flex items-center gap-2">
                      <LevelDots value={dashboard.mood.mood_level} color="bg-blue-400" />
                      <span className="text-sm font-semibold">{dashboard.mood.mood_level}/5</span>
                    </div>
                  </div>
                </div>
                {dashboard.mood.notes && (
                  <p className="text-xs text-muted-foreground italic truncate">
                    &ldquo;{dashboard.mood.notes}&rdquo;
                  </p>
                )}
                <p className="text-xs text-muted-foreground">
                  {LEVEL_LABELS[(dashboard.mood.energy_level + dashboard.mood.mood_level) / 2 > 3 ? 3 : Math.round((dashboard.mood.energy_level + dashboard.mood.mood_level) / 2) - 1]}
                </p>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Não registrado hoje</p>
            )}
          </CardContent>
        </Card>

        {/* Peso */}
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-primary/40">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-1.5">
              <span className="flex items-center justify-center w-7 h-7 rounded-lg bg-primary/10">
                <Scale className="h-4 w-4 text-primary" />
              </span>
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
                {user?.weight_goal && weightDelta !== null && (
                  <p className={`text-xs mt-1 flex items-center gap-1 ${weightDelta > 0 ? "text-orange-400" : weightDelta < 0 ? "text-green-500" : "text-muted-foreground"}`}>
                    {weightDelta > 0
                      ? <TrendingUp className="h-3 w-3" />
                      : weightDelta < 0
                      ? <TrendingDown className="h-3 w-3" />
                      : <Minus className="h-3 w-3" />}
                    Meta: {user.weight_goal} kg ({weightDelta > 0 ? "+" : ""}{weightDelta.toFixed(1)} kg)
                  </p>
                )}
              </>
            ) : (
              <p className="text-sm text-muted-foreground">Sem registro de peso</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Gráficos */}
      <div className="grid gap-4 md:grid-cols-2">
        <MacroPieChart nutrition={dashboard.nutrition} />
        {macros && <CaloriesBarChart data={macros} calorieGoal={user?.calorie_goal ?? undefined} />}
      </div>

      {/* Refeições do dia */}
      {dashboard.nutrition.meals.length > 0 && (
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-primary/30">
          <CardHeader>
            <CardTitle className="text-sm">Refeições de hoje</CardTitle>
          </CardHeader>
          <CardContent className="divide-y p-0">
            {dashboard.nutrition.meals.map((meal, i) => {
              const totalCal = meal.items.reduce((s, it) => s + it.calories, 0);
              const accent = MEAL_ACCENT[meal.meal_type];
              return (
                <div
                  key={i}
                  className={`py-2.5 px-6 flex items-start justify-between border-l-4 ${accent.border} transition-colors duration-150 hover:bg-muted/30`}
                >
                  <div>
                    <p className="text-sm font-medium flex items-center gap-1.5">
                      <span className={`inline-block h-2 w-2 rounded-full ${accent.dot}`} />
                      {MEAL_LABELS[meal.meal_type]}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {meal.items.map((it) => it.food_name).join(", ")}
                    </p>
                  </div>
                  <p className={`text-sm font-semibold shrink-0 ml-3 ${accent.cal}`}>
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
