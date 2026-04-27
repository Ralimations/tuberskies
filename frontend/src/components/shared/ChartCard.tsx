import { useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { cn } from "@/lib/utils";

interface ChartCardProps {
  title: string;
  data: Record<string, unknown>[];
  metrics?: { key: string; label: string; color: string }[];
  dateKey?: string;
}

const DEFAULT_METRICS = [
  { key: "views", label: "Views", color: "#4f6ef7" },
  { key: "watch_time_hours", label: "Watch Time", color: "#06b6d4" },
  { key: "retention", label: "Retention", color: "#22c55e" },
  { key: "subscribers_gained", label: "Subscribers", color: "#8b5cf6" },
];

function CustomTooltip({ active, payload, label }: Record<string, unknown>) {
  if (!active || !payload || !(payload as unknown[]).length) return null;
  const p = (payload as Array<{ color: string; name: string; value: number }>)[0];
  return (
    <div className="rounded-xl bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border-strong)] px-3 py-2 shadow-xl">
      <p className="text-[10px] text-[var(--color-aria-muted)] mb-1">{String(label)}</p>
      <p className="text-sm font-bold" style={{ color: p.color }}>
        {Number(p.value).toLocaleString()} {p.name}
      </p>
    </div>
  );
}

export function ChartCard({ title, data, metrics = DEFAULT_METRICS, dateKey = "date" }: ChartCardProps) {
  const [active, setActive] = useState(metrics[0].key);
  const metric = metrics.find((m) => m.key === active) ?? metrics[0];

  const chartData = data.map((row) => ({
    date:
      typeof row[dateKey] === "string"
        ? String(row[dateKey]).slice(0, 10)
        : row[dateKey],
    [metric.key]: Number(row[metric.key] ?? 0),
  }));

  return (
    <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-5">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <p className="text-sm font-semibold text-[var(--color-aria-ink)]">{title}</p>
        <div className="flex gap-1">
          {metrics.map((m) => (
            <button
              key={m.key}
              onClick={() => setActive(m.key)}
              className={cn(
                "px-3 py-1 rounded-lg text-xs font-semibold transition-all",
                active === m.key
                  ? "text-white"
                  : "text-[var(--color-aria-muted)] hover:text-[var(--color-aria-ink)] bg-transparent"
              )}
              style={active === m.key ? { backgroundColor: m.color + "33", color: m.color } : {}}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id={`cg-${metric.key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={metric.color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={metric.color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(255,255,255,0.04)"
            vertical={false}
          />
          <XAxis
            dataKey="date"
            tick={{ fill: "var(--color-aria-faint)", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v: string) => {
              try {
                return new Date(v).toLocaleDateString("en", { month: "short", day: "numeric" });
              } catch {
                return v;
              }
            }}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fill: "var(--color-aria-faint)", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v: number) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey={metric.key}
            stroke={metric.color}
            strokeWidth={2.5}
            fill={`url(#cg-${metric.key})`}
            dot={false}
            activeDot={{ r: 5, fill: metric.color, strokeWidth: 0 }}
            name={metric.label}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
