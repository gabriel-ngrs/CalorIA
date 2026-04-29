"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TooltipProps } from "recharts";

function HydrationTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  const value = payload[0].value as number;
  const isGoal = payload[0].payload?.isGoal as boolean;
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
      <p style={{ margin: "0 0 4px", fontSize: "11px", color: "#6B7280", fontWeight: 500 }}>{label}</p>
      <p style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: isGoal ? "#22C55E" : "#3B82F6", lineHeight: 1.2 }}>
        {value.toLocaleString("pt-BR")}
        <span style={{ fontSize: "12px", fontWeight: 400, color: "#9CA3AF", marginLeft: "4px" }}>ml</span>
      </p>
    </div>
  );
}

interface Props {
  data: { date: string; ml: number; isGoal: boolean }[];
}

export function HydrationBarChart({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 16, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="#F3F4F6" />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#9CA3AF" }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
        <YAxis tick={{ fontSize: 10, fill: "#9CA3AF" }} axisLine={false} tickLine={false} />
        <Tooltip content={<HydrationTooltip />} cursor={{ fill: "rgba(59,130,246,0.04)" }} />
        <Bar dataKey="ml" radius={[6, 6, 0, 0]}>
          <LabelList
            dataKey="ml"
            position="top"
            style={{ fontSize: 9, fill: "#9CA3AF" }}
            formatter={(v: number) => v >= 1000 ? `${(v / 1000).toFixed(1)}L` : `${v}`}
          />
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.isGoal ? "#22C55E" : "#3B82F6"} fillOpacity={0.85} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
