import { useState, useEffect } from "react";
import { Zap, RefreshCw, CheckCircle2, Send } from "lucide-react";
import { motion } from "framer-motion";
import { PageHeader } from "@/components/shared/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { loadCreatorActions, draftMetadata, publishMetadata, loadMetadata } from "@/api";
import type { CreatorActionsPayload } from "@/types";

export default function Optimize() {
  const [payload, setPayload] = useState<CreatorActionsPayload | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");
  const [draft, setDraft] = useState("");
  const [reviewed, setReviewed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");

  useEffect(() => {
    loadCreatorActions()
      .then((r) => { setPayload(r); if (r.metadataActions[0]) autoSelect(r.metadataActions[0]); })
      .catch((e: Error) => setStatus(e.message));
  }, []);

  async function autoSelect(action: CreatorActionsPayload["metadataActions"][number]) {
    setSelectedId(action.video_id);
    setTitle(action.title);
    setBusy(true);
    try {
      const meta = await loadMetadata(action.video_id);
      if (meta.metadata) {
        setTitle(String(meta.metadata.title ?? action.title));
        setDescription(String(meta.metadata.description ?? ""));
        setTags(Array.isArray(meta.metadata.tags) ? (meta.metadata.tags as string[]).join(", ") : "");
      }
      const d = await draftMetadata(action.label, `${action.reason}. ${action.suggestion}`, action.title);
      setDraft(d.content);
    } catch (e) { setStatus(e instanceof Error ? e.message : "Failed."); }
    finally { setBusy(false); }
  }

  async function handlePublish() {
    setBusy(true);
    try {
      const r = await publishMetadata({ video_id: selectedId, title, description, tags: tags.split(",").map(t => t.trim().replace(/^#/, "")).filter(Boolean), reviewed });
      setStatus(r.message);
    } catch (e) { setStatus(e instanceof Error ? e.message : "Publish failed."); }
    finally { setBusy(false); }
  }

  const selected = payload?.metadataActions.find(a => a.video_id === selectedId);

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-[var(--space-section)]">
      <PageHeader title="Optimize" subtitle="A.R.I.A. prioritizes underperforming uploads and drafts metadata improvements for review." />
      {status && <div className="rounded-xl border border-[var(--color-aria-blue)]/20 bg-[var(--color-aria-blue-dim)] px-4 py-3 text-sm text-[var(--color-aria-blue)]">{status}</div>}

      {/* Guardrails */}
      {payload?.guardrails?.length ? (
        <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-6">
          <p className="mb-[var(--space-default)] text-xs font-semibold uppercase tracking-widest text-[var(--color-aria-muted)]">Safety Guardrails</p>
          <div className="grid grid-cols-2 gap-[var(--space-block)]">
            {payload.guardrails.map(([label, value]) => (
              <div key={label} className="flex items-center gap-2 text-xs">
                <CheckCircle2 className="h-3.5 w-3.5 text-[var(--color-aria-green)] shrink-0" />
                <span className="text-[var(--color-aria-muted)]">{label}:</span>
                <span className="text-[var(--color-aria-ink)] font-semibold">{value}</span>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-[var(--space-card-grid-lg)] 2xl:grid-cols-12">
        {/* Action list */}
        <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-6 space-y-[var(--space-block)] 2xl:col-span-4">
          <p className="text-sm font-semibold text-[var(--color-aria-ink)] flex items-center gap-2">
            <Zap className="h-4 w-4 text-[var(--color-aria-amber)]" /> Metadata Actions
          </p>
          {payload?.metadataActions.length ? (
            <div className="space-y-[var(--space-tight)] max-h-[420px] overflow-y-auto pr-1">
              {payload.metadataActions.map((a) => (
                <button key={a.video_id} onClick={() => autoSelect(a)} disabled={busy}
                  className={`w-full text-left rounded-xl p-3 border transition-all ${selectedId === a.video_id ? "border-[var(--color-aria-blue)]/40 bg-[var(--color-aria-blue-dim)]" : "border-[var(--color-aria-border)] bg-[var(--color-aria-surface-3)] hover:border-[var(--color-aria-border-strong)]"}`}>
                  <p className="text-xs font-bold text-[var(--color-aria-ink)] truncate">{a.title}</p>
                  <p className="text-[10px] text-[var(--color-aria-muted)] mt-0.5">{a.reason} · {a.views.toLocaleString()} views · {Math.round(a.retention)}% ret.</p>
                  <p className="text-[10px] text-[var(--color-aria-blue)] mt-1">{a.suggestion}</p>
                </button>
              ))}
            </div>
          ) : <p className="text-sm text-[var(--color-aria-muted)]">No metadata actions loaded yet.</p>}
        </div>

        {/* Editor */}
        <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-6 space-y-[var(--space-default)] 2xl:col-span-8">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-[var(--color-aria-ink)]">Metadata Editor</p>
            {selected && <Badge color="amber" dot>{Math.round(selected.engagement_score)} score</Badge>}
          </div>
          <div className="space-y-[var(--space-block)]">
            <div>
              <label className="mb-2 block text-[10px] font-semibold uppercase tracking-widest text-[var(--color-aria-muted)]">Title</label>
              <input value={title} onChange={e => setTitle(e.target.value)} maxLength={100}
                className="w-full rounded-xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface-3)] px-4 py-3 text-sm text-[var(--color-aria-ink)] outline-none transition-colors focus:border-[var(--color-aria-blue)]" />
            </div>
            <div>
              <label className="mb-2 block text-[10px] font-semibold uppercase tracking-widest text-[var(--color-aria-muted)]">Description</label>
              <textarea value={description} onChange={e => setDescription(e.target.value)} rows={5}
                className="w-full bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)] rounded-xl px-4 py-3 text-sm text-[var(--color-aria-ink)] outline-none focus:border-[var(--color-aria-blue)] transition-colors resize-none" />
            </div>
            <div>
              <label className="mb-2 block text-[10px] font-semibold uppercase tracking-widest text-[var(--color-aria-muted)]">Tags (comma-separated)</label>
              <textarea value={tags} onChange={e => setTags(e.target.value)} rows={2}
                className="w-full bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)] rounded-xl px-4 py-3 text-sm text-[var(--color-aria-ink)] outline-none focus:border-[var(--color-aria-blue)] transition-colors resize-none" />
            </div>
            {draft && (
              <div className="rounded-xl bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)] p-3">
                <p className="text-[10px] font-semibold uppercase tracking-widest text-[var(--color-aria-blue)] mb-2">A.R.I.A. Draft Suggestion</p>
                <pre className="text-xs text-[var(--color-aria-muted)] whitespace-pre-wrap leading-relaxed">{draft}</pre>
              </div>
            )}
            <label className="flex items-center gap-2 text-xs text-[var(--color-aria-muted)] cursor-pointer">
              <input type="checkbox" checked={reviewed} onChange={e => setReviewed(e.target.checked)} className="rounded" />
              I reviewed this metadata and want to publish it.
            </label>
            <div className="flex gap-2 pt-1">
              <Button variant="secondary" size="sm" onClick={() => selected && autoSelect(selected)} disabled={busy}>
                <RefreshCw className="h-3.5 w-3.5" /> Refresh Draft
              </Button>
              <Button variant="primary" size="sm" onClick={handlePublish} disabled={!reviewed || !selectedId || busy}>
                <Send className="h-3.5 w-3.5" /> Publish
              </Button>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
