import { Calendar, BarChart2, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

interface NextBestActionProps {
  action: string;
  detail: string;
  confidence: number;
  reasons?: string[];
  onSchedule?: () => void;
  onSeeWhy?: () => void;
}

export function NextBestAction({
  action,
  detail,
  confidence,
  reasons = [],
  onSchedule,
  onSeeWhy,
}: NextBestActionProps) {
  const topReasons = reasons.slice(0, 2);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-[28px] bg-[linear-gradient(135deg,rgba(96,165,250,0.16),rgba(94,234,212,0.08)_36%,rgba(15,23,42,0.74)_78%)] p-6"
    >
      <div className="grid items-stretch gap-[var(--space-card-grid)] xl:grid-cols-12">
        <div className="flex h-full min-w-0 flex-col pr-1 xl:col-span-8">
          <Badge color="blue" dot className="mb-3 ml-0.5">
            Next best action
          </Badge>
          <h2 className="max-w-2xl pl-0.5 text-4xl font-semibold leading-[1.05] tracking-[-0.02em] text-[var(--color-aria-ink)]">
            {action}
          </h2>
          <p className="mt-[var(--space-title-subtitle)] max-w-2xl text-base leading-7 text-[var(--color-aria-muted)]">{detail}</p>
          <div className="mt-[var(--space-default)] flex flex-wrap items-center gap-[var(--space-default)]">
            <Button variant="primary" size="lg" onClick={onSchedule}>
              <Calendar className="h-4 w-4" />
              Schedule upload
            </Button>
            <Button variant="secondary" size="lg" onClick={onSeeWhy}>
              <BarChart2 className="h-4 w-4" />
              See the reasoning
            </Button>
          </div>
        </div>

        <div className="grid auto-rows-fr gap-[var(--space-card-grid)] xl:col-span-4">
          <div className="flex h-full flex-col rounded-[24px] bg-white/6 p-6">
            <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-[var(--color-aria-faint)]">Confidence</p>
            <div className="mt-[var(--space-default)] flex items-end justify-between gap-[var(--space-default)] pt-[var(--space-default)]">
              <div>
                <p className="mb-[var(--space-title-subtitle)] font-mono text-4xl font-bold text-[var(--color-aria-ink)]">{confidence}%</p>
                <p className="text-sm text-[var(--color-aria-muted)]">Strong enough to act on now.</p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--color-aria-cyan-dim)] text-[var(--color-aria-cyan)]">
                <Sparkles className="h-5 w-5" />
              </div>
            </div>
          </div>

          <div className="flex h-full flex-col rounded-[24px] bg-white/6 p-6">
            <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-[var(--color-aria-faint)]">Why now</p>
            <div className="mt-[var(--space-default)] flex-1 space-y-[var(--space-block)] pt-[var(--space-default)]">
              {topReasons.map((reason) => (
                <div key={reason} className="rounded-2xl bg-white/4 px-4 py-2 text-sm leading-6 text-[var(--color-aria-muted)]">
                  {reason}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
