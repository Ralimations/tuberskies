import { Bot, TrendingUp, Lightbulb, Send, ChevronRight } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const INSIGHTS = [
  {
    icon: TrendingUp,
    color: "text-[var(--color-aria-green)]",
    bg: "bg-[var(--color-aria-green-dim)]",
    title: "Audience retention is rising",
    body: "Great momentum this week!",
  },
  {
    icon: Lightbulb,
    color: "text-[var(--color-aria-amber)]",
    bg: "bg-amber-500/10",
    title: "Similar content performs best",
    body: "Emotional hooks drive watch time.",
  },
];

const IMPROVE = [
  "Strengthen the first 3 seconds",
  "Add more pattern interrupts",
  "Experiment with cinematic cuts",
];

interface ARIAPanelProps {
  recommendation?: string;
  recommendationDetail?: string;
}

export function ARIAPanel({
  recommendation = "Upload on Thursday at 6:00 PM",
  recommendationDetail = "Best performing time window for your audience.",
}: ARIAPanelProps) {
  const [draft, setDraft] = useState("");

  return (
    <aside className="fixed inset-y-0 right-0 z-40 flex w-[280px] flex-col border-l border-[var(--color-aria-border)] bg-[var(--color-aria-surface)]">
      {/* Header */}
      <div className="flex items-center gap-2 px-5 py-5 border-b border-[var(--color-aria-border)]">
        <div className="h-8 w-8 rounded-lg bg-[var(--color-aria-purple-dim)] border border-[var(--color-aria-border-strong)] flex items-center justify-center">
          <Bot className="h-4 w-4 text-[var(--color-aria-purple)]" />
        </div>
        <div>
          <p className="text-sm font-bold text-[var(--color-aria-ink)]">A.R.I.A.</p>
          <p className="text-[10px] text-[var(--color-aria-muted)] uppercase tracking-widest">AI Strategist</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-5">
        {/* ARIA face / greeting */}
        <div className="rounded-xl bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)] p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-[var(--color-aria-blue)] to-[var(--color-aria-purple)] flex items-center justify-center text-white font-black text-sm">
              A
            </div>
            <div>
              <p className="text-xs font-semibold text-[var(--color-aria-ink)]">A.R.I.A. says</p>
              <p className="text-[10px] text-[var(--color-aria-muted)]">Just now</p>
            </div>
          </div>
          <p className="text-sm text-[var(--color-aria-ink)] leading-relaxed">
            I analyzed your channel and found the best path forward.
          </p>
        </div>

        {/* Key Recommendation */}
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-[var(--color-aria-blue)] mb-2">
            Key Recommendation
          </p>
          <div className="rounded-xl bg-[var(--color-aria-blue-dim)] border border-[var(--color-aria-blue)]/20 p-4">
            <p className="text-sm font-bold text-[var(--color-aria-ink)] leading-snug mb-1">
              {recommendation}
            </p>
            <p className="text-xs text-[var(--color-aria-muted)] mb-3">{recommendationDetail}</p>
            <button className="w-full py-2 rounded-lg gradient-btn text-white text-xs font-bold transition-opacity hover:opacity-90 flex items-center justify-center gap-2">
              Apply Recommendation
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* What to Improve */}
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-[var(--color-aria-muted)] mb-2">
            What to Improve
          </p>
          <div className="space-y-2">
            {IMPROVE.map((item) => (
              <div
                key={item}
                className="flex items-center gap-2.5 text-xs text-[var(--color-aria-muted)] hover:text-[var(--color-aria-ink)] cursor-pointer transition-colors"
              >
                <div className="h-1.5 w-1.5 rounded-full bg-[var(--color-aria-red)] shrink-0" />
                {item}
              </div>
            ))}
          </div>
        </div>

        {/* Recent Insights */}
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-[var(--color-aria-muted)] mb-2">
            Recent Insights
          </p>
          <div className="space-y-2">
            {INSIGHTS.map((insight) => (
              <div
                key={insight.title}
                className="flex items-start gap-2.5 p-3 rounded-lg bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)]"
              >
                <div className={cn("h-6 w-6 rounded-md flex items-center justify-center shrink-0", insight.bg)}>
                  <insight.icon className={cn("h-3.5 w-3.5", insight.color)} />
                </div>
                <div>
                  <p className="text-xs font-semibold text-[var(--color-aria-ink)]">{insight.title}</p>
                  <p className="text-[10px] text-[var(--color-aria-muted)] mt-0.5">{insight.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Chat input */}
      <div className="border-t border-[var(--color-aria-border)] px-4 py-3">
        <p className="text-[10px] text-[var(--color-aria-muted)] mb-2">
          A.R.I.A. learns from your data.
        </p>
        <div className="flex items-center gap-2">
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Ask anything about your channel…"
            className="flex-1 min-w-0 bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)] rounded-lg px-3 py-2 text-xs text-[var(--color-aria-ink)] placeholder:text-[var(--color-aria-faint)] outline-none focus:border-[var(--color-aria-blue)] transition-colors"
          />
          <button className="h-8 w-8 gradient-btn rounded-lg flex items-center justify-center shrink-0 hover:opacity-90 transition-opacity">
            <Send className="h-3.5 w-3.5 text-white" />
          </button>
        </div>
      </div>
    </aside>
  );
}
