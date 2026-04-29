"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TooltipProps } from "recharts";

function MoodTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "#FFFFFF",
        border: "1px solid #E5E7EB",
        borderRadius: "10px",
        padding: "10px 14px",
        boxShadow: "0 4px 20px rgba(0,0,0,0.08)",
        minWidth: "130px",
      }}
    >
      <p style={{ margin: "0 0 6px", fontSize: "11px", color: "#6B7280", fontWeight: 500 }}>{label}</p>
      {payload.map((p, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "2px" }}>
          <span style={{ display: "inline-block", width: "8px", height: "8px", borderRadius: "50%", background: p.color }} />
          <span style={{ fontSize: "12px", color: "#6B7280", textTransform: "capitalize" }}>{p.dataKey}</span>
          <span style={{ fontSize: "13px", fontWeight: 600, color: "#111827", marginLeft: "auto" }}>{p.value}/5</span>
        </div>
      ))}
    </div>
  );
}

interface Props {
  data: { date: string; energia: number; humor: number }[];
}

export function MoodLineChart({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="#F3F4F6" />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#9CA3AF" }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
        <YAxis domain={[0, 5.5]} ticks={[1, 2, 3, 4, 5]} tick={{ fontSize: 10, fill: "#9CA3AF" }} axisLine={false} tickLine={false} />
        <Tooltip content={<MoodTooltip />} cursor={{ stroke: "rgba(139,92,246,0.15)", strokeWidth: 1 }} />
        {/* Sem legenda redundante — cores identificam as séries */}
        <Line type="monotone" dataKey="energia" stroke="#F97316" strokeWidth={2.5} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
        <Line type="monotone" dataKey="humor" stroke="#8B5CF6" strokeWidth={2.5} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
