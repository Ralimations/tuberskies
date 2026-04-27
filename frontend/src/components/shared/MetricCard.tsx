import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  label: string;
  value: string;
  change?: number;
  changeLabel?: string;
  sparklineData?: number[];
  color?: "blue" | "purple" | "cyan" | "green" | "amber";
}

const colorMap = {
  blue: {
    stroke: "#4f6ef7",
    fill: "rgba(79,110,247,0.12)",
    text: "text-[var(--color-aria-blue)]",
    icon: "bg-[var(--color-aria-blue-dim)]",
  },
  purple: {
    stroke: "#8b5cf6",
    fill: "rgba(139,92,246,0.12)",
    text: "text-[var(--color-aria-purple)]",
    icon: "bg-[var(--color-aria-purple-dim)]",
  },
  cyan: {
    stroke: "#06b6d4",
    fill: "rgba(6,182,212,0.12)",
    text: "text-[var(--color-aria-cyan)]",
    icon: "bg-[var(--color-aria-cyan-dim)]",
  },
  green: {
    stroke: "#22c55e",
    fill: "rgba(34,197,94,0.10)",
    text: "text-[var(--color-aria-green)]",
    icon: "bg-[var(--color-aria-green-dim)]",
  },
  amber: {
    stroke: "#f59e0b",
    fill: "rgba(245,158,11,0.10)",
    text: "text-[var(--color-aria-amber)]",
    icon: "bg-amber-500/10",
  },
};

function MiniSparkline({
  data,
  color,
}: {
  data: number[];
  color: { stroke: string; fill: string };
}) {
  if (data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const W = 80;
  const H = 28;
  const pts = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * W;
      const y = H - ((v - min) / range) * (H - 4) - 2;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  const last = pts.split(" ").pop()!.split(",");
  const fillPath = `M0,${H} L${pts.replace(",", " L")} L${W},${H} Z`;

  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id={`sg-${color.stroke}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color.stroke} stopOpacity="0.35" />
          <stop offset="100%" stopColor={color.stroke} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={fillPath} fill={`url(#sg-${color.stroke})`} />
      <polyline points={pts} fill="none" stroke={color.stroke} strokeWidth="1.8" />
      {last && (
        <circle
          cx={parseFloat(last[0])}
          cy={parseFloat(last[1])}
          r="2.5"
          fill={color.stroke}
        />
      )}
    </svg>
  );
}

export function MetricCard({
  label,
  value,
  change,
  changeLabel,
  sparklineData = [],
  color = "blue",
}: MetricCardProps) {
  const c = colorMap[color];
  const isUp = change !== undefined && change >= 0;
  const isDown = change !== undefined && change < 0;

  return (
    <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-5 flex flex-col gap-3 hover:border-[var(--color-aria-border-strong)] transition-colors">
      <p className="text-xs font-semibold text-[var(--color-aria-muted)] uppercase tracking-wide">
        {label}
      </p>
      <div className="flex items-end justify-between gap-2">
        <p className="text-2xl font-bold text-[var(--color-aria-ink)] font-mono leading-none">
          {value}
        </p>
        <MiniSparkline data={sparklineData} color={c} />
      </div>
      {change !== undefined && (
        <div className={cn("flex items-center gap-1 text-xs font-semibold", isUp ? "text-[var(--color-aria-green)]" : isDown ? "text-[var(--color-aria-red)]" : "text-[var(--color-aria-muted)]")}>
          {isUp ? <TrendingUp className="h-3.5 w-3.5" /> : isDown ? <TrendingDown className="h-3.5 w-3.5" /> : <Minus className="h-3.5 w-3.5" />}
          {isUp ? "+" : ""}{change}%
          {changeLabel && <span className="text-[var(--color-aria-muted)] font-normal ml-1">{changeLabel}</span>}
        </div>
      )}
    </div>
  );
}
