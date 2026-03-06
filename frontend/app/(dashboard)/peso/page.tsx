"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Scale, TrendingDown, TrendingUp, Minus, Target } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

const WeightAreaChart = dynamic(
  () => import("@/components/charts/WeightAreaChart").then((m) => m.WeightAreaChart),
  { ssr: false, loading: () => <Skeleton className="h-[260px] w-full" /> }
);
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { useWeightLogs, useLogWeight } from "@/lib/hooks/useLogs";
import { useWeightChart } from "@/lib/hooks/useDashboard";
import { useMe } from "@/lib/hooks/useProfile";

function getLocalToday(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}


export default function PesoPage() {
  const [weight, setWeight] = useState("");
  const { data: logs } = useWeightLogs();
  const { data: chartData } = useWeightChart(90);
  const { data: user } = useMe();
  const logWeight = useLogWeight();

  const today = getLocalToday();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const kg = parseFloat(weight.replace(",", "."));
    if (isNaN(kg) || kg <= 0) return;
    await logWeight.mutateAsync({ weight_kg: kg, date: today });
    setWeight("");
  }

  const formatted = (chartData ?? []).map((d) => ({
    ...d,
    date: new Date(d.date).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }),
  }));

  const latest = logs?.[0];
  const prev = logs?.[1];
  const delta = latest && prev ? latest.weight_kg - prev.weight_kg : null;

  const goalPct = (() => {
    if (!latest || !user?.weight_goal || !logs?.length) return null;
    const start = logs[logs.length - 1]?.weight_kg ?? latest.weight_kg;
    const goal = user.weight_goal;
    if (start === goal) return 100;
    const pct = ((start - latest.weight_kg) / (start - goal)) * 100;
    return Math.min(Math.max(pct, 0), 100);
  })();

  return (
    <div className="space-y-5">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Scale className="h-6 w-6 text-primary" />
          Peso
        </h1>
        <p className="text-muted-foreground text-sm">Acompanhe sua evolução</p>
      </div>

      {/* Stat cards */}
      {latest && (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {/* Peso atual */}
          <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-orange-500/40">
            <CardHeader className="pb-1">
              <CardTitle className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
                <span className="flex items-center justify-center w-5 h-5 rounded-md bg-orange-500/10">
                  <Scale className="h-3 w-3 text-orange-500" />
                </span>
                Peso atual
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-orange-500">
                {latest.weight_kg}
                <span className="text-sm font-normal text-muted-foreground ml-1">kg</span>
              </p>
              {delta !== null && (
                <p className={`text-xs mt-1.5 flex items-center gap-1 font-medium ${delta < 0 ? "text-green-500" : delta > 0 ? "text-orange-400" : "text-muted-foreground"}`}>
                  {delta < 0 ? <TrendingDown className="h-3 w-3" /> : delta > 0 ? <TrendingUp className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
                  {delta > 0 ? "+" : ""}{delta.toFixed(1)} kg
                </p>
              )}
            </CardContent>
          </Card>

          {/* Meta */}
          {user?.weight_goal && (
            <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-green-500/40">
              <CardHeader className="pb-1">
                <CardTitle className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
                  <span className="flex items-center justify-center w-5 h-5 rounded-md bg-green-500/10">
                    <Target className="h-3 w-3 text-green-500" />
                  </span>
                  Meta
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold text-green-500">
                  {user.weight_goal}
                  <span className="text-sm font-normal text-muted-foreground ml-1">kg</span>
                </p>
                <p className={`text-xs mt-1.5 font-medium ${latest.weight_kg <= user.weight_goal ? "text-green-500" : "text-orange-400"}`}>
                  {latest.weight_kg <= user.weight_goal
                    ? "Meta atingida!"
                    : `Faltam ${(latest.weight_kg - user.weight_goal).toFixed(1)} kg`}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Progresso para meta */}
          {user?.weight_goal && goalPct !== null && (
            <Card className="col-span-2 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-green-500/30">
              <CardHeader className="pb-1">
                <CardTitle className="text-xs text-muted-foreground uppercase tracking-wide">
                  Progresso para a meta
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between items-end">
                  <span className="text-2xl font-bold text-green-500">{goalPct.toFixed(0)}%</span>
                  <span className="text-xs text-muted-foreground">
                    {logs?.[logs.length - 1]?.weight_kg} → {user.weight_goal} kg
                  </span>
                </div>
                <Progress
                  value={goalPct}
                  indicatorColor="linear-gradient(90deg, #86efac 0%, #22c55e 100%)"
                />
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Gráfico — largura total */}
      {formatted.length > 1 && (
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-primary/30">
          <CardHeader>
            <CardTitle className="text-sm">Evolução — últimos 90 dias</CardTitle>
          </CardHeader>
          <CardContent>
            <WeightAreaChart data={formatted} weightGoal={user?.weight_goal ?? undefined} />
          </CardContent>
        </Card>
      )}

      {/* Linha inferior: Registrar + Histórico lado a lado */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

        {/* Registrar */}
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-primary/30">
          <CardHeader>
            <CardTitle className="text-sm">Registrar peso</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <form onSubmit={handleSubmit} className="flex gap-3">
              <div className="flex-1">
                <Label className="sr-only" htmlFor="weight">Peso (kg)</Label>
                <Input
                  id="weight"
                  placeholder="Ex: 80.5"
                  value={weight}
                  onChange={(e) => setWeight(e.target.value)}
                />
              </div>
              <Button type="submit" disabled={logWeight.isPending}>
                {logWeight.isPending ? "..." : "Salvar"}
              </Button>
            </form>
            {latest && (
              <div className="grid grid-cols-6 gap-1.5">
                {[-1, -0.5, -0.1, +0.1, +0.5, +1].map((v) => {
                  const val = parseFloat((latest.weight_kg + v).toFixed(1));
                  return (
                    <button
                      key={v}
                      type="button"
                      onClick={() => setWeight(String(val))}
                      className={`py-1.5 rounded-lg text-xs font-medium border transition-colors cursor-pointer
                        ${v < 0
                          ? "border-green-500/30 text-green-500 hover:bg-green-500/10"
                          : "border-orange-500/30 text-orange-400 hover:bg-orange-500/10"
                        }`}
                    >
                      {v > 0 ? `+${v}` : v}
                    </button>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Histórico */}
        {logs && logs.length > 0 && (
          <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-primary/30">
            <CardHeader>
              <CardTitle className="text-sm">Histórico</CardTitle>
            </CardHeader>
            <CardContent className="divide-y text-sm p-0">
              {logs.slice(0, 8).map((l, idx) => {
                const next = logs[idx + 1];
                const d = next ? l.weight_kg - next.weight_kg : null;
                return (
                  <div key={l.id} className="flex justify-between items-center py-2.5 px-6 hover:bg-muted/30 transition-colors">
                    <span className="text-muted-foreground text-xs">
                      {new Date(l.date).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" })}
                    </span>
                    <div className="flex items-center gap-3">
                      {d !== null && (
                        <span className={`text-xs flex items-center gap-0.5 font-medium ${d < 0 ? "text-green-500" : d > 0 ? "text-orange-400" : "text-muted-foreground"}`}>
                          {d < 0 ? <TrendingDown className="h-3 w-3" /> : d > 0 ? <TrendingUp className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
                          {d > 0 ? "+" : ""}{d.toFixed(1)}
                        </span>
                      )}
                      <span className="font-semibold">{l.weight_kg} kg</span>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        )}

      </div>
    </div>
  );
}
