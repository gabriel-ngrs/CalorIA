"use client";

import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CheckCircle2, Droplets, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { useHydrationHistory, useHydrationToday, useLogHydration } from "@/lib/hooks/useLogs";
import { useMe } from "@/lib/hooks/useProfile";

const QUICK_OPTIONS = [200, 300, 500];
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

  const chartData = (history ?? []).map((day) => ({
    date: new Date(day.date + "T12:00").toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }),
    ml: day.total_ml,
    meta: goalMl,
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
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Droplets className="h-6 w-6 text-blue-500" />
          Hidratação
        </h1>
        <p className="text-muted-foreground text-sm">Controle seu consumo de água</p>
      </div>

      {/* Progresso do dia */}
      <Card>
        <CardContent className="pt-6">
          <div className="text-center mb-4">
            <p className="text-4xl font-bold text-blue-500">
              {total} <span className="text-xl font-normal text-muted-foreground">ml</span>
            </p>
            <p className="text-sm text-muted-foreground mt-1">de {goalMl} ml hoje</p>
          </div>
          <Progress value={pct} className="h-3" indicatorColor="linear-gradient(90deg, #bfdbfe 0%, #3b82f6 100%)" />
          <div className="flex justify-between items-center mt-2">
            <p className="text-xs text-muted-foreground">0 ml</p>
            <p className="text-sm font-medium">{pct.toFixed(0)}%</p>
            <p className="text-xs text-muted-foreground">{goalMl} ml</p>
          </div>
          {pct >= 100 && (
            <p className="text-center text-green-500 font-medium flex items-center justify-center gap-1.5 mt-3 text-sm">
              <CheckCircle2 className="h-4 w-4" />
              Meta diária atingida!
            </p>
          )}
        </CardContent>
      </Card>

      {/* Adicionar */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Adicionar água</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-3 gap-2">
            {QUICK_OPTIONS.map((ml) => (
              <button
                key={ml}
                type="button"
                disabled={logHydration.isPending}
                onClick={() => log(ml)}
                className="flex flex-col items-center gap-1 py-3 px-2 rounded-xl border border-border bg-blue-500/5 hover:bg-blue-500/15 hover:border-blue-500/40 transition-colors cursor-pointer disabled:opacity-50"
              >
                <Droplets className="h-5 w-5 text-blue-500" />
                <span className="text-sm font-semibold">+{ml} ml</span>
                <span className="text-xs text-muted-foreground">
                  {ml === 200 ? "Copo" : ml === 300 ? "Garrafa P" : "Garrafa M"}
                </span>
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
              className="gap-1.5"
            >
              <Plus className="h-3.5 w-3.5" />
              Adicionar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Métricas do período */}
      {history && history.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-blue-500">{avgMl}</p>
              <p className="text-xs text-muted-foreground mt-1">Média diária (ml)</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-green-500">{daysWithGoal}/{historyDays}</p>
              <p className="text-xs text-muted-foreground mt-1">Dias com meta</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-orange-500">{streak}</p>
              <p className="text-xs text-muted-foreground mt-1">Sequência atual</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Gráfico de histórico */}
      {chartData.length > 0 && (
        <Card>
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
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip
                  formatter={(value: number) => [`${value} ml`, "Ingestão"]}
                  labelStyle={{ fontSize: 12 }}
                />
                <Bar dataKey="ml" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, i) => (
                    <Cell
                      key={i}
                      fill={entry.ml >= goalMl ? "#22c55e" : "#3b82f6"}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <p className="text-xs text-muted-foreground text-center mt-1">
              Verde = meta atingida · Azul = abaixo da meta
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
