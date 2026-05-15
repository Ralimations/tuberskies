import { Bot, Sparkles, Send, Loader2, User, ArrowRight, TrendingUp } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";
import { useBootstrap } from "@/context/BootstrapContext";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export function ARIAPanel() {
  const { data } = useBootstrap();
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const recommendation = data?.today?.today_action || data?.today?.focus_title || "Pick the next upload to refine.";
  const suggestionChips = [
    "What should I post next?",
    "Where is retention dropping?",
    "Which title angle should I repeat?",
  ];

  async function handleSend(overrideText?: string) {
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
  }

  return (
    <aside className="glass-panel hidden rounded-[28px] border border-[var(--color-aria-border)] 2xl:ml-6 2xl:flex 2xl:max-h-[calc(100vh-3rem)] 2xl:self-start 2xl:flex-col 2xl:overflow-hidden">
      <div className="px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--color-aria-blue-dim)] text-[var(--color-aria-blue)]">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--color-aria-muted)]">A.R.I.A.</p>
            <p className="text-base font-semibold text-[var(--color-aria-ink)]">Work with the assistant</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="space-y-6">
        <div className="rounded-[24px] bg-white/5 p-6">
          <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-[var(--color-aria-faint)]">Recommended next step</p>
          <p className="mt-4 text-lg font-semibold leading-snug text-[var(--color-aria-ink)]">{recommendation}</p>
          <p className="mt-2 text-sm leading-6 text-[var(--color-aria-muted)]">
            Ask for the exact title, hook, or packaging change needed to move this forward.
          </p>
          <button className="gradient-btn mt-4 flex w-full items-center justify-center gap-2 rounded-full px-4 py-4 text-sm font-semibold text-slate-950">
            Start with this
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>

        <div className="rounded-[24px] bg-white/5 p-6">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[var(--color-aria-green-dim)] text-[var(--color-aria-green)]">
              <TrendingUp className="h-4 w-4" />
            </div>
            <p className="text-sm font-semibold text-[var(--color-aria-ink)]">What changed</p>
          </div>
          <p className="mt-4 text-sm leading-6 text-[var(--color-aria-muted)]">
            {data?.messages?.analytics || "I analyzed your channel and found the strongest next move."}
          </p>
        </div>

        {messages.length > 0 && (
          <div className="rounded-[24px] bg-white/4 p-6">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-[var(--color-aria-faint)]">Conversation</p>
                <p className="mt-2 text-sm font-semibold text-[var(--color-aria-ink)]">Working thread</p>
              </div>
            </div>
            <div className="space-y-4">
            {messages.map((msg, idx) => (
              <div key={idx} className={cn("flex flex-col gap-2", msg.role === "user" ? "items-end" : "items-start")}>
                <div className="flex items-center gap-2">
                  {msg.role === "assistant" ? (
                    <>
                      <div className="gradient-btn flex h-5 w-5 items-center justify-center rounded-full text-[8px] font-black text-slate-950">A</div>
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
                    "max-w-[92%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-xs leading-5",
                    msg.role === "user"
                      ? "bg-[var(--color-aria-blue)] text-slate-950"
                      : "border border-[var(--color-aria-border)] bg-white/5 text-[var(--color-aria-ink)]",
                  )}
                >
                  {msg.role === "user" ? (
                    msg.content
                  ) : (
                    <ReactMarkdown
                      components={{
                        p: ({ node, ...props }) => <p className="leading-relaxed" {...props} />,
                        ul: ({ node, ...props }) => <ul className="list-disc space-y-1 pl-4" {...props} />,
                        ol: ({ node, ...props }) => <ol className="list-decimal space-y-1 pl-4" {...props} />,
                        li: ({ node, ...props }) => <li className="pl-1" {...props} />,
                        strong: ({ node, ...props }) => <strong className="font-bold text-white" {...props} />,
                        code: ({ node, ...props }) => <code className="rounded bg-[var(--color-aria-surface)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-aria-blue)]" {...props} />,
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
          </div>
        )}
        </div>
      </div>

      <div className="bg-[var(--color-aria-surface)] p-6">
        <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.22em] text-[var(--color-aria-faint)]">Quick starts</p>
        <div className="mb-4 flex flex-wrap gap-2">
          {suggestionChips.map((chip) => (
            <button
              key={chip}
              onClick={() => handleSend(chip)}
              className="rounded-full border border-[var(--color-aria-border)] bg-white/5 px-3 py-2 text-xs text-[var(--color-aria-muted)] transition-colors hover:border-[var(--color-aria-blue)] hover:text-[var(--color-aria-ink)]"
            >
              <span className="inline-flex items-center gap-1.5">
                <Sparkles className="h-3 w-3" />
                {chip}
              </span>
            </button>
          ))}
        </div>
        <div className="items-center gap-3 2xl:flex">
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            disabled={isLoading}
            placeholder="Ask for the next fix..."
            className="min-w-0 flex-1 rounded-full border border-[var(--color-aria-border)] bg-white/6 px-4 py-4 text-sm text-[var(--color-aria-ink)] outline-none transition-colors placeholder:text-[var(--color-aria-faint)] focus:border-[var(--color-aria-blue)] disabled:opacity-50"
          />
          <button
            onClick={() => handleSend()}
            disabled={isLoading || !draft.trim()}
            className="gradient-btn mt-2 flex h-11 w-11 shrink-0 items-center justify-center rounded-full transition-opacity hover:opacity-90 disabled:opacity-50 2xl:mt-0"
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin text-slate-950" /> : <Send className="h-4 w-4 text-slate-950" />}
          </button>
        </div>
      </div>
    </aside>
  );
}
