import { motion } from "framer-motion";
import { Bell, Clock, Flame, TrendingUp } from "lucide-react";
import { useBootstrap } from "@/context/BootstrapContext";
import { MetricCard } from "@/components/shared/MetricCard";
import { NextBestAction } from "@/components/shared/NextBestAction";
import { ChartCard } from "@/components/shared/ChartCard";
import { InsightCard } from "@/components/shared/InsightCard";
import { Badge } from "@/components/ui/Badge";

const MOCK_SPARKLINES = {
  views: [1800, 2100, 1950, 2600, 3100, 2800, 3400, 3200, 3800, 4100, 3700, 4500, 5200, 4900],
  subscribers: [8, 12, 9, 14, 18, 11, 16, 20, 15, 22, 19, 25, 23, 28],
  watch_time: [90, 110, 95, 130, 155, 140, 170, 160, 190, 205, 185, 225, 260, 245],
  retention: [48, 51, 47, 53, 56, 52, 58, 55, 61, 59, 63, 60, 65, 62],
};

const TOP_CONTENT = [
  { rank: 1, title: "GRAVITY (Cover)", views: "267K", retention: "60.4%" },
  { rank: 2, title: "LOSING STREAK COVER COMING SOON!", views: "73K", retention: "62.6%" },
  { rank: 3, title: "Saja Boys - Soda Pop (Cover)", views: "71K", retention: "51.1%" },
];

const stagger = {
  container: { animate: { transition: { staggerChildren: 0.07 } } },
  item: { initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0, transition: { duration: 0.35 } } },
};

