"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import {
  BarChart2,
  Flame,
  Dumbbell,
  Droplets,
  TrendingUp,
  TrendingDown,
  Minus,
  Zap,
  Smile,
  Trophy,
  Target,
  UtensilsCrossed,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useMacrosChart, useWeightChart } from "@/lib/hooks/useDashboard";
import { useMoodLogs, useHydrationHistory } from "@/lib/hooks/useLogs";
import { useMe } from "@/lib/hooks/useProfile";
import type { WeeklyMacroPoint, WeightChartPoint } from "@/types";

const CaloriesBarChart = dynamic(
  () =>
    import("@/components/dashboard/CaloriesBarChart").then(
      (m) => m.CaloriesBarChart
    ),
  { ssr: false, loading: () => <Skeleton className="h-[240px] w-full" /> }
);

const WeightAreaChart = dynamic(
  () =>
    import("@/components/charts/WeightAreaChart").then(
      (m) => m.WeightAreaChart
    ),
  { ssr: false, loading: () => <Skeleton className="h-[240px] w-full" /> }
);

const HydrationBarChart = dynamic(
  () =>
    import("@/components/charts/HydrationBarChart").then(
      (m) => m.HydrationBarChart
    ),
  { ssr: false, loading: () => <Skeleton className="h-[240px] w-full" /> }
);

const MoodLineChart = dynamic(
  () =>
    import("@/components/charts/MoodLineChart").then((m) => m.MoodLineChart),
  { ssr: false, loading: () => <Skeleton className="h-[240px] w-full" /> }
);

const WEEKDAY_NAMES = [
  "Domingos",
  "Segundas",
  "Terças",
  "Quartas",
  "Quintas",
  "Sextas",
  "Sábados",
];

const DEFAULT_GOAL_ML = 2000;

