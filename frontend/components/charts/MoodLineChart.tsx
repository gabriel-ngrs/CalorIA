"use client";

import {
  CartesianGrid,
  Legend,
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
      <p style={{ margin: "0 0 6px", fontSize: "11px", color: "#94a3b8", fontWeight: 500 }}>{label}</p>
      {payload.map((p, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "2px" }}>
          <span style={{ display: "inline-block", width: "8px", height: "8px", borderRadius: "50%", background: p.color }} />
          <span style={{ fontSize: "12px", color: "#94a3b8", textTransform: "capitalize" }}>{p.dataKey}</span>
          <span style={{ fontSize: "13px", fontWeight: 600, color: "#e2e8f0", marginLeft: "auto" }}>{p.value}/5</span>
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
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(145,183,199,0.08)" />
        <XAxis dataKey="date" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
        <YAxis domain={[0, 5.5]} ticks={[1, 2, 3, 4, 5]} tick={{ fontSize: 10 }} />
        <Tooltip content={<MoodTooltip />} cursor={{ stroke: "rgba(145,183,199,0.2)", strokeWidth: 1 }} />
        <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }} />
        <Line type="monotone" dataKey="energia" stroke="#f97316" strokeWidth={2.5} dot={false} activeDot={{ r: 5, strokeWidth: 0 }} />
        <Line type="monotone" dataKey="humor" stroke="#3b82f6" strokeWidth={2.5} dot={false} activeDot={{ r: 5, strokeWidth: 0 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
