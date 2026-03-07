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
      <p style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "#f97316", lineHeight: 1.2 }}>
        {value.toFixed(1)}
        <span style={{ fontSize: "12px", fontWeight: 400, color: "#64748b", marginLeft: "4px" }}>kg</span>
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
            <stop offset="5%" stopColor="#f97316" stopOpacity={0.25} />
            <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(145,183,199,0.08)" />
        <XAxis dataKey="date" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
        <YAxis tick={{ fontSize: 10 }} domain={["dataMin - 1", "dataMax + 1"]} />
        <Tooltip content={<WeightTooltip />} cursor={{ stroke: "rgba(249,115,22,0.3)", strokeWidth: 1 }} />
        <Area
          type="monotone"
          dataKey="weight_kg"
          stroke="#f97316"
          strokeWidth={2.5}
          fill="url(#weightGrad)"
          dot={false}
          activeDot={{ r: 5, fill: "#f97316", strokeWidth: 0 }}
        />
        {weightGoal && (
          <ReferenceLine
            y={weightGoal}
            stroke="#22c55e"
            strokeDasharray="4 4"
            strokeWidth={1.5}
            label={{ value: `Meta ${weightGoal}kg`, fontSize: 10, fill: "#22c55e", position: "insideTopRight" }}
          />
        )}
      </AreaChart>
    </ResponsiveContainer>
  );
}
