import { type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface InsightCardProps {
  icon: LucideIcon;
  title: string;
  body: string;
  cta?: string;
  color?: "blue" | "purple" | "cyan" | "green" | "amber";
  onCta?: () => void;
}

const colorMap = {
  blue: { icon: "bg-[var(--color-aria-blue-dim)] text-[var(--color-aria-blue)]", cta: "text-[var(--color-aria-blue)]" },
  purple: { icon: "bg-[var(--color-aria-purple-dim)] text-[var(--color-aria-purple)]", cta: "text-[var(--color-aria-purple)]" },
  cyan: { icon: "bg-[var(--color-aria-cyan-dim)] text-[var(--color-aria-cyan)]", cta: "text-[var(--color-aria-cyan)]" },
  green: { icon: "bg-[var(--color-aria-green-dim)] text-[var(--color-aria-green)]", cta: "text-[var(--color-aria-green)]" },
  amber: { icon: "bg-amber-500/10 text-[var(--color-aria-amber)]", cta: "text-[var(--color-aria-amber)]" },
};

export function InsightCard({ icon: Icon, title, body, cta, color = "blue", onCta }: InsightCardProps) {
  const c = colorMap[color];
  return (
    <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-5 flex flex-col gap-3 hover:border-[var(--color-aria-border-strong)] transition-colors">
      <div className={cn("h-9 w-9 rounded-xl flex items-center justify-center", c.icon)}>
        <Icon className="h-4.5 w-4.5" />
      </div>
      <div>
        <p className="text-sm font-semibold text-[var(--color-aria-ink)] mb-1">{title}</p>
        <p className="text-xs text-[var(--color-aria-muted)] leading-relaxed">{body}</p>
      </div>
      {cta && (
        <button
          onClick={onCta}
          className={cn("text-xs font-semibold mt-auto text-left flex items-center gap-1 hover:opacity-70 transition-opacity", c.cta)}
        >
          {cta} →
        </button>
      )}
    </div>
  );
}
