import { cn } from "@/lib/utils";
import { type HTMLAttributes } from "react";

type BadgeColor = "blue" | "purple" | "green" | "amber" | "red" | "cyan" | "muted";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  color?: BadgeColor;
  dot?: boolean;
}

const colorMap: Record<BadgeColor, string> = {
  blue: "bg-[var(--color-aria-blue-dim)] text-[var(--color-aria-blue)] border-[var(--color-aria-blue)]/20",
  purple: "bg-[var(--color-aria-purple-dim)] text-[var(--color-aria-purple)] border-[var(--color-aria-purple)]/20",
  green: "bg-[var(--color-aria-green-dim)] text-[var(--color-aria-green)] border-green-500/20",
  amber: "bg-amber-500/10 text-[var(--color-aria-amber)] border-amber-500/20",
  red: "bg-red-500/10 text-[var(--color-aria-red)] border-red-500/20",
  cyan: "bg-[var(--color-aria-cyan-dim)] text-[var(--color-aria-cyan)] border-cyan-500/20",
  muted: "bg-[var(--color-aria-surface-3)] text-[var(--color-aria-muted)] border-[var(--color-aria-border)]",
};

const dotMap: Record<BadgeColor, string> = {
  blue: "bg-[var(--color-aria-blue)]",
  purple: "bg-[var(--color-aria-purple)]",
  green: "bg-[var(--color-aria-green)]",
  amber: "bg-[var(--color-aria-amber)]",
  red: "bg-[var(--color-aria-red)]",
  cyan: "bg-[var(--color-aria-cyan)]",
  muted: "bg-[var(--color-aria-muted)]",
};

export function Badge({ className, color = "muted", dot = false, children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-[10px] font-semibold uppercase tracking-wide",
        colorMap[color],
        className
      )}
      {...props}
    >
      {dot && <span className={cn("h-1.5 w-1.5 rounded-full shrink-0", dotMap[color])} />}
      {children}
    </span>
  );
}
