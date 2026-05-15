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
      .then((next) => {
        setPayload(next);
        setStatus("");
      })
      .catch((e: Error) => setStatus(e.message));
  }, []);

  const stats = payload?.stats ?? [];

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-[var(--space-section)]">
      <PageHeader
        title="Analyze"
        subtitle="Deep performance insights across your entire channel history."
        action={payload ? <Badge color="green" dot>{payload.source}</Badge> : null}
      />

      {status && (
        <div className="rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-[var(--color-aria-red)]">
          {status}
        </div>
      )}

      <div className="grid grid-cols-1 gap-[var(--space-card-grid)] sm:grid-cols-2 2xl:grid-cols-12">
        {stats.map((s, i) => (
          <div key={s.label} className="2xl:col-span-3">
            <MetricCard
              label={s.label}
              value={s.value}
              changeLabel={s.meta}
              color={["blue", "purple", "cyan", "green"][i % 4] as "blue"}
            />
          </div>
        ))}
      </div>

      <ChartCard
        title="Performance Trend"
        data={payload?.rows ?? []}
        summary="Track the main daily movement first, then use alerts and timing below to decide what needs attention."
      />

      <div className="grid grid-cols-1 gap-[var(--space-card-grid-lg)] 2xl:grid-cols-12">
        <div className="overflow-hidden rounded-[24px] border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-6 2xl:col-span-8">
          <div className="mb-[var(--space-default)] space-y-[var(--space-title-subtitle)]">
            <p className="text-sm font-semibold text-[var(--color-aria-ink)]">Trend Alerts</p>
            <p className="text-sm text-[var(--color-aria-muted)]">Largest spikes and dips from recent performance.</p>
          </div>
          <DataTable rows={payload?.alerts ?? []} columns={["date", "trend", "views", "retention", "ctr"]} />
        </div>

        <div className="overflow-hidden rounded-[24px] border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-6 2xl:col-span-4">
          <div className="mb-[var(--space-default)] space-y-[var(--space-title-subtitle)]">
            <p className="text-sm font-semibold text-[var(--color-aria-ink)]">Publish Timing</p>
            <p className="text-sm text-[var(--color-aria-muted)]">Average response by weekday based on available analytics.</p>
          </div>
          <DataTable rows={payload?.publishTiming ?? []} columns={["weekday", "avg_views", "avg_retention", "publish_score"]} />
        </div>
      </div>

      <div className="overflow-hidden rounded-[24px] border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-6">
        <div className="mb-[var(--space-default)] space-y-[var(--space-title-subtitle)]">
          <p className="text-sm font-semibold text-[var(--color-aria-ink)]">Channel Audit</p>
          <p className="text-sm text-[var(--color-aria-muted)]">Operational checks built from current analytics and setup state.</p>
        </div>
        <div className="grid grid-cols-1 gap-[var(--space-card-grid)] md:grid-cols-2">
          {(payload?.auditRows ?? []).map((r) => (
            <div
              key={r.label}
              className="flex items-center justify-between gap-3 rounded-xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface-3)] px-4 py-3"
            >
              <span className="text-xs text-[var(--color-aria-muted)]">{r.label}</span>
              <span className="text-xs font-bold text-[var(--color-aria-ink)]">{r.value}</span>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
