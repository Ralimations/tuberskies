import { CheckCircle2, Calendar, BarChart2 } from "lucide-react";
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
  reasons = [
    "Highest retention on Thursdays",
    "Your audience is most active",
    "Matches your best performing pattern",
    "Low competition at this time",
  ],
  onSchedule,
  onSeeWhy,
}: NextBestActionProps) {
  const [lead, rest] = action.split(" on ");

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="overflow-hidden rounded-[28px] border border-[var(--color-aria-border)] bg-[linear-gradient(135deg,rgba(96,165,250,0.14),rgba(94,234,212,0.08)_38%,rgba(15,23,42,0.72)_80%)] p-6"
    >
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_280px]">
        <div className="min-w-0">
          <Badge color="blue" dot className="mb-4">
            Next best action
          </Badge>
          <h2 className="text-3xl font-semibold leading-tight tracking-[-0.03em] text-[var(--color-aria-ink)]">
            {lead}
          </h2>
          {rest && <p className="gradient-text mt-1 text-2xl font-semibold leading-tight">on {rest}</p>}
          <p className="mt-4 max-w-xl text-sm leading-6 text-[var(--color-aria-muted)]">{detail}</p>
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Button variant="primary" size="md" onClick={onSchedule}>
              <Calendar className="h-4 w-4" />
              Schedule upload
            </Button>
            <Button variant="secondary" size="md" onClick={onSeeWhy}>
              <BarChart2 className="h-4 w-4" />
              See why
            </Button>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-[120px_minmax(0,1fr)] lg:grid-cols-1">
          <ConfidenceRing value={confidence} />
          <div className="rounded-[24px] border border-[var(--color-aria-border)] bg-white/6 p-4">
            <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.22em] text-[var(--color-aria-faint)]">
              Why this works
            </p>
            <div className="space-y-2">
              {reasons.map((reason) => (
                <div key={reason} className="flex items-start gap-2 text-xs leading-5 text-[var(--color-aria-muted)]">
                  <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--color-aria-green)]" />
                  <span>{reason}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function ConfidenceRing({ value }: { value: number }) {
  const r = 38;
  const circ = 2 * Math.PI * r;
  const offset = circ - (value / 100) * circ;

  return (
    <div className="flex items-center gap-4 rounded-[24px] border border-[var(--color-aria-border)] bg-white/6 p-4">
      <div className="relative h-24 w-24 shrink-0">
        <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
          <circle cx="50" cy="50" r={r} fill="none" stroke="rgba(148,163,184,0.16)" strokeWidth="8" />
          <circle
            cx="50"
            cy="50"
            r={r}
            fill="none"
            stroke="url(#ring-grad)"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 1s ease" }}
          />
          <defs>
            <linearGradient id="ring-grad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#67b7ff" />
              <stop offset="100%" stopColor="#5eead4" />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-mono text-2xl font-bold text-[var(--color-aria-ink)]">{value}%</span>
        </div>
      </div>
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-[var(--color-aria-faint)]">
          Confidence
        </p>
        <p className="mt-1 text-sm font-semibold text-[var(--color-aria-ink)]">High confidence recommendation</p>
      </div>
    </div>
  );
}
