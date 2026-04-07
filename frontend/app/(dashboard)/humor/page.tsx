"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Star, Smile, Zap, CalendarDays, NotebookPen } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

const MoodLineChart = dynamic(
  () => import("@/components/charts/MoodLineChart").then((m) => m.MoodLineChart),
  { ssr: false, loading: () => <Skeleton className="h-[240px] w-full" /> }
);
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { useMoodLogs, useLogMood } from "@/lib/hooks/useLogs";

const LEVELS = [
  { value: 1, label: "Muito baixo" },
  { value: 2, label: "Baixo"       },
  { value: 3, label: "Médio"       },
  { value: 4, label: "Alto"        },
  { value: 5, label: "Muito alto"  },
];

const ENERGY_COLORS: Record<number, string> = {
  1: "border-red-500/50 bg-red-500/10 text-red-400 hover:bg-red-500/20",
  2: "border-orange-500/50 bg-orange-500/10 text-orange-400 hover:bg-orange-500/20",
  3: "border-yellow-500/50 bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500/20",
  4: "border-blue-500/50 bg-blue-500/10 text-blue-400 hover:bg-blue-500/20",
  5: "border-green-500/50 bg-green-500/10 text-green-400 hover:bg-green-500/20",
};

const ENERGY_SELECTED: Record<number, string> = {
  1: "border-red-500 bg-red-500/25 text-red-300 ring-1 ring-red-500/50",
  2: "border-orange-500 bg-orange-500/25 text-orange-300 ring-1 ring-orange-500/50",
  3: "border-yellow-500 bg-yellow-500/25 text-yellow-300 ring-1 ring-yellow-500/50",
  4: "border-blue-500 bg-blue-500/25 text-blue-300 ring-1 ring-blue-500/50",
  5: "border-green-500 bg-green-500/25 text-green-300 ring-1 ring-green-500/50",
};

function LevelSelector({
  value,
  onChange,
  colorMap,
  selectedMap,
}: {
  value: number;
  onChange: (v: number) => void;
  colorMap: Record<number, string>;
  selectedMap: Record<number, string>;
}) {
  return (
    <div className="flex gap-2">
      {LEVELS.map((l) => {
        const isSelected = value === l.value;
        return (
          <button
            key={l.value}
            type="button"
            onClick={() => onChange(l.value)}
            title={l.label}
            className={cn(
              "flex-1 flex flex-col items-center gap-0.5 py-3 rounded-xl border transition-all duration-150 cursor-pointer",
              isSelected ? selectedMap[l.value] : colorMap[l.value]
            )}
          >
            <span className="text-lg font-bold leading-none">{l.value}</span>
            <span className="text-[10px] font-medium leading-tight text-center px-0.5">{l.label}</span>
          </button>
        );
      })}
    </div>
  );
}


