import { useEffect, useState } from "react";
import { Brain, Repeat2, TrendingDown, Tag } from "lucide-react";
import { motion } from "framer-motion";
import { loadBootstrap } from "@/api";
import type { BootstrapPayload } from "@/types";
import { PageHeader } from "@/components/shared/PageHeader";
import { Badge } from "@/components/ui/Badge";

export default function Learn() {
  const [data, setData] = useState<BootstrapPayload | null>(null);

  useEffect(() => { loadBootstrap().then(setData).catch(console.error); }, []);

  const pm = data?.patternMemory as Record<string, unknown> | null;
  const repeatMore = (pm?.repeat_more as string[] | undefined) ?? [];
  const reduceOrFix = (pm?.reduce_or_fix as string[] | undefined) ?? [];
  const titlePatterns = (pm?.title_patterns as Record<string, unknown>[] | undefined) ?? [];
  const generatedAt = String(pm?.generated_at ?? "");

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader
        title="A.R.I.A. Memory"
        subtitle="The patterns A.R.I.A. remembers so advice stays consistent, not generic."
        action={generatedAt && <Badge color="muted">Updated {generatedAt.slice(0, 10)}</Badge>}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Repeat More */}
        <div className="rounded-2xl border border-[var(--color-aria-green-dim)] bg-[var(--color-aria-surface)] p-5">
          <div className="flex items-center gap-2 mb-4">
            <div className="h-8 w-8 rounded-lg bg-[var(--color-aria-green-dim)] flex items-center justify-center">
              <Repeat2 className="h-4 w-4 text-[var(--color-aria-green)]" />
            </div>
            <p className="text-sm font-semibold text-[var(--color-aria-ink)]">Repeat More</p>
          </div>
          {repeatMore.length ? (
            <ul className="space-y-3">
              {repeatMore.map((item) => (
                <li key={item} className="flex items-start gap-2.5 text-sm">
                  <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-[var(--color-aria-green)] shrink-0" />
                  <span className="text-[var(--color-aria-muted)]">{item}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-[var(--color-aria-muted)]">Pattern memory will populate after your first analytics sync.</p>
          )}
        </div>

        {/* Reduce or Fix */}
        <div className="rounded-2xl border border-red-500/15 bg-[var(--color-aria-surface)] p-5">
          <div className="flex items-center gap-2 mb-4">
            <div className="h-8 w-8 rounded-lg bg-red-500/10 flex items-center justify-center">
              <TrendingDown className="h-4 w-4 text-[var(--color-aria-red)]" />
            </div>
            <p className="text-sm font-semibold text-[var(--color-aria-ink)]">Reduce or Fix</p>
          </div>
          {reduceOrFix.length ? (
            <ul className="space-y-3">
              {reduceOrFix.map((item) => (
                <li key={item} className="flex items-start gap-2.5 text-sm">
                  <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-[var(--color-aria-red)] shrink-0" />
                  <span className="text-[var(--color-aria-muted)]">{item}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-[var(--color-aria-muted)]">No issues detected yet.</p>
          )}
        </div>
      </div>

      {/* Title Patterns */}
      <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-5">
        <div className="flex items-center gap-2 mb-4">
          <Tag className="h-4 w-4 text-[var(--color-aria-blue)]" />
          <p className="text-sm font-semibold text-[var(--color-aria-ink)]">Title Patterns</p>
        </div>
        {titlePatterns.length ? (
          <div className="flex flex-wrap gap-2">
            {titlePatterns.map((p) => (
              <div key={String(p.pattern)} className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)]">
                <span className="text-xs font-semibold text-[var(--color-aria-ink)]">{String(p.pattern)}</span>
                <span className="text-[10px] text-[var(--color-aria-muted)]">×{String(p.count)}</span>
                <Badge color={String(p.type) === "phrase" ? "purple" : "blue"} className="text-[9px] px-1.5 py-0">{String(p.type)}</Badge>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-[var(--color-aria-muted)]">Title patterns load after upload history is synced.</p>
        )}
      </div>

      {/* Empty memory hint */}
      {!pm && (
        <div className="flex items-center gap-3 rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-6">
          <Brain className="h-8 w-8 text-[var(--color-aria-faint)] shrink-0" />
          <div>
            <p className="text-sm font-semibold text-[var(--color-aria-ink)]">No memory snapshot yet</p>
            <p className="text-xs text-[var(--color-aria-muted)] mt-1">Connect YouTube and sync data to let A.R.I.A. start building your creator memory.</p>
          </div>
        </div>
      )}
    </motion.div>
  );
}
