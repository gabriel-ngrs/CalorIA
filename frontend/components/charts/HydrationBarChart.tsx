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
      <p style={{ margin: "0 0 4px", fontSize: "11px", color: "#94a3b8", fontWeight: 500 }}>{label}</p>
      <p style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: isGoal ? "#22c55e" : "#3b82f6", lineHeight: 1.2 }}>
        {value.toLocaleString("pt-BR")}
        <span style={{ fontSize: "12px", fontWeight: 400, color: "#64748b", marginLeft: "4px" }}>ml</span>
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
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(145,183,199,0.08)" />
        <XAxis dataKey="date" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
        <YAxis tick={{ fontSize: 10 }} />
        <Tooltip content={<HydrationTooltip />} cursor={{ fill: "rgba(59,130,246,0.06)" }} />
        <Bar dataKey="ml" radius={[5, 5, 0, 0]}>
          <LabelList
            dataKey="ml"
            position="top"
            style={{ fontSize: 9, fill: "#64748b" }}
            formatter={(v: number) => v >= 1000 ? `${(v / 1000).toFixed(1)}L` : `${v}`}
          />
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.isGoal ? "#22c55e" : "#3b82f6"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
