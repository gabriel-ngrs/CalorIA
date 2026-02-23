"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { NutritionSummary } from "@/types";

interface Props {
  nutrition: NutritionSummary;
}

const COLORS = ["#f97316", "#ef4444", "#eab308", "#3b82f6"];

export function MacroPieChart({ nutrition }: Props) {
  const data = [
    { name: "Proteína", value: Number((nutrition.total_protein * 4).toFixed(0)) },
    { name: "Carboidrato", value: Number((nutrition.total_carbs * 4).toFixed(0)) },
    { name: "Gordura", value: Number((nutrition.total_fat * 9).toFixed(0)) },
  ].filter((d) => d.value > 0);

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Distribuição de macros</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-40 text-muted-foreground text-sm">
          Sem dados hoje
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Distribuição de macros</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={80}
              paddingAngle={3}
              dataKey="value"
            >
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i + 1]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number, name: string) => [`${value} kcal`, name]}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="flex justify-center gap-4 text-xs mt-1">
          {data.map((d, i) => (
            <span key={d.name} className="flex items-center gap-1">
              <span
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{ background: COLORS[i + 1] }}
              />
              {d.name}
            </span>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