export default function RelatoriosPage() {
  const [period, setPeriod] = useState<7 | 14 | 30>(7);

  const { data: macros } = useMacrosChart(period);
  const { data: weightData } = useWeightChart(period);
  const { data: logs } = useMoodLogs();
  const { data: hydration } = useHydrationHistory(period);
  const { data: user } = useMe();

  const calorieGoal = user?.calorie_goal ?? undefined;
  const goalMl = user?.water_goal_ml ?? DEFAULT_GOAL_ML;

  // ── Macro chart data — dados brutos; CaloriesBarChart faz sua própria formatação ──
  const macroChartData: WeeklyMacroPoint[] = macros ?? [];

  // ── Summary stats ─────────────────────────────────────────────────────────
  const avgCalories =
    macros && macros.length > 0
      ? Math.round(macros.reduce((s, d) => s + d.calories, 0) / macros.length)
      : 0;

  const avgProtein =
    macros && macros.length > 0
      ? Math.round(macros.reduce((s, d) => s + d.protein, 0) / macros.length)
      : 0;

  const daysWithHydrationGoal = (hydration ?? []).filter(
    (d) => d.total_ml >= goalMl
  ).length;

  const latestWeight = weightData?.[weightData.length - 1]?.weight_kg;
  const firstWeight = weightData?.[0]?.weight_kg;
  const weightTrend =
    latestWeight !== undefined && firstWeight !== undefined
      ? latestWeight - firstWeight
      : null;

  // ── Insight: best weekday ─────────────────────────────────────────────────
  const bestWeekday = (() => {
    if (!macros || macros.length === 0) return null;
    const byDay: Record<number, { total: number; count: number }> = {};
    macros.forEach((d) => {
      const dayIdx = new Date(d.date + "T12:00").getDay();
      if (!byDay[dayIdx]) byDay[dayIdx] = { total: 0, count: 0 };
      if (calorieGoal && d.calories <= calorieGoal) {
        byDay[dayIdx].total += 1;
      }
      byDay[dayIdx].count += 1;
    });
    let bestDay = -1;
    let bestRatio = -1;
    Object.entries(byDay).forEach(([day, val]) => {
      if (val.count === 0) return;
      const ratio = val.total / val.count;
      if (ratio > bestRatio) {
        bestRatio = ratio;
        bestDay = Number(day);
      }
    });
    return bestDay >= 0 ? { dayName: WEEKDAY_NAMES[bestDay], ratio: bestRatio } : null;
  })();

  // ── Insight: avg mood ─────────────────────────────────────────────────────
  const moodSlice = (logs ?? []).slice(0, period);
  const avgMood =
    moodSlice.length > 0
      ? (
          moodSlice.reduce((s, l) => s + l.mood_level, 0) / moodSlice.length
        ).toFixed(1)
      : null;

  // ── Insight: hydration streak ─────────────────────────────────────────────
  const hydrationStreak = (() => {
    if (!hydration) return 0;
    let count = 0;
    for (let i = hydration.length - 1; i >= 0; i--) {
      if (hydration[i].total_ml >= goalMl) count++;
      else break;
    }
    return count;
  })();

  // ── Insight: days within calorie goal ─────────────────────────────────────
  const daysWithinCalorieGoal =
    calorieGoal && macros
      ? macros.filter((d) => d.calories > 0 && d.calories <= calorieGoal).length
      : null;

  // ── Mood chart data ───────────────────────────────────────────────────────
  const moodChartData = (logs ?? [])
    .slice()
    .reverse()
    .slice(-period)
    .map((l) => ({
      date: new Date(l.date + "T12:00").toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
      }),
      energia: l.energy_level,
      humor: l.mood_level,
    }));

  // ── Hydration chart data ──────────────────────────────────────────────────
  const hydrationChartData = (hydration ?? []).map((day) => ({
    date: new Date(day.date + "T12:00").toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
    }),
    ml: day.total_ml,
    isGoal: day.total_ml >= goalMl,
  }));

  // ── Weight chart data ─────────────────────────────────────────────────────
  const weightChartData = (weightData ?? []).map((d: WeightChartPoint) => ({
    ...d,
    date: new Date(d.date + "T12:00").toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
    }),
  }));

  return (
    <div className="space-y-5">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <BarChart2 className="h-6 w-6 text-primary" />
          Relatórios
        </h1>
        <p className="text-muted-foreground text-sm">
          Visão geral do seu progresso no período
        </p>
      </div>

      {/* Period selector */}
      <div className="flex gap-1">
        {([7, 14, 30] as const).map((d) => (
          <Button
            key={d}
            size="sm"
            variant={period === d ? "default" : "outline"}
            className="h-9 px-3 text-xs"
            onClick={() => setPeriod(d)}
          >
            {d}d
          </Button>
        ))}
      </div>

      {/* Empty state quando não há dados no período */}
      {avgCalories === 0 && avgProtein === 0 && !weightTrend && (
        <div className="rounded-xl border border-dashed border-muted-foreground/30 bg-muted/20 px-5 py-6 flex flex-col items-center gap-3 text-center">
          <span className="flex items-center justify-center w-10 h-10 rounded-full bg-primary/10">
            <UtensilsCrossed className="h-5 w-5 text-primary" />
          </span>
          <div>
            <p className="font-semibold text-sm">Sem dados no período selecionado</p>
            <p className="text-xs text-muted-foreground mt-1">
              Registre refeições, peso e hidratação para ver seu progresso aqui.
            </p>
          </div>
        </div>
      )}

      {/* Summary stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">

        {/* Média calórica */}
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-orange-500/40">
          <CardHeader className="pb-1">
            <CardTitle className="text-xs text-muted-foreground font-medium flex items-center gap-1.5">
              <span className="flex items-center justify-center w-5 h-5 rounded-md bg-orange-500/10">
                <Flame className="h-3 w-3 text-orange-500" />
              </span>
              Média calórica
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-orange-500">
              {avgCalories > 0 ? avgCalories.toLocaleString("pt-BR") : "—"}
            </p>
            <p className="text-xs text-muted-foreground mt-1">kcal / dia</p>
          </CardContent>
        </Card>

        {/* Média proteína */}
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-green-500/40">
          <CardHeader className="pb-1">
            <CardTitle className="text-xs text-muted-foreground font-medium flex items-center gap-1.5">
              <span className="flex items-center justify-center w-5 h-5 rounded-md bg-green-500/10">
                <Dumbbell className="h-3 w-3 text-green-500" />
              </span>
              Média proteína
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-green-500">
              {avgProtein > 0 ? avgProtein : "—"}
              {avgProtein > 0 && (
                <span className="text-base font-normal text-muted-foreground ml-1">
                  g
                </span>
              )}
            </p>
            <p className="text-xs text-muted-foreground mt-1">por dia</p>
          </CardContent>
        </Card>

        {/* Dias com meta hídrica */}
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-blue-500/40">
          <CardHeader className="pb-1">
            <CardTitle className="text-xs text-muted-foreground font-medium flex items-center gap-1.5">
              <span className="flex items-center justify-center w-5 h-5 rounded-md bg-blue-500/10">
                <Droplets className="h-3 w-3 text-blue-500" />
              </span>
              Meta hídrica
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-blue-500">
              {daysWithHydrationGoal}
              <span className="text-base font-normal text-muted-foreground ml-1">
                / {period}
              </span>
            </p>
            <p className="text-xs text-muted-foreground mt-1">dias atingidos</p>
          </CardContent>
        </Card>

        {/* Tendência de peso */}
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-primary/40">
          <CardHeader className="pb-1">
            <CardTitle className="text-xs text-muted-foreground font-medium flex items-center gap-1.5">
              <span className="flex items-center justify-center w-5 h-5 rounded-md bg-primary/10">
                {weightTrend === null ? (
                  <Minus className="h-3 w-3 text-primary" />
                ) : weightTrend > 0 ? (
                  <TrendingUp className="h-3 w-3 text-primary" />
                ) : weightTrend < 0 ? (
                  <TrendingDown className="h-3 w-3 text-primary" />
                ) : (
                  <Minus className="h-3 w-3 text-primary" />
                )}
              </span>
              Tendência peso
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p
              className={`text-3xl font-bold ${
                weightTrend === null
                  ? "text-muted-foreground"
                  : weightTrend > 0
                  ? "text-orange-500"
                  : weightTrend < 0
                  ? "text-green-500"
                  : "text-primary"
              }`}
            >
              {weightTrend === null
                ? "—"
                : `${weightTrend > 0 ? "+" : ""}${weightTrend.toFixed(1)}`}
              {weightTrend !== null && (
                <span className="text-base font-normal text-muted-foreground ml-1">
                  kg
                </span>
              )}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              nos últimos {period} dias
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Insight cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">

        {/* Best weekday */}
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-orange-500/30 rounded-xl border">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-muted-foreground font-medium flex items-center gap-1.5">
              <span className="flex items-center justify-center w-5 h-5 rounded-md bg-orange-500/10">
                <Trophy className="h-3 w-3 text-orange-500" />
              </span>
              Melhor dia da semana
            </CardTitle>
          </CardHeader>
          <CardContent>
            {bestWeekday && calorieGoal ? (
              <>
                <p className="text-base font-semibold">
                  {bestWeekday.dayName} são suas melhores
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {Math.round(bestWeekday.ratio * 100)}% das vezes dentro da meta calórica
                </p>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">
                {calorieGoal
                  ? "Dados insuficientes para o período"
                  : "Defina uma meta calórica no perfil"}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Avg mood/energy */}
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-yellow-400/30 rounded-xl border">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-muted-foreground font-medium flex items-center gap-1.5">
              <span className="flex items-center justify-center w-5 h-5 rounded-md bg-yellow-400/10">
                <Smile className="h-3 w-3 text-yellow-400" />
              </span>
              Bem-estar médio
            </CardTitle>
          </CardHeader>
          <CardContent>
            {avgMood !== null ? (
              <>
                <p className="text-base font-semibold flex items-center gap-2">
                  <span className="text-yellow-400 flex items-center gap-1">
                    <Smile className="h-4 w-4" />
                    {avgMood}
                    <span className="text-xs text-muted-foreground font-normal">/ 5</span>
                  </span>
                  <span className="text-muted-foreground text-xs font-normal">humor</span>
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  baseado em {moodSlice.length} registro{moodSlice.length !== 1 ? "s" : ""} no período
                </p>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">
                Nenhum registro de humor no período
              </p>
            )}
          </CardContent>
        </Card>

        {/* Hydration streak */}
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-blue-500/30 rounded-xl border">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-muted-foreground font-medium flex items-center gap-1.5">
              <span className="flex items-center justify-center w-5 h-5 rounded-md bg-blue-500/10">
                <Zap className="h-3 w-3 text-blue-500" />
              </span>
              Sequência hídrica
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-base font-semibold">
              <span className="text-blue-500 text-2xl font-bold">{hydrationStreak}</span>
              <span className="text-muted-foreground text-sm font-normal ml-1">
                dia{hydrationStreak !== 1 ? "s" : ""} consecutivo{hydrationStreak !== 1 ? "s" : ""}
              </span>
            </p>
            {hydrationStreak >= 3 ? (
              <p className="text-xs text-blue-400 mt-1 flex items-center gap-1">
                <Trophy className="h-3 w-3" />
                {hydrationStreak >= 7 ? "Incrível! Hidratação em dia!" : "Boa sequência!"}
              </p>
            ) : (
              <p className="text-xs text-muted-foreground mt-1">
                Beba {(goalMl / 1000).toFixed(1)}L por dia para manter a sequência
              </p>
            )}
          </CardContent>
        </Card>

        {/* Days within calorie goal */}
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-green-500/30 rounded-xl border">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-muted-foreground font-medium flex items-center gap-1.5">
              <span className="flex items-center justify-center w-5 h-5 rounded-md bg-green-500/10">
                <Target className="h-3 w-3 text-green-500" />
              </span>
              Dias dentro da meta
            </CardTitle>
          </CardHeader>
          <CardContent>
            {daysWithinCalorieGoal !== null ? (
              <>
                <p className="text-base font-semibold">
                  <span className="text-green-500 text-2xl font-bold">{daysWithinCalorieGoal}</span>
                  <span className="text-muted-foreground text-sm font-normal ml-1">
                    / {macros?.filter((d) => d.calories > 0).length ?? 0} dias com refeições
                  </span>
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  meta: {calorieGoal?.toLocaleString("pt-BR")} kcal/dia
                </p>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">
                Defina uma meta calórica no perfil
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Macro chart — CaloriesBarChart já inclui seu próprio Card */}
      {macroChartData.length > 0 ? (
        <CaloriesBarChart data={macroChartData} calorieGoal={calorieGoal} />
      ) : (
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-orange-500/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-1.5">
              <Flame className="h-4 w-4 text-orange-500" />
              Calorias diárias
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[240px] flex items-center justify-center text-muted-foreground text-sm">
              Sem dados de refeições no período
            </div>
          </CardContent>
        </Card>
      )}

      {/* Weight chart */}
      {weightChartData.length > 1 && (
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-primary/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-1.5">
              <TrendingUp className="h-4 w-4 text-primary" />
              Evolução do peso
            </CardTitle>
          </CardHeader>
          <CardContent>
            <WeightAreaChart data={weightChartData} />
          </CardContent>
        </Card>
      )}

      {/* Hydration chart */}
      {hydrationChartData.length > 0 && (
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-blue-500/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-1.5">
              <Droplets className="h-4 w-4 text-blue-500" />
              Hidratação diária
            </CardTitle>
          </CardHeader>
          <CardContent>
            <HydrationBarChart data={hydrationChartData} />
            <div className="flex items-center justify-center gap-4 mt-1">
              <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <span className="h-2.5 w-2.5 rounded-full bg-green-500 inline-block" />
                Meta atingida
              </span>
              <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <span className="h-2.5 w-2.5 rounded-full bg-blue-500 inline-block" />
                Abaixo da meta
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Mood chart */}
      {moodChartData.length > 1 && (
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-yellow-400/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-1.5">
              <Smile className="h-4 w-4 text-yellow-400" />
              Evolução do humor & energia
            </CardTitle>
          </CardHeader>
          <CardContent>
            <MoodLineChart data={moodChartData} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
