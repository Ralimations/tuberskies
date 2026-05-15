import { motion } from "framer-motion";
import { Bell, Clock3, Flame, TrendingUp, ImageIcon, WandSparkles } from "lucide-react";
import { useBootstrap } from "@/context/BootstrapContext";
import { MetricCard } from "@/components/shared/MetricCard";
import { NextBestAction } from "@/components/shared/NextBestAction";
import { ChartCard } from "@/components/shared/ChartCard";
import { InsightCard } from "@/components/shared/InsightCard";
import { Badge } from "@/components/ui/Badge";

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
  const videoRows = data?.videoRows ?? [];
  const topContentRows = videoRows.length ? videoRows.slice(0, 3) : TOP_CONTENT;

  const views7d = getStat("Views (7D)");
  const subs7d = getStat("Subscribers (7D)");
  const watch7d = getStat("Watch Time (7D)");
  const retention = getStat("Retention (Avg.)");

  const pm = data?.patternMemory as Record<string, unknown> | null;
  const pubMem = pm?.publish_memory as Record<string, unknown> | undefined;
  const bestDay = String(pubMem?.best_day ?? "Thursday");
  const nextAction = `Upload on ${bestDay} at 6:00 PM`;
  const today = data?.today;

  const chartRows = analyticsRows.length ? analyticsRows : MOCK_CHART_DATA;
  const peakRow = [...chartRows]
    .map((row) => ({ date: String(row.date ?? ""), views: Number(row.views ?? 0) }))
    .sort((a, b) => b.views - a.views)[0];
  const latestRow = chartRows[chartRows.length - 1];
  const previousRow = chartRows[chartRows.length - 2];
  const direction =
    latestRow && previousRow && Number(latestRow.views ?? 0) >= Number(previousRow.views ?? 0) ? "up" : "down";

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
    <motion.div variants={stagger.container} initial="initial" animate="animate" className="mx-auto max-w-[1280px] space-y-[var(--space-section)]">
      <motion.div variants={stagger.item} className="rounded-[28px] bg-white/4 p-8">
        <div className="flex items-start justify-between gap-4">
          <div className="max-w-3xl space-y-[var(--space-block)] pl-0.5">
            <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[var(--color-aria-faint)]">Daily focus</p>
            <h1 className="text-4xl font-semibold leading-[1.08] tracking-[-0.02em] text-[var(--color-aria-ink)] xl:text-5xl">
              Good evening, {data?.profile?.title ?? "Creator"}
            </h1>
            <p className="max-w-2xl text-base leading-7 text-[var(--color-aria-muted)]">
              One goal today: push the next upload toward a stronger launch. The dashboard below is organized around that decision.
            </p>
            <div className="flex flex-wrap items-center gap-2 pt-2">
              <Badge color="blue">Act on one priority</Badge>
              <Badge color="cyan">Fresh channel data</Badge>
              <Badge color="muted">Last 30 days in view</Badge>
            </div>
          </div>
          <button className="relative flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-[var(--color-aria-border)] bg-white/6 text-[var(--color-aria-muted)] transition-colors hover:text-[var(--color-aria-ink)]">
            <Bell className="h-4 w-4" />
          </button>
        </div>
      </motion.div>

      <motion.div variants={stagger.item}>
        <NextBestAction
          action={nextAction}
          detail="Your recent performance supports publishing in this window. Use it for the strongest near-ready upload rather than spending it on an average release."
          confidence={86}
          reasons={[
            `Retention is strongest on ${bestDay}.`,
            "This is your cleanest action with the highest short-term upside.",
            "Audience activity and prior performance line up here.",
          ]}
        />
      </motion.div>

      <motion.div variants={stagger.item} className="grid grid-cols-1 items-stretch gap-[var(--space-card-grid)] md:grid-cols-2 xl:grid-cols-12">
        <div className="xl:col-span-6 2xl:col-span-3">
          <MetricCard
          label="Views (7D)"
          value={views7d?.value ?? "-"}
          change={18.6}
          changeLabel="Demand is improving"
          color="blue"
          detail="Reach is climbing. This is the time to double down on the packaging pattern that caused the spike."
        />
        </div>
        <div className="xl:col-span-6 2xl:col-span-3">
          <MetricCard
          label="Subscribers (7D)"
          value={subs7d?.value ?? "-"}
          change={12.4}
          changeLabel="More viewers are converting"
          color="purple"
          detail="Subscriber pickup is healthy. Preserve the same title promise if this was driven by one standout upload."
        />
        </div>
        <div className="xl:col-span-6 2xl:col-span-3">
          <MetricCard
          label="Watch Time (7D)"
          value={watch7d?.value ?? "-"}
          change={9.7}
          changeLabel="Session depth is rising"
          color="cyan"
          detail="People are staying longer. Test a stronger second beat rather than changing the whole format."
        />
        </div>
        <div className="xl:col-span-6 2xl:col-span-3">
          <MetricCard
          label="Retention (Avg.)"
          value={retention?.value ?? "-"}
          change={6.3}
          changeLabel="Audience hold is stronger"
          color="green"
          detail="Retention is moving in the right direction. The next win is to tighten the opening even more."
        />
        </div>
      </motion.div>

      <motion.div variants={stagger.item} className="grid grid-cols-1 items-stretch gap-[var(--space-card-grid)] xl:grid-cols-12">
        <div className="xl:col-span-8">
          <ChartCard
          title="Performance trend"
          data={chartRows}
          summary={
            direction === "up"
              ? "The latest data is stabilizing after a spike. Look for which title, topic, or upload slot caused the jump and repeat that specific move."
              : "The spike has cooled. Use the best-performing upload as the baseline and compare the drop-off to your weaker follow-ups."
          }
          annotation={peakRow ? { date: peakRow.date, label: "Peak day" } : null}
        />
        </div>

        <div className="xl:col-span-4">
          <div className="flex h-full flex-col rounded-[28px] bg-white/4 p-6">
          <div className="mb-[var(--space-default)] flex items-center justify-between gap-3">
            <div className="min-w-0 space-y-[var(--space-title-subtitle)]">
              <p className="text-lg font-semibold text-[var(--color-aria-ink)]">Top content</p>
              <p className="text-sm leading-6 text-[var(--color-aria-muted)]">Use these as templates, not trophies.</p>
            </div>
            <Badge color="muted">Quick actions</Badge>
          </div>
          <div className="flex-1 space-y-[var(--space-card-grid)]">
            {topContentRows.map((item: any, idx: number) => {
              const title = item.title || item.title;
              const views = typeof item.views === "number" ? `${(item.views / 1000).toFixed(1)}K` : item.views;
              const retentionStr = item.retention !== undefined ? `${item.retention}%` : item.retention;

              return (
                <div key={item.video_id || idx} className="rounded-[22px] bg-white/6 p-6">
                  <div className="flex items-stretch gap-3">
                    <div className="flex h-16 w-24 shrink-0 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,rgba(79,110,247,0.22),rgba(94,234,212,0.14))] text-[var(--color-aria-blue)]">
                      <ImageIcon className="h-5 w-5" />
                    </div>
                    <div className="flex min-w-0 flex-1 flex-col">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="mb-[var(--space-title-subtitle)] line-clamp-2 text-sm font-semibold leading-5 text-[var(--color-aria-ink)]">{title}</p>
                          <p className="line-clamp-2 text-xs leading-5 text-[var(--color-aria-muted)]">
                            {views} views - {retentionStr} retention
                          </p>
                        </div>
                        <span className="rounded-full bg-[var(--color-aria-blue-dim)] px-2 py-1 text-[10px] font-semibold text-[var(--color-aria-blue)]">
                          #{idx + 1}
                        </span>
                      </div>
                      <div className="mt-[var(--space-default)] flex flex-wrap gap-[var(--space-block)] pt-[var(--space-default)]">
                        <button className="rounded-full border border-[var(--color-aria-border)] bg-white/5 px-3 py-1 text-xs text-[var(--color-aria-ink)]">
                          Reuse angle
                        </button>
                        <button className="rounded-full border border-[var(--color-aria-border)] bg-white/5 px-3 py-1 text-xs text-[var(--color-aria-ink)]">
                          Analyze
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        </div>
      </motion.div>

      {today && (
        <motion.div variants={stagger.item} className="grid grid-cols-1 items-stretch gap-[var(--space-card-grid)] md:grid-cols-2 xl:grid-cols-12">
          <div className="xl:col-span-4">
            <InsightCard
            icon={TrendingUp}
            title="Fix the first weak point"
            body={today.focus_reason || "Strengthen your intro hook to boost retention in the first 30 seconds."}
            cta="Open analysis"
            color="blue"
          />
          </div>
          <div className="xl:col-span-4">
            <InsightCard
            icon={Clock3}
            title={`Reserve ${bestDay} for your best upload`}
            body="That window is currently your best bet. Do not spend it on a filler release."
            cta="Review timing"
            color="purple"
          />
          </div>
          <div className="md:col-span-2 xl:col-span-4">
            <InsightCard
            icon={Flame}
            title="Push the winning content lane"
            body={today.opportunity_reason || "Cinematic covers are performing above average in your niche right now."}
            cta="Explore ideas"
            color="amber"
          />
          </div>
        </motion.div>
      )}

      <motion.div variants={stagger.item} className="rounded-[28px] bg-white/4 p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[var(--color-aria-cyan-dim)] text-[var(--color-aria-cyan)]">
            <WandSparkles className="h-5 w-5" />
          </div>
          <div className="min-w-0 space-y-[var(--space-title-subtitle)]">
            <p className="text-lg font-semibold text-[var(--color-aria-ink)]">What to do next</p>
            <p className="text-sm text-[var(--color-aria-muted)]">Three practical moves based on what the dashboard is showing right now.</p>
          </div>
        </div>
        <div className="mt-6 grid grid-cols-1 items-stretch gap-[var(--space-card-grid)] xl:grid-cols-12">
          <div className="flex h-full flex-col rounded-[22px] bg-white/5 p-6 xl:col-span-4">
            <p className="mb-[var(--space-title-subtitle)] text-sm font-semibold text-[var(--color-aria-ink)]">1. Repeat the winning promise</p>
            <p className="mb-[var(--space-block)] line-clamp-3 text-sm leading-6 text-[var(--color-aria-muted)]">Start the next title or concept from the top performer instead of inventing a new frame from scratch.</p>
            <div className="mt-auto pt-[var(--space-default)]">
              <p className="text-xs font-medium text-[var(--color-aria-faint)]">Use the current top performer as the baseline.</p>
            </div>
          </div>
          <div className="flex h-full flex-col rounded-[22px] bg-white/5 p-6 xl:col-span-4">
            <p className="mb-[var(--space-title-subtitle)] text-sm font-semibold text-[var(--color-aria-ink)]">2. Tighten the first 30 seconds</p>
            <p className="mb-[var(--space-block)] line-clamp-3 text-sm leading-6 text-[var(--color-aria-muted)]">Retention is the leverage point. Improve the intro before changing production style or schedule.</p>
            <div className="mt-auto pt-[var(--space-default)]">
              <p className="text-xs font-medium text-[var(--color-aria-faint)]">Fix the opening before changing the format.</p>
            </div>
          </div>
          <div className="flex h-full flex-col rounded-[22px] bg-white/5 p-6 xl:col-span-4">
            <p className="mb-[var(--space-title-subtitle)] text-sm font-semibold text-[var(--color-aria-ink)]">3. Publish in the proven slot</p>
            <p className="mb-[var(--space-block)] line-clamp-3 text-sm leading-6 text-[var(--color-aria-muted)]">Use your best timing window intentionally. Save it for the upload with the strongest packaging.</p>
            <div className="mt-auto pt-[var(--space-default)]">
              <p className="text-xs font-medium text-[var(--color-aria-faint)]">Reserve high-performing slots for strong packaging.</p>
            </div>
          </div>
        </div>
      </motion.div>
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
