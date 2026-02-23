"use client";

import { useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useWeightLogs, useLogWeight } from "@/lib/hooks/useLogs";
import { useWeightChart } from "@/lib/hooks/useDashboard";
import { useMe } from "@/lib/hooks/useProfile";

export default function PesoPage() {
  const [weight, setWeight] = useState("");
  const { data: logs } = useWeightLogs();
  const { data: chartData } = useWeightChart(90);
  const { data: user } = useMe();
  const logWeight = useLogWeight();

  const today = new Date().toISOString().slice(0, 10);

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

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">⚖️ Peso</h1>
        <p className="text-muted-foreground text-sm">Acompanhe sua evolução</p>
      </div>

      {latest && (
        <div className="flex gap-4">
          <Card className="flex-1">
            <CardHeader className="pb-1">
              <CardTitle className="text-sm text-muted-foreground">Peso atual</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{latest.weight_kg} <span className="text-base font-normal">kg</span></p>
            </CardContent>
          </Card>
          {user?.weight_goal && (
            <Card className="flex-1">
              <CardHeader className="pb-1">
                <CardTitle className="text-sm text-muted-foreground">Meta</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{user.weight_goal} <span className="text-base font-normal">kg</span></p>
                <p className={`text-xs mt-1 ${latest.weight_kg <= user.weight_goal ? "text-green-600" : "text-orange-600"}`}>
                  {latest.weight_kg <= user.weight_goal ? "✅ Meta atingida!" : `Faltam ${(latest.weight_kg - user.weight_goal).toFixed(1)} kg`}
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Gráfico */}
      {formatted.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Evolução — últimos 90 dias</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={formatted} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 10 }} domain={["dataMin - 2", "dataMax + 2"]} />
                <Tooltip formatter={(v: number) => [`${v} kg`, "Peso"]} />
                <Line type="monotone" dataKey="weight_kg" stroke="#f97316" strokeWidth={2} dot={false} />
                {user?.weight_goal && (
                  <ReferenceLine y={user.weight_goal} stroke="#22c55e" strokeDasharray="4 4" />
                )}
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Registrar */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Registrar peso</CardTitle>
        </CardHeader>
        <CardContent>
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
        </CardContent>
      </Card>

      {/* Histórico */}
      {logs && logs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Histórico</CardTitle>
          </CardHeader>
          <CardContent className="divide-y text-sm">
            {logs.slice(0, 10).map((l) => (
              <div key={l.id} className="flex justify-between py-1.5">
                <span className="text-muted-foreground">
                  {new Date(l.date).toLocaleDateString("pt-BR")}
                </span>
                <span className="font-medium">{l.weight_kg} kg</span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
