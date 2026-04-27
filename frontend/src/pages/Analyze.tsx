import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { loadAnalytics } from "@/api";
import type { AnalyticsPayload } from "@/types";
import { PageHeader } from "@/components/shared/PageHeader";
import { ChartCard } from "@/components/shared/ChartCard";
import { MetricCard } from "@/components/shared/MetricCard";
import { DataTable } from "@/components/shared/DataTable";
import { Badge } from "@/components/ui/Badge";

export default function Analyze() {
  const [payload, setPayload] = useState<AnalyticsPayload | null>(null);
  const [status, setStatus] = useState("");

  useEffect(() => {
    loadAnalytics()
      .then(setPayload)
      .catch((e: Error) => setStatus(e.message));
  }, []);

  const stats = payload?.stats ?? [];

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader
        title="Analyze"
        subtitle="Deep performance insights across your entire channel history."
        action={payload && <Badge color="green" dot>{payload.source}</Badge>}
      />
      {status && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-[var(--color-aria-red)]">{status}</div>
      )}

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {stats.map((s, i) => (
          <MetricCard key={s.label} label={s.label} value={s.value} changeLabel={s.meta}
            color={["blue","purple","cyan","green"][i % 4] as "blue"} />
        ))}
      </div>

      {/* Chart */}
      <ChartCard title="Performance Trend" data={payload?.rows ?? []} />

      {/* Two-col: alerts + timing */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-5">
          <p className="text-sm font-semibold text-[var(--color-aria-ink)] mb-4">Trend Alerts</p>
          <DataTable rows={payload?.alerts ?? []} columns={["date","trend","views","retention","ctr"]} />
        </div>
        <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-5">
          <p className="text-sm font-semibold text-[var(--color-aria-ink)] mb-4">Publish Timing</p>
          <DataTable rows={payload?.publishTiming ?? []} columns={["weekday","avg_views","avg_retention","publish_score"]} />
        </div>
      </div>

      {/* Audit */}
      <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-5">
        <p className="text-sm font-semibold text-[var(--color-aria-ink)] mb-4">Channel Audit</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {(payload?.auditRows ?? []).map((r) => (
            <div key={r.label} className="flex justify-between items-center py-2.5 px-3 rounded-xl bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)]">
              <span className="text-xs text-[var(--color-aria-muted)]">{r.label}</span>
              <span className="text-xs font-bold text-[var(--color-aria-ink)]">{r.value}</span>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
