"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { useHydrationToday, useLogHydration } from "@/lib/hooks/useLogs";

const QUICK_OPTIONS = [200, 300, 500];
const GOAL_ML = 2000;

export default function HidratacaoPage() {
  const [custom, setCustom] = useState("");
  const { data: summary, isLoading } = useHydrationToday();
  const logHydration = useLogHydration();

  const today = new Date().toISOString().slice(0, 10);
  const now = new Date();
  const timeStr = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;

  async function log(ml: number) {
    if (ml <= 0) return;
    await logHydration.mutateAsync({ amount_ml: ml, date: today, time: timeStr });
    setCustom("");
  }

  const total = summary?.total_ml ?? 0;
  const pct = Math.min((total / GOAL_ML) * 100, 100);

  return (
    <div className="space-y-6 max-w-md">
      <div>
        <h1 className="text-2xl font-bold">💧 Hidratação</h1>
        <p className="text-muted-foreground text-sm">Controle seu consumo de água</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="text-center mb-4">
            <p className="text-4xl font-bold text-blue-500">
              {total} <span className="text-xl font-normal text-muted-foreground">ml</span>
            </p>
            <p className="text-sm text-muted-foreground mt-1">de {GOAL_ML} ml hoje</p>
          </div>
          <Progress value={pct} className="h-3" />
          <p className="text-center text-sm font-medium mt-2">{pct.toFixed(0)}%</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Adicionar</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            {QUICK_OPTIONS.map((ml) => (
              <Button
                key={ml}
                variant="outline"
                className="flex-1"
                disabled={logHydration.isPending}
                onClick={() => log(ml)}
              >
                +{ml} ml
              </Button>
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
              onClick={() => log(parseInt(custom))}
              disabled={!custom || logHydration.isPending}
            >
              Adicionar
            </Button>
          </div>
        </CardContent>
      </Card>

      {pct >= 100 && (
        <p className="text-center text-green-600 font-medium">
          🎉 Meta diária atingida! Continue bebendo água.
        </p>
      )}
    </div>
  );
}
