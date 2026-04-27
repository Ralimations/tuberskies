import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Bell, Eye, Users, Clock, Flame, Music2, TrendingUp } from "lucide-react";
import { loadBootstrap } from "@/api";
import type { BootstrapPayload } from "@/types";
import { MetricCard } from "@/components/shared/MetricCard";
import { NextBestAction } from "@/components/shared/NextBestAction";
import { ChartCard } from "@/components/shared/ChartCard";
import { InsightCard } from "@/components/shared/InsightCard";
import { Badge } from "@/components/ui/Badge";

// ─── mock sparklines (replaced by real data when available) ──────────────────
const MOCK_SPARKLINES = {
  views: [1800, 2100, 1950, 2600, 3100, 2800, 3400, 3200, 3800, 4100, 3700, 4500, 5200, 4900],
  subscribers: [8, 12, 9, 14, 18, 11, 16, 20, 15, 22, 19, 25, 23, 28],
  watch_time: [90, 110, 95, 130, 155, 140, 170, 160, 190, 205, 185, 225, 260, 245],
  retention: [48, 51, 47, 53, 56, 52, 58, 55, 61, 59, 63, 60, 65, 62],
};

// ─── top content mock ─────────────────────────────────────────────────────────
const TOP_CONTENT = [
  { rank: 1, title: "GRAVITY (Cover) ♬", views: "267K", retention: "60.4%" },
  { rank: 2, title: "LOSING STREAK COVER COMING SOON!", views: "73K", retention: "62.6%" },
  { rank: 3, title: "Saja Boys – Soda Pop (Cover)", views: "71K", retention: "51.1%" },
];

const stagger = {
  container: { animate: { transition: { staggerChildren: 0.07 } } },
  item: { initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0, transition: { duration: 0.35 } } },
};