export default function Dashboard() {
  const { data, loading } = useBootstrap();

  const stats = data?.stats ?? [];
  const getStat = (label: string) => stats.find((s) => s.label === label);
  const analyticsRows = data?.analyticsRows ?? [];

  const views7d = getStat("Views (7D)");
  const subs7d = getStat("Subscribers (7D)");
  const watch7d = getStat("Watch Time (7D)");
  const retention = getStat("Retention (Avg.)");

  const pm = data?.patternMemory as Record<string, unknown> | null;
  const pubMem = pm?.publish_memory as Record<string, unknown> | undefined;
  const bestDay = String(pubMem?.best_day ?? "Thursday");
  const nextAction = `Upload on ${bestDay} at 6:00 PM`;

  const today = data?.today;

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="gradient-btn h-8 w-8 animate-pulse rounded-full" />
          <p className="text-sm text-[var(--color-aria-muted)]">A.R.I.A. is loading your creator context...</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div variants={stagger.container} initial="initial" animate="animate" className="space-y-6">
      <motion.div variants={stagger.item} className="rounded-[28px] border border-[var(--color-aria-border)] bg-white/4 p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="max-w-2xl">
            <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[var(--color-aria-faint)]">
              Daily command center
            </p>
            <h1 className="mt-2 text-4xl font-semibold tracking-[-0.04em] text-[var(--color-aria-ink)]">
              Good evening, {data?.profile?.title ?? "Creator"}
            </h1>
            <p className="mt-3 text-sm leading-6 text-[var(--color-aria-muted)]">
              Your dashboard is tuned for the next upload window, the strongest signal, and where attention is climbing.
            </p>
          </div>
          <button className="relative flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-[var(--color-aria-border)] bg-white/6 text-[var(--color-aria-muted)] transition-colors hover:text-[var(--color-aria-ink)]">
            <Bell className="h-4 w-4" />
            <span className="absolute right-0 top-0 flex h-5 w-5 items-center justify-center rounded-full bg-[var(--color-aria-cyan)] text-[10px] font-bold text-slate-950">
              3
            </span>
          </button>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-2">
          <Badge color="blue">Performance-led</Badge>
          <Badge color="cyan">Audience timing aware</Badge>
          <Badge color="muted">Last 7 days</Badge>
        </div>
      </motion.div>

      <motion.div variants={stagger.item}>
        <NextBestAction
          action={nextAction}
          detail="This slot lines up with your strongest retention history and the best chance of converting interest into sustained watch time."
          confidence={86}
          reasons={[
            `Highest retention on ${bestDay}s`,
            "Audience activity peaks in this window",
            "Matches your best recurring pattern",
            "Lower competition pressure at publish time",
          ]}
        />
      </motion.div>

      <motion.div variants={stagger.item} className="rounded-[28px] border border-[var(--color-aria-border)] bg-white/4 p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[var(--color-aria-faint)]">
              Overview
            </p>
            <p className="mt-1 text-sm text-[var(--color-aria-muted)]">Momentum across views, subs, watch time, and retention.</p>
          </div>
          <Badge color="muted">Last 7 days</Badge>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Views (7D)" value={views7d?.value ?? "-"} change={18.6} changeLabel="vs last week" sparklineData={MOCK_SPARKLINES.views} color="blue" />
          <MetricCard label="Subscribers (7D)" value={subs7d?.value ?? "-"} change={12.4} changeLabel="vs last week" sparklineData={MOCK_SPARKLINES.subscribers} color="purple" />
          <MetricCard label="Watch Time (7D)" value={watch7d?.value ?? "-"} change={9.7} changeLabel="vs last week" sparklineData={MOCK_SPARKLINES.watch_time} color="cyan" />
          <MetricCard label="Retention (Avg.)" value={retention?.value ?? "-"} change={6.3} changeLabel="vs last week" sparklineData={MOCK_SPARKLINES.retention} color="green" />
        </div>
      </motion.div>

      <motion.div variants={stagger.item} className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <ChartCard title="Performance Trend" data={analyticsRows.length ? analyticsRows : MOCK_CHART_DATA} />
        </div>
        <div className="rounded-[28px] border border-[var(--color-aria-border)] bg-white/4 p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-[var(--color-aria-ink)]">Top content</p>
              <p className="mt-1 text-xs text-[var(--color-aria-muted)]">Best recent performers by reach and retention.</p>
            </div>
            <Badge color="muted">28D</Badge>
          </div>
          <div className="space-y-3">
            {(data?.videoRows?.slice(0, 3) || TOP_CONTENT).map((item: any, idx: number) => {
              const title = item.title || item.title;
              const views = item.views !== undefined ? `${(item.views / 1000).toFixed(1)}K` : item.views;
              const retentionStr = item.retention !== undefined ? `${item.retention}%` : item.retention;

              return (
                <div
                  key={item.video_id || idx}
                  className="rounded-[22px] border border-[var(--color-aria-border)] bg-white/6 p-4 transition-colors hover:border-[var(--color-aria-border-strong)]"
                >
                  <div className="flex items-start gap-3">
                    <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--color-aria-blue-dim)] text-xs font-bold text-[var(--color-aria-blue)]">
                      {idx + 1}
                    </span>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-[var(--color-aria-ink)]">{title}</p>
                      <p className="mt-1 text-xs text-[var(--color-aria-muted)]">
                        {views} views · {retentionStr} retention
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          <button className="mt-4 text-sm font-semibold text-[var(--color-aria-blue)] transition-opacity hover:opacity-75">
            View all content →
          </button>
        </div>
      </motion.div>

      {today && (
        <motion.div variants={stagger.item} className="grid grid-cols-1 gap-3 lg:grid-cols-3">
          <InsightCard
            icon={TrendingUp}
            title="Improve retention"
            body={today.focus_reason || "Strengthen your intro hook to boost retention in the first 30 seconds."}
            cta="See analysis"
            color="blue"
          />
          <InsightCard
            icon={Clock}
            title={`Best day to upload: ${bestDay}`}
            body="6:00 PM - 8:00 PM is your peak engagement window based on pattern memory."
            cta="View time slots"
            color="purple"
          />
          <InsightCard
            icon={Flame}
            title="Content opportunity"
            body={today.opportunity_reason || "Cinematic covers are performing above average in your niche right now."}
            cta="Explore ideas"
            color="amber"
          />
        </motion.div>
      )}
    </motion.div>
  );
}

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
