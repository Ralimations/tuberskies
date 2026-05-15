import { useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { cn } from "@/lib/utils";

interface ChartCardProps {
  title: string;
  data: Record<string, unknown>[];
  metrics?: { key: string; label: string; color: string }[];
  dateKey?: string;
  summary?: string;
  annotation?: { date: string; label: string } | null;
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
    <div className="rounded-xl border border-[var(--color-aria-border-strong)] bg-[var(--color-aria-surface-3)] px-3 py-2 shadow-xl">
      <p className="mb-1 text-[10px] text-[var(--color-aria-muted)]">{String(label)}</p>
      <p className="text-sm font-bold" style={{ color: p.color }}>
        {Number(p.value).toLocaleString()} {p.name}
      </p>
    </div>
  );
}

export function ChartCard({ title, data, metrics = DEFAULT_METRICS, dateKey = "date", summary, annotation }: ChartCardProps) {
  const [active, setActive] = useState(metrics[0].key);
  const metric = metrics.find((m) => m.key === active) ?? metrics[0];

  const chartData = data.map((row) => ({
    date: typeof row[dateKey] === "string" ? String(row[dateKey]).slice(0, 10) : row[dateKey],
    [metric.key]: Number(row[metric.key] ?? 0),
  }));

  return (
    <div className="flex h-full flex-col rounded-[28px] bg-white/4 p-6">
      <div className="flex flex-col gap-[var(--space-default)] lg:flex-row lg:items-start lg:justify-between">
        <div className="max-w-xl space-y-[var(--space-title-subtitle)]">
          <p className="text-lg font-semibold text-[var(--color-aria-ink)]">{title}</p>
          {summary && <p className="text-sm leading-6 text-[var(--color-aria-muted)]">{summary}</p>}
        </div>
        <div className="flex flex-wrap items-center gap-[var(--space-tight)]">
          {metrics.map((m) => (
            <button
              key={m.key}
              onClick={() => setActive(m.key)}
              className={cn(
                "rounded-full px-3 py-1.5 text-xs font-semibold transition-all",
                active === m.key ? "text-white" : "bg-white/4 text-[var(--color-aria-muted)] hover:text-[var(--color-aria-ink)]",
              )}
              style={active === m.key ? { backgroundColor: `${m.color}22`, color: m.color } : {}}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6 min-h-[280px] flex-1 overflow-hidden rounded-[24px] bg-white/[0.03] p-5">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 12, right: 8, left: -24, bottom: 8 }}>
            <defs>
              <linearGradient id={`cg-${metric.key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={metric.color} stopOpacity={0.34} />
                <stop offset="95%" stopColor={metric.color} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
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
              tickFormatter={(v: number) => (v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v))}
            />
            <Tooltip content={<CustomTooltip />} />
            {annotation ? (
              <ReferenceLine
                x={annotation.date}
                stroke="rgba(255,255,255,0.18)"
                strokeDasharray="4 4"
                label={{ value: annotation.label, position: "insideTopRight", fill: "var(--color-aria-muted)", fontSize: 11 }}
              />
            ) : null}
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
    </div>
  );
}
