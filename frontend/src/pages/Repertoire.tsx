import { useEffect, useState } from "react";
import { Music2, Eye, Clock, Percent } from "lucide-react";
import { motion } from "framer-motion";
import { loadBootstrap } from "@/api";
import type { BootstrapPayload } from "@/types";
import { PageHeader } from "@/components/shared/PageHeader";
import { DataTable } from "@/components/shared/DataTable";
import { Badge } from "@/components/ui/Badge";

export default function Repertoire() {
  const [data, setData] = useState<BootstrapPayload | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => { loadBootstrap().then(setData).catch(console.error); }, []);

  const rows = data?.videoRows ?? [];
  const sorted = [...rows].sort((a, b) => Number(b.engagement_score ?? 0) - Number(a.engagement_score ?? 0));
  const filtered = search
    ? sorted.filter((r) => String(r.title ?? "").toLowerCase().includes(search.toLowerCase()))
    : sorted;

  const best = sorted[0];
  const weak = sorted[sorted.length - 1];

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader
        title="Repertoire"
        subtitle="Your complete upload library ranked by engagement performance."
        action={<Badge color="muted">{rows.length} videos</Badge>}
      />

      {/* Best / Weakest */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {best && (
          <VideoHighlight label="Top Performer" video={best} color="green" icon={Eye} />
        )}
        {weak && (
          <VideoHighlight label="Needs Attention" video={weak} color="amber" icon={Clock} />
        )}
      </div>

      {/* Search + Table */}
      <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-5 space-y-4">
        <div className="flex items-center gap-3">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search videos…"
            className="flex-1 bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)] rounded-xl px-4 py-2.5 text-sm text-[var(--color-aria-ink)] placeholder:text-[var(--color-aria-faint)] outline-none focus:border-[var(--color-aria-blue)] transition-colors"
          />
          <Badge color="muted">{filtered.length} results</Badge>
        </div>
        <DataTable
          rows={filtered}
          columns={["title", "views", "retention", "watch_time_hours", "engagement_score"]}
          emptyMessage="No videos loaded. Connect YouTube to sync your upload history."
        />
      </div>
    </motion.div>
  );
}

function VideoHighlight({
  label,
  video,
  color,
  icon: Icon,
}: {
  label: string;
  video: Record<string, unknown>;
  color: "green" | "amber";
  icon: typeof Eye;
}) {
  const colorMap = {
    green: { badge: "green" as const, accent: "text-[var(--color-aria-green)]", border: "border-[var(--color-aria-green-dim)]" },
    amber: { badge: "amber" as const, accent: "text-[var(--color-aria-amber)]", border: "border-amber-500/15" },
  };
  const c = colorMap[color];

  return (
    <div className={`rounded-2xl border ${c.border} bg-[var(--color-aria-surface)] p-5`}>
      <Badge color={c.badge} className="mb-3">{label}</Badge>
      <p className="text-sm font-bold text-[var(--color-aria-ink)] mb-3 leading-snug">
        {String(video.title ?? "Untitled Video")}
      </p>
      <div className="grid grid-cols-3 gap-3">
        <Stat icon={Eye} label="Views" value={Number(video.views ?? 0).toLocaleString()} accent={c.accent} />
        <Stat icon={Percent} label="Retention" value={`${Number(video.retention ?? 0).toFixed(1)}%`} accent={c.accent} />
        <Stat icon={Clock} label="Watch Time" value={`${Math.round(Number(video.watch_time_hours ?? 0))}h`} accent={c.accent} />
      </div>
    </div>
  );
}

function Stat({ icon: Icon, label, value, accent }: { icon: typeof Eye; label: string; value: string; accent: string }) {
  return (
    <div className="flex flex-col gap-1">
      <Icon className={`h-3.5 w-3.5 ${accent}`} />
      <p className="text-xs font-bold text-[var(--color-aria-ink)]">{value}</p>
      <p className="text-[10px] text-[var(--color-aria-muted)]">{label}</p>
    </div>
  );
}
