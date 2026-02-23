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
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { useMoodLogs, useLogMood } from "@/lib/hooks/useLogs";

const ENERGY_EMOJIS = ["😴", "😪", "😐", "😊", "⚡"];
const MOOD_EMOJIS = ["😞", "😕", "😐", "😊", "😄"];

export default function HumorPage() {
  const [energy, setEnergy] = useState(3);
  const [mood, setMood] = useState(3);
  const [notes, setNotes] = useState("");
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

  const chartData = (logs ?? [])
    .slice()
    .reverse()
    .slice(-30)
    .map((l) => ({
      date: new Date(l.date).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }),
      energia: l.energy_level,
      humor: l.mood_level,
    }));

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">😊 Humor & Energia</h1>
        <p className="text-muted-foreground text-sm">Como você está hoje?</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Registrar hoje</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <Label className="mb-2 block">
                ⚡ Energia: {ENERGY_EMOJIS[energy - 1]} {energy}/5
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
              <Label className="mb-2 block">
                😊 Humor: {MOOD_EMOJIS[mood - 1]} {mood}/5
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

      {chartData.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Evolução — últimos 30 dias</CardTitle>
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
