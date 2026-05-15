import { TrendingDown, TrendingUp, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  label: string;
  value: string;
  change?: number;
  changeLabel?: string;
  sparklineData?: number[];
  color?: "blue" | "purple" | "cyan" | "green" | "amber";
  detail?: string;
}

export function MetricCard({
  label,
  value,
  change,
  changeLabel,
  color = "blue",
  detail,
}: MetricCardProps) {
  const isUp = change !== undefined && change > 0;
  const isDown = change !== undefined && change < 0;

  return (
    <div className="flex h-full flex-col justify-between gap-[var(--space-default)] rounded-[24px] bg-white/5 p-6">
      <div className="flex items-start justify-between gap-[var(--space-block)]">
        <div className="min-w-0 space-y-[var(--space-title-subtitle)] pl-0.5 pr-2">
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--color-aria-muted)]">{label}</p>
          <p className="break-words font-mono text-3xl font-bold leading-none text-[var(--color-aria-ink)]">{value}</p>
        </div>
        <span
          className={cn(
            "rounded-full px-3 py-1 text-xs font-semibold",
            color === "blue" && "bg-[var(--color-aria-blue-dim)] text-[var(--color-aria-blue)]",
            color === "purple" && "bg-[var(--color-aria-purple-dim)] text-[var(--color-aria-purple)]",
            color === "cyan" && "bg-[var(--color-aria-cyan-dim)] text-[var(--color-aria-cyan)]",
            color === "green" && "bg-[var(--color-aria-green-dim)] text-[var(--color-aria-green)]",
            color === "amber" && "bg-amber-500/10 text-[var(--color-aria-amber)]",
          )}
        >
          {change !== undefined ? `${change > 0 ? "+" : ""}${change}%` : "steady"}
        </span>
      </div>

      <div className="space-y-[var(--space-block)]">
        {change !== undefined && (
          <div
            className={cn(
              "flex items-center gap-[var(--space-tight)] text-xs font-semibold",
              isUp ? "text-[var(--color-aria-green)]" : isDown ? "text-[var(--color-aria-red)]" : "text-[var(--color-aria-muted)]",
            )}
          >
            {isUp ? <TrendingUp className="h-3.5 w-3.5" /> : isDown ? <TrendingDown className="h-3.5 w-3.5" /> : <Minus className="h-3.5 w-3.5" />}
            <span>{changeLabel || "vs prior period"}</span>
          </div>
        )}
        {detail && <p className="line-clamp-3 text-sm leading-6 text-[var(--color-aria-muted)]">{detail}</p>}
      </div>
    </div>
  );
}