export default function Dashboard() {
  const [data, setData] = useState<BootstrapPayload | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBootstrap()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // Derive display values from real data or fall back to zeroes
  const stats = data?.stats ?? [];
  const getStat = (label: string) => stats.find((s) => s.label === label);
  const analyticsRows = data?.analyticsRows ?? [];

  const views7d = getStat("Views (7D)");
  const subs7d = getStat("Subscribers (7D)");
  const watch7d = getStat("Watch Time (7D)");
  const retention = getStat("Retention (Avg.)");

  // Best publish day from patternMemory
  const pm = data?.patternMemory as Record<string, unknown> | null;
  const pubMem = pm?.publish_memory as Record<string, unknown> | undefined;
  const bestDay = String(pubMem?.best_day ?? "Thursday");
  const nbaAction = `Upload on ${bestDay} at 6:00 PM`;

  const today = data?.today;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 rounded-full gradient-btn animate-pulse" />
          <p className="text-sm text-[var(--color-aria-muted)]">A.R.I.A. is loading your creator context…</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div variants={stagger.container} initial="initial" animate="animate" className="space-y-6">
      {/* Page title */}
      <motion.div variants={stagger.item} className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-black text-[var(--color-aria-ink)] tracking-tight">
            Good evening, {data?.profile?.title ?? "Creator"} 👋
          </h1>
          <p className="text-sm text-[var(--color-aria-muted)] mt-1">
            Here&apos;s your creator command center.
          </p>
        </div>
        <button className="relative h-9 w-9 rounded-xl bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)] flex items-center justify-center text-[var(--color-aria-muted)] hover:text-[var(--color-aria-ink)] transition-colors">
          <Bell className="h-4 w-4" />
          <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full gradient-btn text-[9px] text-white flex items-center justify-center font-bold">
            3
          </span>
        </button>
      </motion.div>

      {/* Next Best Action */}
      <motion.div variants={stagger.item}>
        <NextBestAction
          action={nbaAction}
          detail="This time slot has the highest chance of strong retention based on your historical performance."
          confidence={86}
          reasons={[
            `Highest retention on ${bestDay}s`,
            "Your audience is most active",
            "Matches your best performing pattern",
            "Low competition at this time",
          ]}
        />
      </motion.div>

      {/* Metric cards */}
      <motion.div variants={stagger.item}>
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs font-semibold uppercase tracking-widest text-[var(--color-aria-muted)]">
            Overview
          </p>
          <Badge color="muted">Last 7 days</Badge>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard
            label="Views (7D)"
            value={views7d?.value ?? "—"}
            change={18.6}
            changeLabel="vs last week"
            sparklineData={MOCK_SPARKLINES.views}
            color="blue"
          />
          <MetricCard
            label="Subscribers (7D)"
            value={subs7d?.value ?? "—"}
            change={12.4}
            changeLabel="vs last week"
            sparklineData={MOCK_SPARKLINES.subscribers}
            color="purple"
          />
          <MetricCard
            label="Watch Time (7D)"
            value={watch7d?.value ?? "—"}
            change={9.7}
            changeLabel="vs last week"
            sparklineData={MOCK_SPARKLINES.watch_time}
            color="cyan"
          />
          <MetricCard
            label="Retention (Avg.)"
            value={retention?.value ?? "—"}
            change={6.3}
            changeLabel="vs last week"
            sparklineData={MOCK_SPARKLINES.retention}
            color="green"
          />
        </div>
      </motion.div>

      {/* Performance Trend + Top Content */}
      <motion.div variants={stagger.item} className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <ChartCard
            title="Performance Trend"
            data={analyticsRows.length ? analyticsRows : MOCK_CHART_DATA}
          />
        </div>
        {/* Top Content */}
        <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-5 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm font-semibold text-[var(--color-aria-ink)]">Top Content</p>
            <Badge color="muted">28D</Badge>
          </div>
          <div className="flex-1 space-y-3">
            {TOP_CONTENT.map((item) => (
              <div
                key={item.rank}
                className="flex items-start gap-3 p-3 rounded-xl bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)] hover:border-[var(--color-aria-border-strong)] transition-colors cursor-pointer"
              >
                <span className="text-xs font-black text-[var(--color-aria-faint)] w-4 shrink-0 mt-0.5">
                  {item.rank}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-[var(--color-aria-ink)] leading-snug truncate">
                    {item.title}
                  </p>
                  <p className="text-[10px] text-[var(--color-aria-muted)] mt-1">
                    {item.views} views · {item.retention} retention
                  </p>
                </div>
              </div>
            ))}
          </div>
          <button className="mt-4 text-xs text-[var(--color-aria-blue)] font-semibold hover:opacity-70 transition-opacity text-center">
            View All Content →
          </button>
        </div>
      </motion.div>

      {/* Today brief */}
      {today && (
        <motion.div variants={stagger.item} className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <InsightCard
            icon={TrendingUp}
            title="Improve Retention"
            body={today.focus_reason || "Strengthen your intro hook to boost retention in the first 30 seconds."}
            cta="See Analysis"
            color="blue"
          />
          <InsightCard
            icon={Clock}
            title={`Best Day to Upload: ${bestDay}`}
            body="6:00 PM – 8:00 PM is your peak engagement window based on pattern memory."
            cta="View All Time Slots"
            color="purple"
          />
          <InsightCard
            icon={Flame}
            title="Content Opportunity"
            body={today.opportunity_reason || "Cinematic covers are performing above average in your niche right now."}
            cta="Explore Ideas"
            color="amber"
          />
        </motion.div>
      )}
    </motion.div>
  );
}

// ─── Mock data for chart when no real data ────────────────────────────────────
const MOCK_CHART_DATA = Array.from({ length: 28 }, (_, i) => {
  const d = new Date();
  d.setDate(d.getDate() - (27 - i));
  return {
    date: d.toISOString().slice(0, 10),
    views: Math.round(20000 + Math.sin(i / 3) * 8000 + Math.random() * 4000),
    watch_time_hours: Math.round(800 + Math.sin(i / 4) * 200 + Math.random() * 100),
    retention: Math.round(55 + Math.sin(i / 5) * 8 + Math.random() * 3),
    subscribers_gained: Math.round(30 + Math.sin(i / 3) * 12 + Math.random() * 8),
  };
});
