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
    <div className="flex h-full flex-col rounded-[24px] bg-white/5 p-6">
      <div className="mb-[var(--space-default)] flex items-start gap-[var(--space-block)]">
        <div className={cn("mt-0.5 flex h-11 w-11 items-center justify-center rounded-2xl", c.icon)}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <p className="mb-[var(--space-title-subtitle)] text-base font-semibold text-[var(--color-aria-ink)]">{title}</p>
          <p className="min-w-0 pr-1 text-sm leading-6 text-[var(--color-aria-muted)] line-clamp-3">{body}</p>
        </div>
      </div>
      {cta && (
        <div className="mt-[var(--space-default)] pt-[var(--space-default)]">
          <button onClick={onCta} className={cn("text-left text-sm font-semibold transition-opacity hover:opacity-75", c.cta)}>
          {cta} {"->"}
          </button>
        </div>
      )}
    </div>
  );
}