function getLocalToday(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export default function HumorPage() {
  const [energy, setEnergy] = useState(3);
  const [mood, setMood] = useState(3);
  const [notes, setNotes] = useState("");
  const [period, setPeriod] = useState<7 | 14 | 30>(7);
  const { data: logs } = useMoodLogs();
  const logMood = useLogMood();

  const today = getLocalToday();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await logMood.mutateAsync({
      date: today,
      energy_level: energy,
      mood_level: mood,
      notes: notes || undefined,
    });
    setNotes("");
  }

  const allLogs = logs ?? [];
  const recentLogs = allLogs.slice(0, period);

  const avgEnergy = recentLogs.length > 0
    ? recentLogs.reduce((s, l) => s + l.energy_level, 0) / recentLogs.length
    : null;
  const avgMood = recentLogs.length > 0
    ? recentLogs.reduce((s, l) => s + l.mood_level, 0) / recentLogs.length
    : null;
  const bestDay = recentLogs.length > 0
    ? recentLogs.reduce((best, l) =>
        l.mood_level + l.energy_level > best.mood_level + best.energy_level ? l : best
      )
    : null;

  const chartData = allLogs
    .slice()
    .reverse()
    .slice(-period)
    .map((l) => ({
      date: new Date(l.date + "T12:00").toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }),
      energia: l.energy_level,
      humor: l.mood_level,
    }));

  return (
    <div className="space-y-5">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-gray-900 flex items-center gap-2">
          <Smile className="h-6 w-6 text-yellow-400" />
          Humor & Energia
        </h1>
        <p className="text-gray-400 text-sm">Como você está hoje?</p>
      </div>

      {/* Layout 2 colunas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Coluna esquerda — formulário (2/3) */}
        <Card className="lg:col-span-2 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-yellow-400/30">
          <CardHeader>
            <CardTitle className="text-sm">Registrar hoje</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">

              {/* Energia */}
              <div className="space-y-2.5">
                <Label className="flex items-center gap-1.5 text-sm font-medium">
                  <span className="flex items-center justify-center w-5 h-5 rounded-md bg-orange-500/10">
                    <Zap className="h-3 w-3 text-orange-500" />
                  </span>
                  Energia
                  <span className="ml-auto text-xs text-muted-foreground">
                    {LEVELS[energy - 1].label}
                  </span>
                </Label>
                <LevelSelector
                  value={energy}
                  onChange={setEnergy}
                  colorMap={ENERGY_COLORS}
                  selectedMap={ENERGY_SELECTED}
                />
              </div>

              {/* Humor */}
              <div className="space-y-2.5">
                <Label className="flex items-center gap-1.5 text-sm font-medium">
                  <span className="flex items-center justify-center w-5 h-5 rounded-md bg-blue-500/10">
                    <Smile className="h-3 w-3 text-blue-400" />
                  </span>
                  Humor
                  <span className="ml-auto text-xs text-muted-foreground">
                    {LEVELS[mood - 1].label}
                  </span>
                </Label>
                <LevelSelector
                  value={mood}
                  onChange={setMood}
                  colorMap={ENERGY_COLORS}
                  selectedMap={ENERGY_SELECTED}
                />
              </div>

              {/* Notas */}
              <div className="space-y-1.5">
                <Label htmlFor="notes" className="flex items-center gap-1.5 text-sm">
                  <NotebookPen className="h-3.5 w-3.5 text-muted-foreground" />
                  Notas (opcional)
                </Label>
                <Input
                  id="notes"
                  placeholder="Como foi seu dia?"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </div>

              <Button type="submit" disabled={logMood.isPending} className="w-full">
                {logMood.isPending ? "Salvando..." : "Registrar"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Coluna direita — stats (1/3) */}
        <div className="space-y-4">
          {/* Média energia */}
          <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-orange-500/40">
            <CardHeader className="pb-1">
              <CardTitle className="text-xs text-muted-foreground font-medium flex items-center gap-1.5">
                <span className="flex items-center justify-center w-5 h-5 rounded-md bg-orange-500/10">
                  <Zap className="h-3 w-3 text-orange-500" />
                </span>
                Média energia
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-orange-500">
                {avgEnergy !== null ? avgEnergy.toFixed(1) : "—"}
                <span className="text-base font-normal text-muted-foreground ml-1">/ 5</span>
              </p>
              {avgEnergy !== null && (
                <p className="text-xs text-muted-foreground mt-1">{LEVELS[Math.round(avgEnergy) - 1]?.label}</p>
              )}
            </CardContent>
          </Card>

          {/* Média humor */}
          <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-blue-500/40">
            <CardHeader className="pb-1">
              <CardTitle className="text-xs text-muted-foreground font-medium flex items-center gap-1.5">
                <span className="flex items-center justify-center w-5 h-5 rounded-md bg-blue-500/10">
                  <Smile className="h-3 w-3 text-blue-400" />
                </span>
                Média humor
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-blue-400">
                {avgMood !== null ? avgMood.toFixed(1) : "—"}
                <span className="text-base font-normal text-muted-foreground ml-1">/ 5</span>
              </p>
              {avgMood !== null && (
                <p className="text-xs text-muted-foreground mt-1">{LEVELS[Math.round(avgMood) - 1]?.label}</p>
              )}
            </CardContent>
          </Card>

          {/* Melhor dia */}
          {bestDay && (
            <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-yellow-400/40">
              <CardHeader className="pb-1">
                <CardTitle className="text-xs text-muted-foreground font-medium flex items-center gap-1.5">
                  <span className="flex items-center justify-center w-5 h-5 rounded-md bg-yellow-400/10">
                    <Star className="h-3 w-3 text-yellow-400" />
                  </span>
                  Melhor dia
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm font-semibold capitalize">
                  {new Date(bestDay.date + "T12:00").toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit", month: "short" })}
                </p>
                <div className="flex gap-3 mt-1.5">
                  <span className="text-xs text-orange-400 flex items-center gap-1">
                    <Zap className="h-3 w-3" />{bestDay.energy_level}/5
                  </span>
                  <span className="text-xs text-blue-400 flex items-center gap-1">
                    <Smile className="h-3 w-3" />{bestDay.mood_level}/5
                  </span>
                </div>
                {bestDay.notes && (
                  <p className="text-xs text-muted-foreground italic mt-1.5 truncate">&ldquo;{bestDay.notes}&rdquo;</p>
                )}
              </CardContent>
            </Card>
          )}

          {/* Dias registrados */}
          <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-primary/30">
            <CardHeader className="pb-1">
              <CardTitle className="text-xs text-muted-foreground font-medium flex items-center gap-1.5">
                <span className="flex items-center justify-center w-5 h-5 rounded-md bg-primary/10">
                  <CalendarDays className="h-3 w-3 text-primary" />
                </span>
                Dias registrados
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-primary">
                {recentLogs.length}
                <span className="text-base font-normal text-muted-foreground ml-1">/ {period}d</span>
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Gráfico — largura total */}
      {chartData.length > 1 && (
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-primary/30">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">Evolução</CardTitle>
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
          </CardHeader>
          <CardContent>
            <MoodLineChart data={chartData} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
