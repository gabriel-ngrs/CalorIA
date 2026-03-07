"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { CheckCircle2, Droplets, Flame, Plus, Trophy, Zap } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

const HydrationBarChart = dynamic(
  () => import("@/components/charts/HydrationBarChart").then((m) => m.HydrationBarChart),
  { ssr: false, loading: () => <Skeleton className="h-[240px] w-full" /> }
);
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { useHydrationHistory, useHydrationToday, useLogHydration } from "@/lib/hooks/useLogs";
import { useMe } from "@/lib/hooks/useProfile";

const QUICK_OPTIONS = [
  { ml: 200, label: "Copo" },
  { ml: 300, label: "Garrafa P" },
  { ml: 500, label: "Garrafa M" },
  { ml: 750, label: "Garrafa G" },
];
const DEFAULT_GOAL_ML = 2000;

function getLocalToday(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}


export default function HidratacaoPage() {
  const [custom, setCustom] = useState("");
  const [historyDays, setHistoryDays] = useState(7);
  const { data: user } = useMe();
  const { data: summary } = useHydrationToday();
  const { data: history } = useHydrationHistory(historyDays);
  const logHydration = useLogHydration();

  const goalMl = user?.water_goal_ml ?? DEFAULT_GOAL_ML;
  const today = getLocalToday();
  const now = new Date();
  const timeStr = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;

  async function log(ml: number) {
    if (!Number.isFinite(ml) || ml <= 0) return;
    await logHydration.mutateAsync({ amount_ml: ml, date: today, time: timeStr });
    setCustom("");
  }

  const total = summary?.total_ml ?? 0;
  const pct = Math.min((total / goalMl) * 100, 100);
  const remaining = Math.max(goalMl - total, 0);

  const chartData = (history ?? []).map((day) => ({
    date: new Date(day.date + "T12:00").toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }),
    ml: day.total_ml,
    isGoal: day.total_ml >= goalMl,
  }));

  const daysWithGoal = (history ?? []).filter((d) => d.total_ml >= goalMl).length;
  const avgMl = history && history.length > 0
    ? Math.round(history.reduce((s, d) => s + d.total_ml, 0) / history.length)
    : 0;
  const streak = (() => {
    if (!history) return 0;
    let count = 0;
    for (let i = history.length - 1; i >= 0; i--) {
      if (history[i].total_ml >= goalMl) count++;
      else break;
    }
    return count;
  })();

  return (
    <div className="space-y-5">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Droplets className="h-6 w-6 text-blue-500" />
          Hidratação
        </h1>
        <p className="text-muted-foreground text-sm">Controle seu consumo de água</p>
      </div>

      {/* Layout principal: 2 colunas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Coluna esquerda — progresso + ações (2/3) */}
        <div className="lg:col-span-2 space-y-4">

          {/* Progresso do dia */}
          <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-blue-500/40">
            <CardContent className="pt-6 space-y-4">
              {/* Número principal */}
              <div className="flex items-end justify-between">
                <div>
                  <p className="text-5xl font-bold text-blue-500 leading-none">
                    {total.toLocaleString("pt-BR")}
                    <span className="text-xl font-normal text-muted-foreground ml-2">ml</span>
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {pct >= 100
                      ? "Meta diária atingida!"
                      : `Faltam ${remaining.toLocaleString("pt-BR")} ml para a meta`}
                  </p>
                </div>
                {pct >= 100 && (
                  <CheckCircle2 className="h-10 w-10 text-green-500 shrink-0" />
                )}
              </div>

              {/* Barra com marcadores de milestone */}
              <div className="space-y-1.5">
                <Progress
                  value={pct}
                  className="h-4"
                  indicatorColor="linear-gradient(90deg, #bfdbfe 0%, #3b82f6 100%)"
                />
                <div className="flex justify-between text-xs text-muted-foreground px-0.5">
                  <span>0</span>
                  <span className={pct >= 25 ? "text-blue-400" : ""}>{(goalMl * 0.25 / 1000).toFixed(goalMl * 0.25 % 1000 === 0 ? 0 : 1)}L</span>
                  <span className={pct >= 50 ? "text-blue-400" : ""}>{(goalMl * 0.5 / 1000).toFixed(goalMl * 0.5 % 1000 === 0 ? 0 : 1)}L</span>
                  <span className={pct >= 75 ? "text-blue-400" : ""}>{(goalMl * 0.75 / 1000).toFixed(goalMl * 0.75 % 1000 === 0 ? 0 : 1)}L</span>
                  <span className={pct >= 100 ? "text-green-500 font-medium" : ""}>{goalMl / 1000}L</span>
                </div>
                <p className="text-right text-xs font-medium text-blue-400">{pct.toFixed(0)}%</p>
              </div>
            </CardContent>
          </Card>

          {/* Adicionar água */}
          <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-blue-500/30">
            <CardHeader>
              <CardTitle className="text-sm">Adicionar água</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {QUICK_OPTIONS.map(({ ml, label }) => (
                  <button
                    key={ml}
                    type="button"
                    disabled={logHydration.isPending}
                    onClick={() => log(ml)}
                    className="flex flex-col items-center gap-1.5 py-4 px-2 rounded-xl border border-blue-500/20 bg-blue-500/5 hover:bg-blue-500/15 hover:border-blue-500/50 transition-colors cursor-pointer disabled:opacity-50"
                  >
                    <Droplets className="h-5 w-5 text-blue-500" />
                    <span className="text-sm font-bold text-blue-400">+{ml}</span>
                    <span className="text-xs text-muted-foreground">{label}</span>
                  </button>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  placeholder="Outro valor (ml)"
                  type="number"
                  min="1"
                  value={custom}
                  onChange={(e) => setCustom(e.target.value)}
                  className="flex-1"
                />
                <Button
                  onClick={() => log(parseInt(custom, 10))}
                  disabled={!custom || logHydration.isPending}
                  className="gap-1.5 shrink-0"
                >
                  <Plus className="h-3.5 w-3.5" />
                  Adicionar
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Coluna direita — stats (1/3) */}
        <div className="space-y-4">
          <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-blue-500/40">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
                <span className="flex items-center justify-center w-5 h-5 rounded-md bg-blue-500/10">
                  <Droplets className="h-3 w-3 text-blue-500" />
                </span>
                Média diária
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-blue-500">
                {avgMl > 0 ? avgMl.toLocaleString("pt-BR") : "—"}
                <span className="text-sm font-normal text-muted-foreground ml-1">ml</span>
              </p>
              <p className="text-xs text-muted-foreground mt-1">últimos {historyDays} dias</p>
            </CardContent>
          </Card>

          <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-green-500/40">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
                <span className="flex items-center justify-center w-5 h-5 rounded-md bg-green-500/10">
                  <Zap className="h-3 w-3 text-green-500" />
                </span>
                Dias com meta
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-green-500">
                {daysWithGoal}
                <span className="text-base font-normal text-muted-foreground ml-1">/ {historyDays}</span>
              </p>
              <Progress
                value={historyDays > 0 ? (daysWithGoal / historyDays) * 100 : 0}
                className="mt-2"
                indicatorColor="linear-gradient(90deg, #86efac 0%, #22c55e 100%)"
              />
            </CardContent>
          </Card>

          <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-orange-500/40">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
                <span className="flex items-center justify-center w-5 h-5 rounded-md bg-orange-500/10">
                  <Flame className="h-3 w-3 text-orange-500" />
                </span>
                Sequência atual
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-orange-500">
                {streak}
                <span className="text-sm font-normal text-muted-foreground ml-1">dias</span>
              </p>
              {streak >= 3 && (
                <p className="text-xs text-orange-400 mt-1 flex items-center gap-1">
                  <Trophy className="h-3 w-3" />
                  {streak >= 7 ? "Incrível! Continue assim!" : "Ótima sequência!"}
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Gráfico — largura total */}
      {chartData.length > 0 && (
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-blue-500/30">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">Histórico</CardTitle>
            <div className="flex gap-1">
              {[7, 14, 30].map((d) => (
                <Button
                  key={d}
                  size="sm"
                  variant={historyDays === d ? "default" : "outline"}
                  className="h-6 px-2 text-xs"
                  onClick={() => setHistoryDays(d)}
                >
                  {d}d
                </Button>
              ))}
            </div>
          </CardHeader>
          <CardContent>
            <HydrationBarChart data={chartData} />
            <div className="flex items-center justify-center gap-4 mt-1">
              <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <span className="h-2.5 w-2.5 rounded-full bg-green-500 inline-block" /> Meta atingida
              </span>
              <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <span className="h-2.5 w-2.5 rounded-full bg-blue-500 inline-block" /> Abaixo da meta
              </span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
