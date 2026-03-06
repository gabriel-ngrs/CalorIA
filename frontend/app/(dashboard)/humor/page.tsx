"use client";

import { useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Star, Smile, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { useMoodLogs, useLogMood } from "@/lib/hooks/useLogs";


const LEVEL_LABELS = ["Muito baixo", "Baixo", "Médio", "Alto", "Muito alto"];

export default function HumorPage() {
  const [energy, setEnergy] = useState(3);
  const [mood, setMood] = useState(3);
  const [notes, setNotes] = useState("");
  const [period, setPeriod] = useState<7 | 14 | 30>(7);
  const { data: logs } = useMoodLogs();
  const logMood = useLogMood();

  const today = new Date().toISOString().slice(0, 10);

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
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
            <Smile className="h-6 w-6 text-yellow-400" />
            Humor & Energia
          </h1>
        <p className="text-muted-foreground text-sm">Como você está hoje?</p>
      </div>

      {/* Registrar */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Registrar hoje</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <Label className="mb-2 flex items-center gap-1.5">
                <Zap className="h-3.5 w-3.5 text-orange-500" />
                Energia: {energy}/5 — {LEVEL_LABELS[energy - 1]}
              </Label>
              <Slider
                min={1}
                max={5}
                step={1}
                value={[energy]}
                onValueChange={([v]) => setEnergy(v)}
                className="w-full"
              />
            </div>
            <div>
              <Label className="mb-2 flex items-center gap-1.5">
                <Smile className="h-3.5 w-3.5 text-blue-500" />
                Humor: {mood}/5 — {LEVEL_LABELS[mood - 1]}
              </Label>
              <Slider
                min={1}
                max={5}
                step={1}
                value={[mood]}
                onValueChange={([v]) => setMood(v)}
                className="w-full"
              />
            </div>
            <div>
              <Label htmlFor="notes">Notas (opcional)</Label>
              <Input
                id="notes"
                placeholder="Como foi seu dia?"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="mt-1"
              />
            </div>
            <Button type="submit" disabled={logMood.isPending}>
              {logMood.isPending ? "Salvando..." : "Registrar"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Métricas */}
      {recentLogs.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-orange-500">
                {avgEnergy !== null ? avgEnergy.toFixed(1) : "—"}
              </p>
              <p className="text-xs text-muted-foreground mt-1 flex items-center justify-center gap-1"><Zap className="h-3 w-3" /> Média energia</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-blue-500">
                {avgMood !== null ? avgMood.toFixed(1) : "—"}
              </p>
              <p className="text-xs text-muted-foreground mt-1 flex items-center justify-center gap-1"><Smile className="h-3 w-3" /> Média humor</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-green-500">{recentLogs.length}</p>
              <p className="text-xs text-muted-foreground mt-1">Dias registrados</p>
            </CardContent>
          </Card>
        </div>
      )}

      {bestDay && (
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="pt-4">
            <p className="text-sm font-medium flex items-center gap-1.5">
              <Star className="h-4 w-4 text-yellow-400 fill-yellow-400" />
              Melhor dia do período
            </p>
            <p className="text-base font-semibold mt-1">
              {new Date(bestDay.date + "T12:00").toLocaleDateString("pt-BR", { weekday: "long", day: "2-digit", month: "long" })}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Energia {bestDay.energy_level}/5 · Humor {bestDay.mood_level}/5
              {bestDay.notes && ` · "${bestDay.notes}"`}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Gráfico */}
      {chartData.length > 1 && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">Evolução</CardTitle>
            <div className="flex gap-1">
              {([7, 14, 30] as const).map((d) => (
                <Button
                  key={d}
                  size="sm"
                  variant={period === d ? "default" : "outline"}
                  className="h-6 px-2 text-xs"
                  onClick={() => setPeriod(d)}
                >
                  {d}d
                </Button>
              ))}
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                <YAxis domain={[0, 5.5]} tick={{ fontSize: 10 }} ticks={[1, 2, 3, 4, 5]} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="energia" stroke="#f97316" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="humor" stroke="#3b82f6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
