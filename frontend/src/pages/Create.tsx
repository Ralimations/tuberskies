import { useState } from "react";
import { Sparkles, Wand2, Target, FileText } from "lucide-react";
import { motion } from "framer-motion";
import { PageHeader } from "@/components/shared/PageHeader";
import { Button } from "@/components/ui/Button";
import { generateIdeation, scoreIdeation } from "@/api";
import type { IdeationScorePayload } from "@/types";

const ACTIONS = [
  { key: "title_pack", label: "Title & Packaging" },
  { key: "hook_write", label: "Hook Writer" },
  { key: "concept_expand", label: "Concept Expander" },
  { key: "niche_spin", label: "Niche Spin" },
];

export default function Create() {
  const [topic, setTopic] = useState("");
  const [workingTitle, setWorkingTitle] = useState("");
  const [action, setAction] = useState("title_pack");
  const [output, setOutput] = useState("");
  const [score, setScore] = useState<IdeationScorePayload>({ keywords: [], scorecard: [] });
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");

  async function handleGenerate() {
    if (!topic.trim()) return;
    setBusy(true);
    setStatus("A.R.I.A. is ideating…");
    try {
      const result = await generateIdeation({ topic, working_title: workingTitle, action });
      setOutput(result.content);
      setStatus("");
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Generation failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleScore() {
    if (!topic.trim() && !workingTitle.trim()) return;
    try {
      const result = await scoreIdeation(topic, workingTitle);
      setScore(result);
    } catch {/* silent */}
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-[var(--space-section)]">
      <PageHeader
        title="Create"
        subtitle="Develop song concepts, covers, and ideas into stronger theatrical plans."
        action={
          <Button variant="primary" onClick={handleGenerate} disabled={busy}>
            <Sparkles className="h-4 w-4" />
            {busy ? "Generating…" : "Ask A.R.I.A."}
          </Button>
        }
      />

      {status && (
        <div className="rounded-xl border border-[var(--color-aria-blue)]/20 bg-[var(--color-aria-blue-dim)] px-4 py-3 text-sm text-[var(--color-aria-blue)]">
          {status}
        </div>
      )}

      <div className="grid grid-cols-1 gap-[var(--space-card-grid-lg)] 2xl:grid-cols-12">
        {/* Concept Builder */}
        <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-6 space-y-[var(--space-default)] 2xl:col-span-8">
          <p className="text-sm font-semibold text-[var(--color-aria-ink)] flex items-center gap-2">
            <Target className="h-4 w-4 text-[var(--color-aria-blue)]" /> Concept Builder
          </p>
          <div className="space-y-[var(--space-block)]">
            <div>
              <label className="mb-2 block text-xs font-semibold text-[var(--color-aria-muted)]">
                Song concept, niche direction, or cover idea
              </label>
              <textarea
                value={topic}
                onChange={(e) => { setTopic(e.target.value); handleScore(); }}
                rows={5}
                placeholder="Male version of Pretty Little Baby with a softer Broadway ballad treatment…"
                className="w-full bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)] rounded-xl px-4 py-3 text-sm text-[var(--color-aria-ink)] placeholder:text-[var(--color-aria-faint)] outline-none focus:border-[var(--color-aria-blue)] transition-colors resize-none"
              />
            </div>
            <div>
              <label className="mb-2 block text-xs font-semibold text-[var(--color-aria-muted)]">
                Working title
              </label>
              <input
                value={workingTitle}
                onChange={(e) => { setWorkingTitle(e.target.value); handleScore(); }}
                placeholder="Pretty Little Baby (Male Version)"
                className="w-full bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)] rounded-xl px-4 py-3 text-sm text-[var(--color-aria-ink)] placeholder:text-[var(--color-aria-faint)] outline-none focus:border-[var(--color-aria-blue)] transition-colors"
              />
            </div>
            <div>
              <label className="mb-2 block text-xs font-semibold text-[var(--color-aria-muted)]">
                Generation mode
              </label>
              <select
                value={action}
                onChange={(e) => setAction(e.target.value)}
                className="w-full bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)] rounded-xl px-4 py-3 text-sm text-[var(--color-aria-ink)] outline-none focus:border-[var(--color-aria-blue)] transition-colors"
              >
                {ACTIONS.map((a) => <option key={a.key} value={a.key}>{a.label}</option>)}
              </select>
            </div>
          </div>
        </div>

        {/* Scorecard */}
        <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-6 space-y-[var(--space-default)] 2xl:col-span-4">
          <p className="text-sm font-semibold text-[var(--color-aria-ink)] flex items-center gap-2">
            <Wand2 className="h-4 w-4 text-[var(--color-aria-purple)]" /> Keyword & Packaging Desk
          </p>
          {score.scorecard.length ? (
            <div className="space-y-[var(--space-tight)]">
              {score.scorecard.map((item) => (
                <div key={item.label} className="flex justify-between items-center py-2 border-b border-[var(--color-aria-border)] last:border-0">
                  <span className="text-xs text-[var(--color-aria-muted)]">{item.label}</span>
                  <span className="text-xs font-bold text-[var(--color-aria-ink)]">{item.value}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[var(--color-aria-muted)]">Add a topic or title to score packaging strength.</p>
          )}
        </div>
      </div>

      {/* Output */}
      {output && (
        <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-6">
          <p className="text-sm font-semibold text-[var(--color-aria-ink)] flex items-center gap-2 mb-3">
            <FileText className="h-4 w-4 text-[var(--color-aria-cyan)]" /> A.R.I.A. Output
          </p>
          <pre className="text-xs text-[var(--color-aria-muted)] whitespace-pre-wrap leading-relaxed">{output}</pre>
        </div>
      )}
    </motion.div>
  );
}
