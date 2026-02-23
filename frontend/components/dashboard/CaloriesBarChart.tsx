"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { WeeklyMacroPoint } from "@/types";

interface Props {
  data: WeeklyMacroPoint[];
  calorieGoal?: number;
}

export function CaloriesBarChart({ data, calorieGoal }: Props) {
  const formatted = data.map((d) => ({
    ...d,
    date: new Date(d.date).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Calorias — últimos 7 dias</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={formatted} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v: number) => [`${v} kcal`, "Calorias"]} />
            <Bar dataKey="calories" fill="#f97316" radius={[4, 4, 0, 0]} />
            {calorieGoal && (
              <ReferenceLine
                y={calorieGoal}
                stroke="#22c55e"
                strokeDasharray="4 4"
                label={{ value: "Meta", fontSize: 10, fill: "#22c55e" }}
              />
            )}
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
