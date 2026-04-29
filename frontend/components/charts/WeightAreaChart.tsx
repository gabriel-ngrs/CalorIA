"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TooltipProps } from "recharts";

function WeightTooltip({ active, payload, label }: TooltipProps<number, string>) {
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
      <p style={{ margin: "0 0 4px", fontSize: "11px", color: "#6B7280", fontWeight: 500 }}>{label}</p>
      <p style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "#10B981", lineHeight: 1.2 }}>
        {value.toFixed(1)}
        <span style={{ fontSize: "12px", fontWeight: 400, color: "#9CA3AF", marginLeft: "4px" }}>kg</span>
      </p>
    </div>
  );
}

interface Props {
  data: { date: string; weight_kg: number }[];
  weightGoal?: number;
}

export function WeightAreaChart({ data, weightGoal }: Props) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={data} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
        <defs>
          <linearGradient id="weightGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#10B981" stopOpacity={0.12} />
            <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="#F3F4F6" />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#9CA3AF" }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
        <YAxis tick={{ fontSize: 10, fill: "#9CA3AF" }} axisLine={false} tickLine={false} domain={["dataMin - 1", "dataMax + 1"]} />
        <Tooltip content={<WeightTooltip />} cursor={{ stroke: "rgba(16,185,129,0.2)", strokeWidth: 1 }} />
        <Area
          type="monotone"
          dataKey="weight_kg"
          stroke="#10B981"
          strokeWidth={2.5}
          fill="url(#weightGrad)"
          dot={false}
          activeDot={{ r: 4, fill: "#10B981", strokeWidth: 0 }}
        />
        {weightGoal && (
          <ReferenceLine
            y={weightGoal}
            stroke="#22C55E"
            strokeDasharray="4 4"
            strokeWidth={1.5}
            label={{ value: `Meta ${weightGoal}kg`, fontSize: 10, fill: "#22C55E", position: "insideTopRight" }}
          />
        )}
      </AreaChart>
    </ResponsiveContainer>
  );
}
