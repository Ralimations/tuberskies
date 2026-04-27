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
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-2xl border border-[var(--color-aria-border)] bg-gradient-to-br from-[var(--color-aria-surface)] via-[#131827] to-[#0e0f1a] p-6 flex flex-col md:flex-row gap-6"
    >
      <div className="flex-1 min-w-0">
        <Badge color="blue" dot className="mb-3">Next Best Action</Badge>
        <h2 className="text-2xl font-bold text-[var(--color-aria-ink)] leading-tight mb-1">
          {action.split(" on ")[0]}
        </h2>
        {action.includes(" on ") && (
          <h2 className="text-2xl font-bold gradient-text leading-tight mb-3">
            on {action.split(" on ")[1]}
          </h2>
        )}
        <p className="text-sm text-[var(--color-aria-muted)] mb-5 max-w-md">{detail}</p>
        <div className="flex items-center gap-3 flex-wrap">
          <Button variant="primary" size="md" onClick={onSchedule}>
            <Calendar className="h-4 w-4" />
            Schedule Upload
          </Button>
          <Button variant="secondary" size="md" onClick={onSeeWhy}>
            <BarChart2 className="h-4 w-4" />
            See Why
          </Button>
        </div>
      </div>

      {/* Confidence ring + reasons */}
      <div className="flex flex-col md:flex-row items-start gap-5 shrink-0">
        <ConfidenceRing value={confidence} />
        <div className="space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-[var(--color-aria-muted)] mb-1">
            Why This Works
          </p>
          {reasons.map((r) => (
            <div key={r} className="flex items-center gap-2 text-xs text-[var(--color-aria-muted)]">
              <CheckCircle2 className="h-3.5 w-3.5 text-[var(--color-aria-green)] shrink-0" />
              {r}
            </div>
          ))}
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
    <div className="flex flex-col items-center gap-1">
      <div className="relative h-24 w-24">
        <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
          <circle cx="50" cy="50" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
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
            <linearGradient id="ring-grad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#4f6ef7" />
              <stop offset="100%" stopColor="#8b5cf6" />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-black text-[var(--color-aria-ink)] font-mono">{value}%</span>
        </div>
      </div>
      <p className="text-[10px] text-[var(--color-aria-muted)] font-semibold uppercase tracking-wide">
        High Confidence
      </p>
    </div>
  );
}
