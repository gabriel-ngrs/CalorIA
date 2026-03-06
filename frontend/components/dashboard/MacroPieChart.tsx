"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { TooltipProps } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { NutritionSummary } from "@/types";

interface Props {
  nutrition: NutritionSummary;
}

const COLORS = ["#f97316", "#ef4444", "#eab308"];

function PieTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  const item = payload[0];
  const color = item.payload?.fill ?? item.fill ?? "#fff";
  const total = item.payload?.total as number | undefined;
  const pct = total && item.value ? ((item.value / total) * 100).toFixed(0) : null;

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
        minWidth: "130px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
        <span
          style={{
            display: "inline-block",
            width: "10px",
            height: "10px",
            borderRadius: "50%",
            background: color,
            flexShrink: 0,
          }}
        />
        <span style={{ fontSize: "12px", color: "#94a3b8", fontWeight: 500 }}>{item.name}</span>
      </div>
      <p style={{ margin: 0, fontSize: "20px", fontWeight: 700, color, lineHeight: 1.2 }}>
        {item.value}
        <span style={{ fontSize: "12px", fontWeight: 400, color: "#64748b", marginLeft: "4px" }}>kcal</span>
      </p>
      {pct && (
        <p style={{ margin: "4px 0 0", fontSize: "11px", color: "#64748b" }}>{pct}% do total</p>
      )}
    </div>
  );
}

export function MacroPieChart({ nutrition }: Props) {
  const rawData = [
    { name: "Proteína",    value: Number((nutrition.total_protein * 4).toFixed(0)) },
    { name: "Carboidrato", value: Number((nutrition.total_carbs * 4).toFixed(0)) },
    { name: "Gordura",     value: Number((nutrition.total_fat * 9).toFixed(0)) },
  ].filter((d) => d.value > 0);

  const total = rawData.reduce((s, d) => s + d.value, 0);
  const data = rawData.map((d) => ({ ...d, total }));

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
    <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-primary/30">
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
                <Cell key={i} fill={COLORS[i]} />
              ))}
            </Pie>
            <Tooltip
              content={<PieTooltip />}
              cursor={false}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="flex justify-center gap-4 text-xs mt-1">
          {data.map((d, i) => (
            <span key={d.name} className="flex items-center gap-1">
              <span
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{ background: COLORS[i] }}
              />
              {d.name}
            </span>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
