import { Bot, TrendingUp, Lightbulb, Send, ChevronRight, User, Loader2, Sparkles } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";
import { useBootstrap } from "@/context/BootstrapContext";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

const INSIGHTS = [
  {
    icon: TrendingUp,
    color: "text-[var(--color-aria-green)]",
    bg: "bg-[var(--color-aria-green-dim)]",
    title: "Audience retention is rising",
    body: "Your recent uploads are holding attention longer than last week.",
  },
  {
    icon: Lightbulb,
    color: "text-[var(--color-aria-amber)]",
    bg: "bg-amber-500/10",
    title: "Hooks are driving clicks",
    body: "Short emotional setups are outperforming generic intros.",
  },
];

const IMPROVE = [
  "Tighten the first 3 seconds",
  "Add one visual pattern interrupt",
  "Cut slower transitions in the middle section",
];

interface ARIAPanelProps {
  recommendation?: string;
  recommendationDetail?: string;
}

export function ARIAPanel({
  recommendation: propRecommendation,
  recommendationDetail: propRecommendationDetail,
}: ARIAPanelProps) {
  const { data } = useBootstrap();
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (overrideText?: string) => {
    const textToSend = overrideText || draft;
    if (!textToSend.trim() || isLoading) return;

    const userMsg = textToSend.trim();
    if (!overrideText) setDraft("");
    
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setIsLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg, history: messages }),
      });

      if (res.ok) {
        const response = await res.json();
        setMessages((prev) => [...prev, { role: "assistant", content: response.content }]);
      } else {
        setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I ran into an error." }]);
      }
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Network error connecting to A.R.I.A." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <aside className="glass-panel hidden rounded-[28px] border border-[var(--color-aria-border)] xl:flex xl:min-h-[calc(100vh-2.5rem)] xl:flex-col xl:overflow-hidden">
      <div className="flex items-center gap-3 border-b border-[var(--color-aria-border)] px-5 py-5">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--color-aria-blue-dim)] text-[var(--color-aria-blue)]">
          <Bot className="h-5 w-5" />
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--color-aria-muted)]">
            A.R.I.A.
          </p>
          <p className="text-base font-semibold text-[var(--color-aria-ink)]">Strategy channel</p>
        </div>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto px-4 py-4">
        <div className="rounded-[24px] border border-[var(--color-aria-border)] bg-white/5 p-4">
          <div className="mb-3 flex items-center gap-3">
            <div className="gradient-btn flex h-11 w-11 items-center justify-center rounded-full text-sm font-black text-slate-950">
              A
            </div>
            <div>
              <p className="text-xs font-semibold text-[var(--color-aria-ink)]">A.R.I.A. says</p>
              <p className="text-[10px] uppercase tracking-wide text-[var(--color-aria-muted)]">Live brief</p>
            </div>
          </div>
          <p className="text-sm leading-6 text-[var(--color-aria-ink)]">
            {data?.messages?.analytics || "I analyzed your channel and found the strongest next move."}
          </p>
        </div>

        <div className="rounded-[24px] border border-[var(--color-aria-blue)]/20 bg-[var(--color-aria-blue-dim)] p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-[var(--color-aria-blue)]">
            Recommended move
          </p>
          <p className="mt-3 text-lg font-semibold leading-snug text-[var(--color-aria-ink)]">
            {propRecommendation || data?.today?.focus_title || "Upload on Thursday at 6:00 PM"}
          </p>
          <p className="mt-2 text-sm leading-6 text-[var(--color-aria-muted)]">
            {propRecommendationDetail || data?.today?.focus_reason || "Best performing time window for your audience."}
          </p>
          <button className="gradient-btn mt-4 flex w-full items-center justify-center gap-2 rounded-full px-4 py-3 text-sm font-semibold text-slate-950 transition-opacity hover:opacity-90">
            Apply recommendation
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>

        <div>
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.22em] text-[var(--color-aria-faint)]">
            Tighten next
          </p>
          <div className="space-y-2">
            {(data?.uploadTakeaways?.improvement_rows?.map((row) => `${row[0]}: ${row[1]}`) || IMPROVE).map((item) => (
              <div
                key={item}
                className="flex items-start gap-2 rounded-2xl border border-[var(--color-aria-border)] bg-white/4 px-3 py-3 text-xs leading-5 text-[var(--color-aria-muted)]"
              >
                <div className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--color-aria-red)]" />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.22em] text-[var(--color-aria-faint)]">
            Signals
          </p>
          <div className="space-y-2">
            {(data?.today?.opportunity_title
              ? [
                  {
                    icon: TrendingUp,
                    color: "text-[var(--color-aria-green)]",
                    bg: "bg-[var(--color-aria-green-dim)]",
                    title: data.today.opportunity_title,
                    body: data.today.opportunity_reason,
                  },
                  {
                    icon: Lightbulb,
                    color: "text-[var(--color-aria-amber)]",
                    bg: "bg-amber-500/10",
                    title: data.today.risk_title || "Audience preference shift",
                    body: data.today.risk_reason || "Hook clarity matters more than production complexity right now.",
                  },
                ]
              : INSIGHTS
            ).map((insight) => (
              <div
                key={insight.title}
                className="flex items-start gap-3 rounded-2xl border border-[var(--color-aria-border)] bg-white/4 p-3"
              >
                <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-xl", insight.bg)}>
                  <insight.icon className={cn("h-4 w-4", insight.color)} />
                </div>
                <div>
                  <p className="text-sm font-medium text-[var(--color-aria-ink)]">{insight.title}</p>
                  <p className="mt-1 text-xs leading-5 text-[var(--color-aria-muted)]">{insight.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {messages.length > 0 && (
          <div className="space-y-4 border-t border-[var(--color-aria-border)] pt-4">
            {messages.map((msg, idx) => (
              <div key={idx} className={cn("flex flex-col gap-1.5", msg.role === "user" ? "items-end" : "items-start")}>
                <div className="flex items-center gap-2">
                  {msg.role === "assistant" ? (
                    <>
                      <div className="gradient-btn flex h-5 w-5 items-center justify-center rounded-full text-[8px] font-black text-slate-950">
                        A
                      </div>
                      <p className="text-[10px] font-semibold text-[var(--color-aria-ink)]">A.R.I.A.</p>
                    </>
                  ) : (
                    <>
                      <p className="text-[10px] font-semibold text-[var(--color-aria-ink)]">You</p>
                      <div className="flex h-5 w-5 items-center justify-center rounded-full border border-[var(--color-aria-border)] bg-white/5">
                        <User className="h-3 w-3 text-[var(--color-aria-muted)]" />
                      </div>
                    </>
                  )}
                </div>
                <div
                  className={cn(
                    "max-w-[92%] rounded-2xl px-3 py-2 text-xs leading-5 whitespace-pre-wrap",
                    msg.role === "user"
                      ? "bg-[var(--color-aria-blue)] text-slate-950"
                      : "border border-[var(--color-aria-border)] bg-white/5 text-[var(--color-aria-ink)]"
                  )}
                >
                  {msg.role === "user" ? (
                    msg.content
                  ) : (
                    <div className="space-y-2">
                      <ReactMarkdown
                        components={{
                          p: ({ node, ...props }) => <p className="leading-relaxed" {...props} />,
                          ul: ({ node, ...props }) => <ul className="list-disc space-y-1 pl-4" {...props} />,
                          ol: ({ node, ...props }) => <ol className="list-decimal space-y-1 pl-4" {...props} />,
                          li: ({ node, ...props }) => <li className="pl-1" {...props} />,
                          strong: ({ node, ...props }) => <strong className="font-bold text-white" {...props} />,
                          em: ({ node, ...props }) => <em className="italic text-[var(--color-aria-faint)]" {...props} />,
                          code: ({ node, ...props }) => (
                            <code
                              className="rounded bg-[var(--color-aria-surface)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-aria-blue)]"
                              {...props}
                            />
                          ),
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Chat input */}
      <div className="border-t border-[var(--color-aria-border)] p-4 shrink-0 bg-[var(--color-aria-surface)] flex flex-col gap-3">
        {messages.length === 0 && (
          <div className="flex flex-wrap gap-2">
            {[
              "Analyze my retention drop-offs", 
              "What title works best?", 
              "Summarize audience requests"
            ].map((insight) => (
              <button
                key={insight}
                onClick={() => handleSend(insight)}
                className="text-[10px] px-2.5 py-1.5 rounded-full border border-[var(--color-aria-border)] bg-[var(--color-aria-surface-3)] text-[var(--color-aria-muted)] hover:text-white hover:border-[var(--color-aria-blue)] hover:bg-[var(--color-aria-blue-dim)] transition-colors flex items-center gap-1.5 whitespace-nowrap text-left"
              >
                <Sparkles className="h-3 w-3" />
                {insight}
              </button>
            ))}
          </div>
        )}
        
        <div className="flex items-center gap-2">
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="What should I post next?"
            className="min-w-0 flex-1 rounded-full border border-[var(--color-aria-border)] bg-white/6 px-4 py-3 text-sm text-[var(--color-aria-ink)] outline-none transition-colors placeholder:text-[var(--color-aria-faint)] focus:border-[var(--color-aria-blue)] disabled:opacity-50"
          />
          <button
            onClick={() => handleSend()}
            disabled={isLoading || !draft.trim()}
            className="gradient-btn flex h-11 w-11 shrink-0 items-center justify-center rounded-full transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin text-slate-950" /> : <Send className="h-4 w-4 text-slate-950" />}
          </button>
        </div>
      </div>
    </aside>
  );
}
