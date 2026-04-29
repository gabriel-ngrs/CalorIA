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
import type { TooltipProps } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { WeeklyMacroPoint } from "@/types";

interface Props {
  data: WeeklyMacroPoint[];
  calorieGoal?: number;
  period?: number;
}

function BarTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  const value = payload[0].value as number;

  return (
    <div
      style={{
        background: "#FFFFFF",
        border: "1px solid #E5E7EB",
        borderRadius: "10px",
        padding: "10px 14px",
        boxShadow: "0 4px 20px rgba(0,0,0,0.08)",
        minWidth: "120px",
      }}
    >
      <p style={{ margin: "0 0 6px", fontSize: "11px", color: "#6B7280", fontWeight: 500 }}>{label}</p>
      <p style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "#F97316", lineHeight: 1.2 }}>
        {value.toFixed(0)}
        <span style={{ fontSize: "12px", fontWeight: 400, color: "#9CA3AF", marginLeft: "4px" }}>kcal</span>
      </p>
    </div>
  );
}

export function CaloriesBarChart({ data, calorieGoal, period }: Props) {
  const formatted = data.map((d) => ({
    ...d,
    date: new Date(d.date).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }),
  }));

  return (
    <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-accent/40">
      <CardHeader>
        <CardTitle className="text-sm">Calorias — últimos {period ?? 7} dias</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={formatted} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F3F4F6" />
            <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#9CA3AF" }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: "#9CA3AF" }} axisLine={false} tickLine={false} />
            <Tooltip content={<BarTooltip />} cursor={{ fill: "rgba(249,115,22,0.04)" }} />
            <Bar dataKey="calories" fill="#F97316" radius={[6, 6, 0, 0]} />
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
