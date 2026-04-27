import { useEffect, useState } from "react";
import { Calendar, Clock, Upload } from "lucide-react";
import { motion } from "framer-motion";
import { loadBootstrap } from "@/api";
import type { BootstrapPayload } from "@/types";
import { PageHeader } from "@/components/shared/PageHeader";
import { DataTable } from "@/components/shared/DataTable";
import { Badge } from "@/components/ui/Badge";

const DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"];

export default function Publish() {
  const [data, setData] = useState<BootstrapPayload | null>(null);

  useEffect(() => { loadBootstrap().then(setData).catch(console.error); }, []);

  const pm = data?.patternMemory as Record<string, unknown> | null;
  const pub = pm?.publish_memory as Record<string, unknown> | undefined;
  const weekdayRows = (pub?.weekday_rows as Record<string, unknown>[] | undefined) ?? [];
  const bestDay = String(pub?.best_day ?? "Thursday");

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader title="Publish" subtitle="Upload scheduling and best time recommendations based on your pattern memory." />

      {/* Best time hero */}
      <div className="rounded-2xl border border-[var(--color-aria-blue)]/20 bg-gradient-to-br from-[var(--color-aria-surface)] to-[var(--color-aria-surface-3)] p-6">
        <Badge color="green" dot className="mb-3">Best Window Detected</Badge>
        <h2 className="text-2xl font-black text-[var(--color-aria-ink)]">
          Upload on <span className="gradient-text">{bestDay}</span>
        </h2>
        <p className="text-sm text-[var(--color-aria-muted)] mt-1 mb-5">6:00 PM – 8:00 PM · Highest average retention for your audience.</p>
        <div className="flex gap-3 flex-wrap">
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)] text-sm">
            <Clock className="h-4 w-4 text-[var(--color-aria-blue)]" />
            <span className="text-[var(--color-aria-ink)] font-semibold">6:00 PM – 8:00 PM</span>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)] text-sm">
            <Calendar className="h-4 w-4 text-[var(--color-aria-purple)]" />
            <span className="text-[var(--color-aria-ink)] font-semibold">{bestDay}</span>
          </div>
        </div>
      </div>

      {/* Weekday heat grid */}
      <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-5">
        <p className="text-sm font-semibold text-[var(--color-aria-ink)] mb-4">Publish Timing Matrix</p>
        <div className="grid grid-cols-7 gap-2">
          {DAYS.map((day) => {
            const row = weekdayRows.find((r) => String(r.weekday) === day);
            const score = row ? Number(row.publish_score ?? 0) : 0;
            const maxScore = 300;
            const intensity = Math.min(score / maxScore, 1);
            const isBest = day === bestDay;
            return (
              <div key={day} className={`rounded-xl p-3 text-center border transition-all ${isBest ? "border-[var(--color-aria-blue)]/40 bg-[var(--color-aria-blue-dim)]" : "border-[var(--color-aria-border)] bg-[var(--color-aria-surface-3)]"}`}>
                <p className="text-[10px] font-semibold text-[var(--color-aria-muted)] mb-2">{day.slice(0, 3)}</p>
                <div className="h-12 rounded-lg flex items-end justify-center overflow-hidden bg-[var(--color-aria-bg)]">
                  <div className="w-4 rounded-t-sm transition-all" style={{ height: `${Math.max(intensity * 100, 8)}%`, background: isBest ? "var(--color-aria-blue)" : "var(--color-aria-faint)" }} />
                </div>
                <p className="text-[10px] font-mono text-[var(--color-aria-muted)] mt-1.5">{score.toFixed(0)}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Publish history */}
      <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-5">
        <div className="flex items-center gap-2 mb-4">
          <Upload className="h-4 w-4 text-[var(--color-aria-muted)]" />
          <p className="text-sm font-semibold text-[var(--color-aria-ink)]">Weekday Performance</p>
        </div>
        <DataTable
          rows={weekdayRows}
          columns={["weekday","avg_views","avg_retention","publish_score"]}
          emptyMessage="Pattern memory will populate after YouTube data is synced."
        />
      </div>
    </motion.div>
  );
}
