"use client";

import { useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TooltipProps } from "recharts";
import { Scale, TrendingDown, TrendingUp, Minus, Target } from "lucide-react";
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

function WeightTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  const value = payload[0].value as number;
  return (
    <div
      style={{
        background: "rgba(15, 28, 38, 0.88)",
        backdropFilter: "blur(14px)",
        WebkitBackdropFilter: "blur(14px)",
        border: "1px solid rgba(145, 183, 199, 0.16)",
        borderRadius: "10px",
        padding: "10px 14px",
        boxShadow: "0 8px 32px rgba(0,0,0,0.45)",
        minWidth: "120px",
      }}
    >
      <p style={{ margin: "0 0 4px", fontSize: "11px", color: "#94a3b8", fontWeight: 500 }}>{label}</p>
      <p style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "#f97316", lineHeight: 1.2 }}>
        {value.toFixed(1)}
        <span style={{ fontSize: "12px", fontWeight: 400, color: "#64748b", marginLeft: "4px" }}>kg</span>
      </p>
    </div>
  );
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

  // progresso para meta (quanto % do caminho já percorreu)
  const goalPct = (() => {
    if (!latest || !user?.weight_goal || !logs?.length) return null;
    const start = logs[logs.length - 1]?.weight_kg ?? latest.weight_kg;
    const goal = user.weight_goal;
    if (start === goal) return 100;
    const pct = ((start - latest.weight_kg) / (start - goal)) * 100;
    return Math.min(Math.max(pct, 0), 100);
  })();

  return (
    <div className="space-y-5 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Scale className="h-6 w-6 text-primary" />
          Peso
        </h1>
        <p className="text-muted-foreground text-sm">Acompanhe sua evolução</p>
      </div>

      {/* Stat cards */}
      {latest && (
        <div className="flex gap-4">
          <Card className="flex-1 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-orange-500/40">
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
                <span className="text-base font-normal text-muted-foreground ml-1">kg</span>
              </p>
              {delta !== null && (
                <p className={`text-xs mt-1.5 flex items-center gap-1 font-medium ${delta < 0 ? "text-green-500" : delta > 0 ? "text-orange-400" : "text-muted-foreground"}`}>
                  {delta < 0 ? <TrendingDown className="h-3 w-3" /> : delta > 0 ? <TrendingUp className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
                  {delta > 0 ? "+" : ""}{delta.toFixed(1)} kg desde o último registro
                </p>
              )}
            </CardContent>
          </Card>

          {user?.weight_goal && (
            <Card className="flex-1 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-green-500/40">
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
                  <span className="text-base font-normal text-muted-foreground ml-1">kg</span>
                </p>
                <p className={`text-xs mt-1.5 font-medium ${latest.weight_kg <= user.weight_goal ? "text-green-500" : "text-orange-400"}`}>
                  {latest.weight_kg <= user.weight_goal
                    ? "Meta atingida!"
                    : `Faltam ${(latest.weight_kg - user.weight_goal).toFixed(1)} kg`}
                </p>
                {goalPct !== null && (
                  <div className="mt-2 space-y-1">
                    <Progress
                      value={goalPct}
                      indicatorColor="linear-gradient(90deg, #86efac 0%, #22c55e 100%)"
                    />
                    <p className="text-xs text-muted-foreground">{goalPct.toFixed(0)}% do caminho</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Gráfico de área */}
      {formatted.length > 1 && (
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-primary/30">
          <CardHeader>
            <CardTitle className="text-sm">Evolução — últimos 90 dias</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={formatted} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="weightGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(145,183,199,0.08)" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 10 }} domain={["dataMin - 1", "dataMax + 1"]} />
                <Tooltip content={<WeightTooltip />} cursor={{ stroke: "rgba(249,115,22,0.3)", strokeWidth: 1 }} />
                <Area
                  type="monotone"
                  dataKey="weight_kg"
                  stroke="#f97316"
                  strokeWidth={2.5}
                  fill="url(#weightGrad)"
                  dot={false}
                  activeDot={{ r: 5, fill: "#f97316", strokeWidth: 0 }}
                />
                {user?.weight_goal && (
                  <ReferenceLine
                    y={user.weight_goal}
                    stroke="#22c55e"
                    strokeDasharray="4 4"
                    strokeWidth={1.5}
                    label={{ value: `Meta ${user.weight_goal}kg`, fontSize: 10, fill: "#22c55e", position: "insideTopRight" }}
                  />
                )}
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

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
          {/* Atalhos baseados no peso atual */}
          {latest && (
            <div className="flex gap-2">
              {[-1, -0.5, -0.1, +0.1, +0.5, +1].map((v) => {
                const val = parseFloat((latest.weight_kg + v).toFixed(1));
                return (
                  <button
                    key={v}
                    type="button"
                    onClick={() => setWeight(String(val))}
                    className={`flex-1 py-1 rounded-lg text-xs font-medium border transition-colors cursor-pointer
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
            {logs.slice(0, 10).map((l, idx) => {
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
  );
}
