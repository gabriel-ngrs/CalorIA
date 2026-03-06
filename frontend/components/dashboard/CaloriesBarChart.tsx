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
}

function BarTooltip({ active, payload, label }: TooltipProps<number, string>) {
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
      <p style={{ margin: "0 0 6px", fontSize: "11px", color: "#94a3b8", fontWeight: 500 }}>{label}</p>
      <p style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "#f97316", lineHeight: 1.2 }}>
        {value.toFixed(0)}
        <span style={{ fontSize: "12px", fontWeight: 400, color: "#64748b", marginLeft: "4px" }}>kcal</span>
      </p>
    </div>
  );
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
            <Tooltip content={<BarTooltip />} cursor={{ fill: "rgba(145, 183, 199, 0.06)" }} />
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
