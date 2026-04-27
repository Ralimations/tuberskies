import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
import {
  analyzeShortsWithAi,
  askAria,
  askAriaStream,
  authorizeYoutube,
  checkLatestYoutubeData,
  clearYoutubeToken,
  coachRepertoire,
  deleteShortsProject,
  draftMetadata,
  draftUploadTips,
  generateIdeation,
  loadAnalytics,
  loadBootstrap,
  loadCreatorActions,
  loadMetadata,
  loadRepertoire,
  listShortsProjects,
  loadShortsProject,
  loadVault,
  previewShortsFromAiPlan,
  publishMetadata,
  renderShortsFromAiPlan,
  saveRepertoire,
  saveShortsProject,
  saveVault,
  scoreIdeation
} from "./api";
import { Icon } from "./icons";
import type { AnalyticsPayload, BootstrapPayload, ChatMessage, CreatorActionsPayload, IdeationScorePayload, NavItem, RepertoirePayload, ShortsAiAnalyzePayload, ShortsPlanClip, ShortsPreviewPayload, ShortsProjectPayload, ShortsRenderPayload, VaultPayload } from "./types";

const fallbackData: BootstrapPayload = {
  navigation: [
    { label: "Ask A.R.I.A.", path: "/", icon: "comments", group: "Home" },
    { label: "Analytics", path: "/analytics", icon: "chart", group: "Home" },
    { label: "Creator Actions", path: "/creator-actions", icon: "reply", group: "Home" },
    { label: "Upload Lab", path: "/upload-lab", icon: "upload", group: "More tools" },
    { label: "A.R.I.A. Memory", path: "/pattern-memory", icon: "memory", group: "More tools" },
    { label: "Repertoire", path: "/repertoire", icon: "music", group: "More tools" },
    { label: "Shorts Architect", path: "/shorts", icon: "scissors", group: "More tools" },
    { label: "The Vault", path: "/vault", icon: "vault", group: "More tools" }
  ],
  chatSuggestions: [
    "What should I do next today?",
    "Which upload pattern should I repeat?",
    "What is the biggest risk in my analytics?",
    "What should I turn into Shorts?"
  ],
  profile: { title: "Ralskies", handle: "@ralskies", source: "Loading" },
  stats: [],
  today: {
    focus_title: "Loading",
    focus_reason: "",
    risk_title: "Loading",
    risk_reason: "",
    opportunity_title: "Loading",
    opportunity_reason: "",
    today_action: ""
  },
  uploadTakeaways: {},
  patternMemory: null,
  analyticsRows: [],
  videoRows: [],
  calendarRows: [],
  messages: {},
  cache: []
};

function currentPath() {
  return window.location.pathname || "/";
}

function navigateTo(path: string) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

const startupSteps = ["Connect API", "Load daily cache", "Wake local AI", "Open studio"];

function useStoredState<T>(key: string, fallback: T): [T, (value: T | ((current: T) => T)) => void] {
  const [state, setState] = useState<T>(() => {
    try {
      const raw = window.localStorage.getItem(key);
      return raw ? JSON.parse(raw) as T : fallback;
    } catch {
      return fallback;
    }
  });

  function updateState(value: T | ((current: T) => T)) {
    setState((current) => {
      const next = typeof value === "function" ? (value as (current: T) => T)(current) : value;
      try {
        window.localStorage.setItem(key, JSON.stringify(next));
      } catch {
        // Persistence is best-effort; the in-memory workspace still keeps running.
      }
      return next;
    });
  }

  return [state, updateState];
}

export function App() {
  const [data, setData] = useState<BootstrapPayload>(fallbackData);
  const [path, setPath] = useState(currentPath());
  const [visitedPaths, setVisitedPaths] = useState<Set<string>>(() => new Set([currentPath()]));
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    loadBootstrap()
      .then((payload) => {
        setData(payload);
        setLoadError("");
      })
      .catch((error: Error) => setLoadError(error.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const onPop = () => setPath(currentPath());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  useEffect(() => {
    setVisitedPaths((current) => {
      if (current.has(path)) return current;
      return new Set([...current, path]);
    });
  }, [path]);

  function navigate(item: NavItem) {
    window.history.pushState({}, "", item.path);
    setPath(item.path);
  }

  function route(pathName: string, child: ReactNode) {
    if (!visitedPaths.has(pathName)) return null;
    return (
      <div className="route-panel" hidden={path !== pathName}>
        {child}
      </div>
    );
  }

  return (
    <div className="studio-shell">
      <Sidebar items={data.navigation} activePath={path} onNavigate={navigate} />
      <main className="workspace">
        {loadError ? <div className="status error">{loadError}</div> : null}
        {loading ? (
          <StartupScreen />
        ) : (
          <>
            {route("/", <AskPage data={data} />)}
            {route("/analytics", <AnalyticsPage data={data} />)}
            {route("/creator-actions", <CreatorActionsPage />)}
            {route("/upload-lab", <UploadLabPage data={data} />)}
            {route("/pattern-memory", <PatternPage data={data} />)}
            {route("/ideation", <IdeationPage />)}
            {route("/repertoire", <RepertoirePage data={data} />)}
            {route("/shorts", <ShortsArchitectPage />)}
            {route("/vault", <VaultPage />)}
          </>
        )}
      </main>
    </div>
  );
}

function StartupScreen() {
  return (
    <section className="startup-screen" aria-live="polite" aria-label="A.R.I.A. Studio is starting">
      <div className="startup-mark">A</div>
      <div className="startup-copy">
        <span>Starting A.R.I.A. Studio</span>
        <h1>Loading today&apos;s creator context</h1>
        <p>Checking the local API, cached YouTube data, and your local AI workspace.</p>
      </div>
      <div className="startup-meter" aria-hidden="true">
        <span />
      </div>
      <div className="startup-steps">
        {startupSteps.map((step, index) => (
          <div className="startup-step" key={step}>
            <span>{index + 1}</span>
            <strong>{step}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

function Sidebar({ items, activePath, onNavigate }: { items: NavItem[]; activePath: string; onNavigate: (item: NavItem) => void }) {
  const groups = useMemo(() => {
    return items.reduce<Record<string, NavItem[]>>((acc, item) => {
      acc[item.group] = [...(acc[item.group] ?? []), item];
      return acc;
    }, {});
  }, [items]);

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">A</div>
        <span>A.R.I.A.</span>
      </div>
      {Object.entries(groups).map(([group, groupItems]) => (
        <section className="nav-group" key={group}>
          <p>{group}</p>
          {groupItems.map((item) => (
            <button className={activePath === item.path ? "nav-item active" : "nav-item"} key={item.path} onClick={() => onNavigate(item)}>
              <Icon name={item.icon} />
              <span>{item.label}</span>
            </button>
          ))}
        </section>
      ))}
      <div className="sidebar-note">Local-first creator intelligence</div>
    </aside>
  );
}

function AskPage({ data }: { data: BootstrapPayload }) {
  const freshness = getPrimaryFreshness(data.cache);
  const suggestions = freshness.freshToday
    ? data.chatSuggestions
    : ["What can I trust in the stored data?", ...data.chatSuggestions.slice(0, 3)];
  const starterMessage: ChatMessage = {
    role: "assistant",
    content: `Ask me what to fix, repeat, post, package, or turn into Shorts. I am reading ${freshness.chatLabel}.`
  };
  const [chatSessions, setChatSessions] = useState<ChatSession[]>(() => loadChatSessions(starterMessage));
  const [activeChatId, setActiveChatId] = useState(() => chatSessions[0]?.id ?? createChatId());
  const activeSession = chatSessions.find((session) => session.id === activeChatId) ?? chatSessions[0];
  const messages = activeSession?.messages ?? [starterMessage];
  const [draft, setDraft] = useState("");
  const [thinking, setThinking] = useState(false);
  const [responseStarted, setResponseStarted] = useState(false);

  useEffect(() => {
    setChatSessions((current) => {
      const next = current.map((session) => {
        if (session.messages.length !== 1 || session.messages[0].role !== "assistant") return session;
        return { ...session, messages: [starterMessage], updatedAt: Date.now() };
      });
      saveChatSessions(next);
      return next;
    });
  }, [freshness.chatLabel]);

  function updateActiveMessages(nextMessages: ChatMessage[] | ((current: ChatMessage[]) => ChatMessage[])) {
    setChatSessions((current) => {
      const next = current.map((session) => {
        if (session.id !== activeChatId) return session;
        const messagesValue = typeof nextMessages === "function" ? nextMessages(session.messages) : nextMessages;
        return { ...session, messages: messagesValue, title: chatTitle(messagesValue), updatedAt: Date.now() };
      });
      saveChatSessions(next);
      return next;
    });
  }

  function startNewChat() {
    const nextSession = createChatSession(starterMessage);
    setChatSessions((current) => {
      const next = [nextSession, ...current].slice(0, 12);
      saveChatSessions(next);
      return next;
    });
    setActiveChatId(nextSession.id);
    setDraft("");
  }

  async function submitMessage(message: string) {
    const clean = message.trim();
    if (!clean || thinking) return;
    const latestUser = [...messages].reverse().find((item) => item.role === "user");
    if (latestUser?.content === clean) return;

    const nextMessages: ChatMessage[] = [...messages, { role: "user", content: clean }];
    const assistantIndex = nextMessages.length;
    updateActiveMessages([...nextMessages, { role: "assistant", content: "" }]);
    setDraft("");
    setThinking(true);
    setResponseStarted(false);
    let accumulated = "";
    try {
      await askAriaStream(clean, nextMessages, (chunk) => {
        accumulated += chunk;
        setResponseStarted(true);
        updateActiveMessages((current) =>
          current.map((item, index) => (index === assistantIndex ? { role: "assistant", content: accumulated } : item))
        );
      });
      if (!accumulated.trim()) {
        updateActiveMessages((current) =>
          current.map((item, index) =>
            index === assistantIndex ? { role: "assistant", content: "A.R.I.A. did not return a response. Check Ollama, then try again." } : item
          )
        );
      }
    } catch (error) {
      try {
        const response = await askAria(clean, nextMessages);
        updateActiveMessages([...nextMessages, response]);
      } catch {
        updateActiveMessages((current) =>
          current.map((item, index) =>
            index === assistantIndex ? { role: "assistant", content: error instanceof Error ? error.message : "A.R.I.A. could not respond." } : item
          )
        );
      }
    } finally {
      setThinking(false);
      setResponseStarted(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    submitMessage(draft);
  }

  return (
    <section className="home-stack">
      <TodayDesk data={data} freshness={freshness} />
      <div className="chat-history-bar">
        <button onClick={startNewChat}>New Chat</button>
        <select value={activeChatId} onChange={(event) => setActiveChatId(event.target.value)}>
          {chatSessions.map((session) => (
            <option value={session.id} key={session.id}>{session.title}</option>
          ))}
        </select>
      </div>
      <div className="suggestions">
        {suggestions.map((suggestion) => (
          <button key={suggestion} onClick={() => submitMessage(suggestion)}>
            {suggestion}
          </button>
        ))}
      </div>
      <div className="messages">
        {messages.map((message, index) => (
          <article className={`message ${message.role}`} key={`${message.role}-${index}`}>
            <div className="avatar">{message.role === "assistant" ? "A" : "R"}</div>
            <p>
              {message.content || (message.role === "assistant" && thinking ? (
                <span className="thinking-inline">
                  <span className="typing-dot" />
                  A.R.I.A. is reading your analytics...
                </span>
              ) : "")}
            </p>
          </article>
        ))}
        {thinking ? (
          <div className="generation-status">
            <span className="spinner" />
            <strong>{responseStarted ? "A.R.I.A. is writing..." : "A.R.I.A. is generating..."}</strong>
          </div>
        ) : null}
      </div>
      <form className="composer" onSubmit={onSubmit}>
        <input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Ask A.R.I.A. about your analytics..." />
        <button type="submit" disabled={thinking}>
          {thinking ? "Wait" : "Ask"}
        </button>
      </form>
    </section>
  );
}

function getPrimaryFreshness(cache: BootstrapPayload["cache"]) {
  const priority = ["Analytics", "Upload Performance", "Channel Profile"];
  const row = priority.map((name) => cache.find((item) => item.dataset === name)).find(Boolean) ?? cache[0];
  const status = row?.status ?? "Loading";
  const latestDate = row?.latest_data_date || row?.today_date || "";
  const checkedToday = Boolean(row?.today_date);
  const freshToday = status === "Fresh today";
  const chatLabel = latestDate
    ? `${freshToday ? "fresh" : "stored"} YouTube data from ${latestDate}`
    : "the currently loaded local context";
  return {
    status,
    latestDate,
    checkedToday,
    freshToday,
    chatLabel,
    message: row?.message ?? "",
  };
}

function TodayDesk({ data, freshness }: { data: BootstrapPayload; freshness: ReturnType<typeof getPrimaryFreshness> }) {
  const best = data.uploadTakeaways.best;
  const bestTitle = best ? String(best.title ?? "Top upload") : "No upload leader loaded";
  const bestMeta = best ? `${Number(best.views ?? 0).toLocaleString()} views | ${Number(best.retention ?? 0).toFixed(1)}% retention` : "Check latest data when YouTube is connected.";
  const freshnessAction = freshness.freshToday ? "View Freshness" : "Check Latest";

  return (
    <section className="today-desk">
      <div className="today-hero">
        <div>
          <span className={freshness.freshToday ? "freshness-badge fresh" : "freshness-badge"}>
            {freshness.status}
          </span>
          <h1>{data.today.today_action || "Choose the next best creator move."}</h1>
          <p>{freshness.latestDate ? `A.R.I.A. is using YouTube data from ${freshness.latestDate}.` : "A.R.I.A. is waiting on a stored YouTube snapshot."}</p>
          <div className="today-actions">
            <button className="primary" onClick={() => navigateTo("/repertoire")}>Move Song Forward</button>
            <button onClick={() => navigateTo("/analytics")}>Review Analytics</button>
            <button onClick={() => navigateTo("/vault")}>{freshnessAction}</button>
          </div>
        </div>
        <div className="pulse-card">
          <small>{data.profile.title}</small>
          <strong>{data.profile.source}</strong>
          <span>{freshness.checkedToday ? "Checked today" : "Not checked today"}</span>
        </div>
      </div>
      <div className="today-grid">
        <article>
          <span>Focus</span>
          <strong>{data.today.focus_title}</strong>
          <p>{data.today.focus_reason}</p>
        </article>
        <article>
          <span>Risk</span>
          <strong>{data.today.risk_title}</strong>
          <p>{data.today.risk_reason}</p>
        </article>
        <article>
          <span>Opportunity</span>
          <strong>{data.today.opportunity_title}</strong>
          <p>{data.today.opportunity_reason}</p>
        </article>
        <article>
          <span>Pattern To Repeat</span>
          <strong>{bestTitle}</strong>
          <p>{bestMeta}</p>
        </article>
      </div>
      <div className="next-strip">
        <button onClick={() => navigateTo("/creator-actions")}>
          <Icon name="reply" />
          Creator Actions
        </button>
        <button onClick={() => navigateTo("/ideation")}>
          <Icon name="spark" />
          Ideation
        </button>
        <button onClick={() => navigateTo("/shorts")}>
          <Icon name="scissors" />
          Shorts Architect
        </button>
      </div>
    </section>
  );
}

type ChatSession = {
  id: string;
  title: string;
  messages: ChatMessage[];
  updatedAt: number;
};

const CHAT_HISTORY_KEY = "aria_chat_sessions";

function createChatId() {
  return `chat_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function chatTitle(messages: ChatMessage[]) {
  const firstUser = messages.find((message) => message.role === "user")?.content.trim();
  return firstUser ? firstUser.slice(0, 64) : "New A.R.I.A. chat";
}

function createChatSession(starterMessage: ChatMessage): ChatSession {
  return {
    id: createChatId(),
    title: "New A.R.I.A. chat",
    messages: [starterMessage],
    updatedAt: Date.now()
  };
}

function loadChatSessions(starterMessage: ChatMessage): ChatSession[] {
  try {
    const raw = window.localStorage.getItem(CHAT_HISTORY_KEY);
    const parsed = raw ? JSON.parse(raw) : null;
    if (Array.isArray(parsed) && parsed.length) {
      return parsed
        .filter((session) => session && Array.isArray(session.messages))
        .slice(0, 12);
    }
  } catch {
    // Ignore malformed local history and start fresh.
  }
  return [createChatSession(starterMessage)];
}

function saveChatSessions(sessions: ChatSession[]) {
  try {
    window.localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(sessions.slice(0, 12)));
  } catch {
    // Local storage can be full or unavailable; chat still works for the session.
  }
}

function AnalyticsPage({ data }: { data: BootstrapPayload }) {
  const [payload, setPayload] = useState<AnalyticsPayload | null>(null);
  const [metric, setMetric] = useState("views");
  const [status, setStatus] = useState("");
  const [notice, setNotice] = useState("");
  const analytics = payload ?? {
    source: data.profile.source,
    profile: data.profile,
    stats: data.stats,
    today: data.today,
    rows: data.analyticsRows,
    alerts: [],
    publishTiming: [],
    auditRows: [],
    actionCards: [],
    messages: data.messages
  };

  useEffect(() => {
    loadAnalytics()
      .then((result) => {
        setPayload(result);
        setStatus("");
      })
      .catch((error: Error) => setStatus(error.message));
  }, []);

  function handleActionCard(card: AnalyticsPayload["actionCards"][number]) {
    if (card.path === "/analytics") {
      setNotice(`${card.cta}: ${card.body}`);
      return;
    }
    navigateTo(card.path);
  }

  return (
    <section className="page-stack">
      <Hero data={{ ...data, profile: { ...data.profile, title: String(analytics.profile.title ?? data.profile.title), handle: String(analytics.profile.handle ?? data.profile.handle), source: analytics.source } }} />
      {status ? <div className="status error">{status}</div> : null}
      {notice ? <div className="status">{notice}</div> : null}
      <div className="grid stats-grid">
        {analytics.stats.map((stat) => (
          <div className="metric-card" key={stat.label}>
            <span>{stat.label}</span>
            <strong>{stat.value}</strong>
            <small>{stat.meta}</small>
          </div>
        ))}
      </div>
      <Panel title="Performance Trend">
        <div className="analytics-toolbar">
          {["views", "retention", "ctr", "watch_time_hours"].map((item) => (
            <button className={metric === item ? "active" : ""} key={item} onClick={() => setMetric(item)}>
              {item.replaceAll("_", " ")}
            </button>
          ))}
        </div>
        <Sparkline rows={analytics.rows} metric={metric} />
        <MetricDetailTable rows={analytics.rows} metric={metric} />
      </Panel>
      <div className="grid two-col">
        <Panel title="Today Brief">
          <InfoRow label="Focus" value={analytics.today.focus_title} />
          <InfoRow label="Risk" value={analytics.today.risk_title} />
          <InfoRow label="Opportunity" value={analytics.today.opportunity_title} />
          <InfoRow label="Move" value={analytics.today.today_action} />
        </Panel>
        <Panel title="Channel Audit">
          {analytics.auditRows.length ? analytics.auditRows.map((row) => <InfoRow key={row.label} label={row.label} value={row.value} />) : <p>Audit rows are loading.</p>}
        </Panel>
      </div>
      <div className="grid two-col">
        <Panel title="Trends">
          <DataTable rows={analytics.alerts} columns={["date", "trend", "views", "views_change", "retention", "ctr"]} />
        </Panel>
        <Panel title="Publish Timing">
          <DataTable rows={analytics.publishTiming} columns={["weekday", "avg_views", "avg_retention", "publish_score"]} />
        </Panel>
      </div>
      <Panel title="Recommended Actions">
        <div className="action-card-grid">
          {analytics.actionCards.length ? analytics.actionCards.map((card) => (
            <article className="action-card" key={`${card.category}-${card.title}`}>
              <span>{card.category}</span>
              <h3>{card.title}</h3>
              <p>{card.body}</p>
              <button onClick={() => handleActionCard(card)}>{card.cta}</button>
            </article>
          )) : <p>No action cards loaded yet.</p>}
        </div>
      </Panel>
    </section>
  );
}

function UploadLabPage({ data }: { data: BootstrapPayload }) {
  const [mode, setMode] = useStoredState<"Shorts" | "Full Length">("aria_upload_lab_mode", "Shorts");
  const [selectedIndex, setSelectedIndex] = useStoredState("aria_upload_lab_selected_index", 0);
  const [tips, setTips] = useStoredState("aria_upload_lab_tips", "");
  const [status, setStatus] = useState("");
  const rows = data.videoRows;
  const filteredRows = useMemo(() => rows.filter((row) => uploadKind(row) === mode), [rows, mode]);
  const activeRows = filteredRows.length ? filteredRows : rows;
  const ranked = [...activeRows].sort((a, b) => Number(b.engagement_score ?? 0) - Number(a.engagement_score ?? 0));
  const best = ranked[0] ?? null;
  const weak = ranked[ranked.length - 1] ?? null;
  const current = activeRows[selectedIndex] ?? activeRows[0] ?? null;

  useEffect(() => {
    setSelectedIndex(0);
    setTips("");
  }, [mode]);

  async function handleDraftTips(upload = current) {
    if (!upload) return;
    setStatus("A.R.I.A. is reading this upload...");
    setTips("");
    try {
      const result = await draftUploadTips(upload, mode);
      setTips(result.content);
      setStatus("");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Upload tips failed.");
    }
  }

  return (
    <section className="page-stack">
      <SectionHeader title="Upload Lab" copy="Compare Shorts and full videos, inspect current upload metrics, and ask A.R.I.A. what to improve." />
      {status ? <div className="status">{status}</div> : null}
      <div className="segmented">
        {["Shorts", "Full Length"].map((item) => (
          <button className={mode === item ? "active" : ""} key={item} onClick={() => setMode(item as "Shorts" | "Full Length")}>{item}</button>
        ))}
      </div>
      <Panel title="Current Upload">
        {current ? (
          <div className="upload-current">
            <RecordSummary record={current} />
            <label className="field">
              <span>Upload</span>
              <select value={selectedIndex} onChange={(event) => setSelectedIndex(Number(event.target.value))}>
                {activeRows.map((row, index) => <option value={index} key={String(row.video_id ?? row.title ?? index)}>{String(row.title ?? "Untitled")}</option>)}
              </select>
            </label>
            <button onClick={() => handleDraftTips(current)}>Ask A.R.I.A. For Tips</button>
          </div>
        ) : <p>No upload data loaded for this view.</p>}
      </Panel>
      <div className="grid two-col">
        <Panel title={`Best ${mode}`}>{best ? <RecordSummary record={best} /> : <p>No upload data loaded.</p>}</Panel>
        <Panel title={`Weakest ${mode}`}>{weak ? <RecordSummary record={weak} /> : <p>No upload data loaded.</p>}</Panel>
      </div>
      <Panel title="AI Suggested Tips">
        <pre>{tips || "Select an upload and ask A.R.I.A. for tips."}</pre>
      </Panel>
      <Panel title="Upload History">
        <DataTable rows={activeRows} columns={["title", "views", "retention", "watch_time_hours", "engagement_score"]} />
      </Panel>
    </section>
  );
}

function uploadKind(row: Record<string, unknown>) {
  const title = String(row.title ?? "").toLowerCase();
  const duration = Number(row.duration_seconds ?? row.duration ?? 0);
  if (duration > 0) return duration <= 90 ? "Shorts" : "Full Length";
  if (title.includes("#shorts") || title.includes("shorts") || title.includes("teaser") || title.includes("snippet")) return "Shorts";
  return "Full Length";
}

function PatternPage({ data }: { data: BootstrapPayload }) {
  const memory = data.patternMemory ?? {};
  const publishMemory = asRecord(memory.publish_memory);
  const stageMemory = asRecord(memory.stage_memory);
  const repeatMore = asStringList(memory.repeat_more);
  const reduceOrFix = asStringList(memory.reduce_or_fix);
  const titlePatterns = asRecordList(memory.title_patterns);
  const pillarMemory = asRecordList(memory.pillar_memory);
  const weekdayRows = asRecordList(publishMemory.weekday_rows);
  const stageRows = asRecordList(stageMemory.stage_rows);

  return (
    <section className="page-stack">
      <SectionHeader title="A.R.I.A. Memory" copy="The patterns A.R.I.A. remembers so advice stays consistent instead of generic." />
      <div className="grid two-col">
        <Panel title="Repeat More">
          <MemoryList items={repeatMore} empty="No repeat patterns have been learned yet." />
        </Panel>
        <Panel title="Reduce Or Fix">
          <MemoryList items={reduceOrFix} empty="No reduce/fix signals have been learned yet." />
        </Panel>
      </div>
      <div className="grid two-col">
        <Panel title="Publishing Memory">
          <div className="memory-summary">
            <InfoRow label="Best Day" value={String(publishMemory.best_day ?? "Unknown")} />
            <InfoRow label="Weak Day" value={String(publishMemory.weak_day ?? "Unknown")} />
            <InfoRow label="Best Score" value={String(publishMemory.best_score ?? "Unavailable")} />
          </div>
          <DataTable rows={weekdayRows} columns={["weekday", "avg_views", "avg_retention", "publish_score"]} />
        </Panel>
        <Panel title="Repertoire Memory">
          <div className="memory-summary">
            <InfoRow label="Bottleneck" value={String(stageMemory.bottleneck_stage ?? "Unknown")} />
            <InfoRow label="Items There" value={String(stageMemory.bottleneck_count ?? "0")} />
            <InfoRow label="Overdue" value={String(stageMemory.overdue_count ?? "0")} />
          </div>
          <DataTable rows={stageRows} columns={["stage", "count"]} />
        </Panel>
      </div>
      <div className="grid two-col">
        <Panel title="Title Patterns">
          <DataTable rows={titlePatterns} columns={["pattern", "type", "count"]} />
        </Panel>
        <Panel title="Content Pillars">
          <DataTable rows={pillarMemory} columns={["pillar", "count"]} />
        </Panel>
      </div>
    </section>
  );
}

function MemoryList({ items, empty }: { items: string[]; empty: string }) {
  if (!items.length) return <p>{empty}</p>;
  return (
    <div className="memory-list">
      {items.map((item) => <p key={item}>{item}</p>)}
    </div>
  );
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function asRecordList(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? value.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object" && !Array.isArray(item)) : [];
}

function asStringList(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item)).filter(Boolean) : [];
}

const ideationActions = [
  ["title_pack", "Title Pack"],
  ["hook_pack", "Hook Pack"],
  ["description_tags", "Description + Tags"],
  ["content_brief", "Content Brief"],
  ["fan_request_spin", "Ralskies Spin"]
] as const;

function IdeationPage() {
  const [topic, setTopic] = useStoredState("aria_ideation_topic", "");
  const [workingTitle, setWorkingTitle] = useStoredState("aria_ideation_working_title", "");
  const [action, setAction] = useStoredState("aria_ideation_action", "title_pack");
  const [output, setOutput] = useStoredState("aria_ideation_output", "");
  const [lastAction, setLastAction] = useStoredState("aria_ideation_last_action", "No generation yet.");
  const [score, setScore] = useStoredState<IdeationScorePayload>("aria_ideation_score", { keywords: [], scorecard: [] });
  const [status, setStatus] = useState("");

  async function refreshScore(nextTopic = topic, nextTitle = workingTitle) {
    if (!nextTopic.trim() && !nextTitle.trim()) {
      setScore({ keywords: [], scorecard: [] });
      return;
    }
    try {
      const result = await scoreIdeation(nextTopic, nextTitle);
      setScore(result);
      setStatus((current) => current === "Keyword scoring failed." ? "" : current);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Keyword scoring failed.");
    }
  }

  async function runGeneration(nextAction = action) {
    if (!topic.trim() && !workingTitle.trim()) {
      setStatus("Add a song concept or working title first.");
      return;
    }
    setStatus("A.R.I.A. is shaping the concept...");
    setOutput("");
    try {
      const result = await generateIdeation({
        topic,
        working_title: workingTitle,
        action: nextAction,
        fan_request: ""
      });
      setOutput(result.content);
      setLastAction(ideationActions.find(([key]) => key === nextAction)?.[1] ?? "A.R.I.A. Generation");
      setStatus("");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Generation failed.");
    }
  }

  function onTopicChange(value: string) {
    setTopic(value);
    refreshScore(value, workingTitle);
  }

  function onTitleChange(value: string) {
    setWorkingTitle(value);
    refreshScore(topic, value);
  }

  return (
    <section className="page-stack">
      <SectionHeader title="Ideation" copy="Develop covers, originals, and fan-requested songs into stronger theatrical concepts with A.R.I.A." />
      {status ? <div className="status">{status}</div> : null}
      <div className="grid two-col">
        <Panel title="Concept Builder">
          <div className="form-grid">
            <label className="field">
              <span>Song concept, niche direction, or cover idea</span>
              <textarea value={topic} onChange={(event) => onTopicChange(event.target.value)} rows={6} placeholder="male version of Pretty Little Baby with a softer Broadway ballad treatment" />
            </label>
            <label className="field">
              <span>Working title</span>
              <input value={workingTitle} onChange={(event) => onTitleChange(event.target.value)} placeholder="Pretty Little Baby (Male Version)" />
            </label>
            <label className="field">
              <span>Generation mode</span>
              <select value={action} onChange={(event) => setAction(event.target.value)}>
                {ideationActions.map(([key, label]) => <option value={key} key={key}>{label}</option>)}
              </select>
            </label>
            <div className="button-row">
              <button className="primary" onClick={() => runGeneration(action)}>Ask A.R.I.A.</button>
              <button onClick={() => { setOutput(""); setLastAction("Output cleared."); }}>Clear Output</button>
            </div>
          </div>
        </Panel>
        <Panel title="Keyword + Packaging Desk">
          <div className="score-list">
            {score.scorecard.length ? score.scorecard.map((item) => <InfoRow key={item.label} label={item.label} value={item.value} />) : <p>Add a topic or title to score packaging strength.</p>}
          </div>
          <DataTable rows={score.keywords} columns={["keyword", "demand", "competition", "channel_fit", "score"]} />
        </Panel>
      </div>
      <div className="grid two-col">
        <Panel title="Output Desk">
          <pre>{output || "Generated ideas will appear here."}</pre>
          <div className="info-row">
            <span>Last Action</span>
            <strong>{lastAction}</strong>
          </div>
        </Panel>
      </div>
    </section>
  );
}

function RepertoirePage({ data }: { data: BootstrapPayload }) {
  const [payload, setPayload] = useState<RepertoirePayload | null>(null);
  const [rows, setRows] = useState<Record<string, unknown>[]>(data.calendarRows);
  const [status, setStatus] = useState("");
  const [coachOutput, setCoachOutput] = useStoredState("aria_repertoire_coach_output", "");
  const [coachLoading, setCoachLoading] = useState(false);
  const stages = payload?.stages ?? ["Song Idea", "Instrumental Prep", "BandLab Recording", "Video Editing", "Upload"];
  const priorities = payload?.priorities ?? ["Low", "Medium", "High"];
  const boardGroups = [
    {
      label: "Song Ideas",
      rows: rows.filter((row) => {
        const pillar = String(row.content_pillar ?? "").toLowerCase();
        return !pillar.includes("collab") && String(row.stage ?? "") === "Song Idea";
      })
    },
    {
      label: "Collabs",
      rows: rows.filter((row) => String(row.content_pillar ?? "").toLowerCase().includes("collab"))
    }
  ];

  useEffect(() => {
    loadRepertoire()
      .then((result) => {
        setPayload(result);
        setRows(result.rows);
      })
      .catch((error: Error) => setStatus(error.message));
  }, []);

  function updateRow(index: number, key: string, value: string) {
    setRows(rows.map((row, rowIndex) => (rowIndex === index ? { ...row, [key]: value } : row)));
  }

  function addRow() {
    setRows([
      ...rows,
      {
        title: "",
        stage: stages[0],
        priority: "Medium",
        content_pillar: "",
        target_upload_date: "",
        notes: ""
      }
    ]);
  }

  function deleteRow(index: number) {
    setRows(rows.filter((_, rowIndex) => rowIndex !== index));
  }

  async function saveRows() {
    setStatus("Saving repertoire...");
    try {
      const result = await saveRepertoire(rows);
      setPayload(result);
      setRows(result.rows);
      setStatus("Repertoire saved.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Save failed.");
    }
  }

  async function coachRow(row: Record<string, unknown>) {
    setCoachLoading(true);
    setCoachOutput("A.R.I.A. is reviewing this idea...");
    const prompt = [
      "You are A.R.I.A. helping Ralskies sharpen one repertoire idea.",
      "Give a score out of 10, biggest upside, biggest risk, three improvements, and the next action.",
      `Title: ${String(row.title ?? "")}`,
      `Stage: ${String(row.stage ?? "")}`,
      `Priority: ${String(row.priority ?? "")}`,
      `Pillar: ${String(row.content_pillar ?? "")}`,
      `Target: ${String(row.target_upload_date ?? "")}`,
      `Notes: ${String(row.notes ?? "")}`
    ].join("\n");
    try {
      const response = await coachRepertoire(prompt);
      setCoachOutput(response.content);
    } catch (error) {
      setCoachOutput(error instanceof Error ? error.message : "Coach request failed.");
    } finally {
      setCoachLoading(false);
    }
  }

  return (
    <section className="page-stack">
      <SectionHeader title="Repertoire" copy="Your song pipeline, priorities, stages, and notes." />
      {status ? <div className="status">{status}</div> : null}
      <div className="grid stats-grid">
        <div className="metric-card"><span>Total Songs</span><strong>{payload?.summary.total ?? rows.length}</strong><small>active concepts</small></div>
        <div className="metric-card"><span>Ready</span><strong>{payload?.summary.ready ?? 0}</strong><small>in upload stage</small></div>
        <div className="metric-card"><span>Due Soon</span><strong>{payload?.summary.due_soon ?? 0}</strong><small>next 14 days</small></div>
        <div className="metric-card"><span>Collabs</span><strong>{boardGroups[1].rows.length}</strong><small>collab concepts</small></div>
      </div>
      <Panel title="Idea Board">
        <div className="board-grid">
          {boardGroups.map((group) => (
            <div className="lane" key={group.label}>
              <h3>{group.label}</h3>
              {group.rows.slice(0, 8).map((row, index) => (
                <button className="song-chip" key={`${group.label}-${index}-${String(row.title ?? "")}`} onClick={() => coachRow(row)}>
                  <strong>{String(row.title || "Untitled")}</strong>
                  <span>{String(row.priority || "Medium")} priority | {String(row.stage || "Song Idea")}</span>
                </button>
              ))}
              {!group.rows.length ? <p>No {group.label.toLowerCase()} yet.</p> : null}
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Edit Repertoire">
        <div className="editable-list">
          {rows.map((row, index) => (
            <div className="edit-row" key={index}>
              <input value={String(row.title ?? "")} onChange={(event) => updateRow(index, "title", event.target.value)} placeholder="Title" />
              <select value={String(row.stage ?? stages[0])} onChange={(event) => updateRow(index, "stage", event.target.value)}>
                {stages.map((stage) => <option key={stage}>{stage}</option>)}
              </select>
              <select value={String(row.priority ?? "Medium")} onChange={(event) => updateRow(index, "priority", event.target.value)}>
                {priorities.map((priority) => <option key={priority}>{priority}</option>)}
              </select>
              <input value={String(row.content_pillar ?? "")} onChange={(event) => updateRow(index, "content_pillar", event.target.value)} placeholder="Pillar" />
              <input type="date" value={String(row.target_upload_date ?? "").slice(0, 10)} onChange={(event) => updateRow(index, "target_upload_date", event.target.value)} />
              <input value={String(row.notes ?? "")} onChange={(event) => updateRow(index, "notes", event.target.value)} placeholder="Notes" />
              <button onClick={() => deleteRow(index)}>Delete</button>
            </div>
          ))}
        </div>
        <div className="button-row">
          <button onClick={addRow}>Add Song</button>
          <button className="primary" onClick={saveRows}>Save Repertoire</button>
        </div>
      </Panel>
      <Panel title="A.R.I.A. Notes">
        {coachLoading ? <div className="status">A.R.I.A. is reviewing this song...</div> : null}
        <pre>{coachOutput || "Select a song card to ask A.R.I.A. for focused feedback."}</pre>
      </Panel>
    </section>
  );
}

function CreatorActionsPage() {
  const [payload, setPayload] = useState<CreatorActionsPayload | null>(null);
  const [selectedVideoId, setSelectedVideoId] = useStoredState("aria_creator_selected_video_id", "");
  const [selectedVideoLabel, setSelectedVideoLabel] = useStoredState("aria_creator_selected_video_label", "");
  const [selectedReason, setSelectedReason] = useStoredState("aria_creator_selected_reason", "");
  const [status, setStatus] = useState("");
  const [title, setTitle] = useStoredState("aria_creator_title", "");
  const [description, setDescription] = useStoredState("aria_creator_description", "");
  const [tags, setTags] = useStoredState("aria_creator_tags", "");
  const [metadataDraft, setMetadataDraft] = useStoredState("aria_creator_metadata_draft", "");
  const [reviewed, setReviewed] = useState(false);
  const [preparing, setPreparing] = useState(false);

  useEffect(() => {
    loadCreatorActions()
      .then((result) => {
        setPayload(result);
        const savedAction = result.metadataActions.find((action) => action.video_id === selectedVideoId);
        const first = savedAction ?? result.metadataActions[0];
        if (first && !metadataDraft) {
          prepareMetadataAction(first, true);
        } else if (savedAction) {
          setSelectedVideoLabel(savedAction.label);
          setSelectedReason(savedAction.reason);
        }
      })
      .catch((error: Error) => setStatus(error.message));
  }, []);

  async function prepareMetadataAction(action: CreatorActionsPayload["metadataActions"][number], automatic = false) {
    setSelectedVideoId(action.video_id);
    setSelectedVideoLabel(action.label);
    setSelectedReason(action.reason);
    setReviewed(false);
    setPreparing(true);
    setStatus(automatic ? "Preparing the top metadata fix..." : "Preparing selected metadata fix...");
    setMetadataDraft("A.R.I.A. is drafting metadata...");
    setTitle(action.title);
    setDescription("");
    setTags("");
    try {
      const result = await loadMetadata(action.video_id);
      const currentTitle = result.metadata ? String(result.metadata.title ?? action.title) : action.title;
      if (result.metadata) {
        setTitle(currentTitle);
        setDescription(String(result.metadata.description ?? ""));
        setTags(Array.isArray(result.metadata.tags) ? result.metadata.tags.join(", ") : "");
      }
      const draft = await draftMetadata(action.label, `${action.reason}. ${action.suggestion}`, currentTitle);
      setMetadataDraft(draft.content);
      setStatus(result.message || "Metadata fix prepared.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Metadata preparation failed.");
      setMetadataDraft("");
    } finally {
      setPreparing(false);
    }
  }

  async function handleDraftMetadata() {
    if (!selectedVideoLabel) return;
    setPreparing(true);
    setMetadataDraft("A.R.I.A. is drafting metadata...");
    try {
      const result = await draftMetadata(selectedVideoLabel, selectedReason, title);
      setMetadataDraft(result.content);
      setStatus("Metadata draft refreshed.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Metadata draft failed.");
    } finally {
      setPreparing(false);
    }
  }

  async function handlePublishMetadata() {
    setStatus("Publishing metadata...");
    const result = await publishMetadata({
      video_id: selectedVideoId,
      title,
      description,
      tags: tags.split(",").map((tag) => tag.trim().replace(/^#/, "")).filter(Boolean),
      reviewed
    });
    setStatus(result.message);
  }

  const selectedAction = payload?.metadataActions.find((video) => video.video_id === selectedVideoId);

  return (
    <section className="page-stack">
      <SectionHeader title="Creator Actions" copy="A.R.I.A. prioritizes low-performing uploads and drafts metadata improvements for review." />
      {status ? <div className="status">{status}</div> : null}
      <Panel title="Safety Guardrails">
        <div className="guardrail-grid">
          {(payload?.guardrails ?? []).map(([label, value]) => <InfoRow key={label} label={label} value={value} />)}
        </div>
      </Panel>
      <Panel title="Metadata Actions">
        <div className="action-priority-list">
          {(payload?.metadataActions ?? []).length ? payload?.metadataActions.map((action) => (
            <button
              className={selectedVideoId === action.video_id ? "active" : ""}
              key={action.video_id}
              onClick={() => prepareMetadataAction(action)}
              disabled={preparing}
            >
              <strong>{action.title}</strong>
              <span>{action.reason} | {action.views.toLocaleString()} views | {Math.round(action.retention)}% retention</span>
              <small>{action.suggestion}</small>
            </button>
          )) : <p>No low-performing metadata actions were loaded yet.</p>}
        </div>
        {selectedAction ? (
          <div className="creator-action-summary">
            <InfoRow label="Priority" value={selectedAction.reason} />
            <InfoRow label="Views" value={selectedAction.views.toLocaleString()} />
            <InfoRow label="Retention" value={`${Math.round(selectedAction.retention)}%`} />
            <InfoRow label="Score" value={String(Math.round(selectedAction.engagement_score))} />
            <InfoRow label="Suggested Fix" value={selectedAction.suggestion} />
          </div>
        ) : null}
        <div className="form-grid">
          <div className="button-row">
            {selectedAction ? <button onClick={() => prepareMetadataAction(selectedAction)} disabled={preparing}>Reload Current Metadata</button> : null}
            <button onClick={handleDraftMetadata} disabled={preparing || !selectedVideoId}>Refresh AI Draft</button>
          </div>
          <label className="field"><span>Title</span><input value={title} onChange={(event) => setTitle(event.target.value)} maxLength={100} /></label>
          <label className="field"><span>Description</span><textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={8} /></label>
          <label className="field"><span>Tags</span><textarea value={tags} onChange={(event) => setTags(event.target.value)} rows={4} /></label>
          <label className="check-row"><input type="checkbox" checked={reviewed} onChange={(event) => setReviewed(event.target.checked)} /> I reviewed this metadata and want to publish it.</label>
          <button className="primary" disabled={!reviewed || !selectedVideoId} onClick={handlePublishMetadata}>Publish Metadata Update</button>
          <pre>{metadataDraft || "A.R.I.A. metadata draft will appear here."}</pre>
        </div>
      </Panel>
    </section>
  );
}

function VaultPage() {
  const [payload, setPayload] = useState<VaultPayload | null>(null);
  const [settings, setSettings] = useState<VaultPayload["settings"] | null>(null);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [lastRefreshMessages, setLastRefreshMessages] = useState<Record<string, string>>({});

  useEffect(() => {
    loadVault()
      .then((result) => {
        setPayload(result);
        setSettings(result.settings);
      })
      .catch((error: Error) => setStatus(error.message));
  }, []);

  function updateSetting(key: keyof VaultPayload["settings"], value: string) {
    if (!settings) return;
    setSettings({ ...settings, [key]: value });
  }

  async function saveSettings() {
    if (!settings) return;
    setStatus("Saving vault...");
    try {
      const result = await saveVault({ ...settings });
      setPayload(result);
      setSettings(result.settings);
      setStatus("Vault settings saved.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Vault save failed.");
    }
  }

  async function reconnectYoutube() {
    setBusy(true);
    setStatus("Opening YouTube authorization...");
    try {
      const result = await authorizeYoutube();
      setPayload(result);
      setSettings(result.settings);
      setStatus(result.message || result.connection.message);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "YouTube authorization failed.");
    } finally {
      setBusy(false);
    }
  }

  async function removeToken() {
    setBusy(true);
    setStatus("Removing saved YouTube token...");
    try {
      const result = await clearYoutubeToken();
      setPayload(result);
      setSettings(result.settings);
      setStatus(result.message || result.connection.message);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Could not clear the YouTube token.");
    } finally {
      setBusy(false);
    }
  }

  async function refreshYoutubeSnapshot() {
    setBusy(true);
    setStatus("Checking latest YouTube data and saving today's snapshot...");
    try {
      const result = await checkLatestYoutubeData();
      const messages = Object.entries(result.messages)
        .map(([label, value]) => `${label}: ${value}`)
        .join("\n");
      setLastRefreshMessages(result.messages);
      setStatus(messages || (result.success ? "Latest YouTube data saved." : "No YouTube data was refreshed."));
      setPayload((current) => current ? { ...current, cache: result.cache } : current);
      loadVault().then((nextPayload) => {
        setPayload(nextPayload);
        setSettings(nextPayload.settings);
      });
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Latest YouTube data check failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="page-stack">
      <SectionHeader title="The Vault" copy="Store local defaults, model preferences, and YouTube credentials for the Python engine." />
      {status ? <div className="status">{status}</div> : null}
      <div className="grid three-col">
        <div className="metric-card"><span>API Key</span><strong>{payload?.connection.api_key ? "Yes" : "No"}</strong><small>YouTube Data API</small></div>
        <div className="metric-card"><span>OAuth Client</span><strong>{payload?.connection.oauth_client ? "Yes" : "No"}</strong><small>write access setup</small></div>
        <div className="metric-card"><span>Token</span><strong>{payload?.connection.token ? "Yes" : "No"}</strong><small>saved locally</small></div>
      </div>
      <Panel title="YouTube Connection">
        <InfoRow label="Status" value={payload?.connection.message ?? "Loading connection status..."} />
        {Object.keys(lastRefreshMessages).length ? (
          <div className="refresh-result">
            {Object.entries(lastRefreshMessages).map(([label, value]) => (
              <div key={label}>
                <span>{label}</span>
                <strong>{value.includes("Saved to today's local cache") ? "Saved today" : value.includes("Using last saved cache") ? "Stored fallback" : "Checked"}</strong>
              </div>
            ))}
          </div>
        ) : null}
        <div className="button-row">
          <button onClick={reconnectYoutube} disabled={busy || !payload?.connection.oauth_client}>Reconnect YouTube</button>
          <button onClick={refreshYoutubeSnapshot} disabled={busy || !payload?.connection.token}>Check Latest Data</button>
          <button onClick={removeToken} disabled={busy || !payload?.connection.token}>Clear Token</button>
        </div>
      </Panel>
      <Panel title="Data Freshness">
        {payload?.cache.length ? (
          <div className="freshness-list">
            {payload.cache.map((row) => (
              <article className="freshness-row" key={row.cache_key}>
                <div>
                  <strong>{row.dataset}</strong>
                  <span>{row.status}</span>
                </div>
                <div>
                  <small>Latest data</small>
                  <strong>{row.latest_data_date || "None"}</strong>
                </div>
                <div>
                  <small>Today</small>
                  <strong>{row.today_date || "Not checked"}</strong>
                </div>
                <p>{row.message || "No cache note recorded."}</p>
              </article>
            ))}
          </div>
        ) : <p>No YouTube cache rows have been recorded yet.</p>}
      </Panel>
      <Panel title="Settings">
        {settings ? (
          <div className="form-grid">
            <label className="field"><span>Model Name</span><input value={settings.model_name} onChange={(event) => updateSetting("model_name", event.target.value)} /></label>
            <label className="field"><span>Model Endpoint</span><input value={settings.model_endpoint} onChange={(event) => updateSetting("model_endpoint", event.target.value)} /></label>
            <label className="field"><span>Default Description</span><textarea value={settings.default_description} onChange={(event) => updateSetting("default_description", event.target.value)} rows={8} /></label>
            <label className="field"><span>YouTube API Key</span><input type="password" value={settings.youtube_api_key} onChange={(event) => updateSetting("youtube_api_key", event.target.value)} /></label>
            <label className="field"><span>YouTube Client ID</span><input type="password" value={settings.youtube_client_id} onChange={(event) => updateSetting("youtube_client_id", event.target.value)} /></label>
            <label className="field"><span>YouTube Client Secret</span><input type="password" value={settings.youtube_client_secret} onChange={(event) => updateSetting("youtube_client_secret", event.target.value)} /></label>
            <button className="primary" onClick={saveSettings}>Save Vault Settings</button>
          </div>
        ) : <p>Loading vault settings...</p>}
      </Panel>
    </section>
  );
}

function ShortsArchitectPage() {
  const [mainVideo, setMainVideo] = useState<File | null>(null);
  const [brollVideo, setBrollVideo] = useState<File | null>(null);
  const [vaultSettings, setVaultSettings] = useState<VaultPayload["settings"] | null>(null);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [layout, setLayout] = useStoredState("aria_shorts_layout", "Solo Mode");
  const [captionTone, setCaptionTone] = useStoredState("aria_shorts_caption_tone", "#ffd166");
  const [objective, setObjective] = useStoredState("aria_shorts_objective", "Retention hook");
  const [whisperModel, setWhisperModel] = useStoredState("aria_shorts_whisper_model", "small");
  const [visionModel, setVisionModel] = useStoredState("aria_shorts_vision_model", "");
  const [status, setStatus] = useState("");
  const [diagnostics, setDiagnostics] = useStoredState<string[]>("aria_shorts_diagnostics", []);
  const [analyzing, setAnalyzing] = useState(false);
  const [rendering, setRendering] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [result, setResult] = useStoredState<ShortsAiAnalyzePayload | null>("aria_shorts_result", null);
  const [renderResult, setRenderResult] = useStoredState<ShortsRenderPayload | null>("aria_shorts_render_result", null);
  const [previewResult, setPreviewResult] = useState<ShortsPreviewPayload | null>(null);
  const [editableShorts, setEditableShorts] = useStoredState<ShortsPlanClip[]>("aria_shorts_editable_plan", []);
  const [projectId, setProjectId] = useStoredState("aria_shorts_project_id", "");
  const [projectTitle, setProjectTitle] = useStoredState("aria_shorts_project_title", "Untitled Shorts Project");
  const [savedProjects, setSavedProjects] = useState<ShortsProjectPayload[]>([]);
  const [projectBusy, setProjectBusy] = useState(false);
  const aiShorts = editableShorts;
  const activeVisionModel = visionModel.trim();
  const mainVideoDuration = Number(result?.mainVideo?.duration_seconds ?? 0);
  const brollVideoDuration = Number(result?.brollVideo?.duration_seconds ?? 0);
  const invalidCutCount = aiShorts.filter((clip) => {
    const start = Number(clip.start ?? 0);
    const end = Number(clip.end ?? 0);
    if (!(end > start)) return true;
    if (mainVideoDuration > 0 && end > mainVideoDuration) return true;
    return false;
  }).length;
  const hasInvalidCuts = invalidCutCount > 0;
  const duetMissingBroll = layout === "Duet Mode" && !result?.broll_video_path;
  const duetCutsExceedBroll = layout === "Duet Mode" && brollVideoDuration > 0 && aiShorts.some((clip) => {
    const start = Number(clip.start ?? 0);
    const end = Number(clip.end ?? 0);
    return end > start && (end - start) > brollVideoDuration;
  });
  const previewFramesByIndex = useMemo(
    () => new Map((previewResult?.frames ?? []).map((frame) => [frame.index, frame])),
    [previewResult]
  );

  useEffect(() => {
    loadVault()
      .then((payload) => {
        setVaultSettings(payload.settings);
        setAvailableModels(payload.available_models);
        setVisionModel((current) => {
          if (current && payload.available_models.includes(current)) return current;
          return payload.available_models.includes(payload.settings.model_name) ? payload.settings.model_name : (payload.available_models[0] || "");
        });
      })
      .catch(() => {
        setVaultSettings(null);
        setAvailableModels([]);
      });
  }, []);

  useEffect(() => {
    listShortsProjects()
      .then((payload) => setSavedProjects(payload.projects))
      .catch(() => setSavedProjects([]));
  }, []);

  async function runAiDirector() {
    if (!mainVideo || analyzing) return;
    setAnalyzing(true);
    setDiagnostics([]);
    setStatus("A.R.I.A. is listening to the full performance, finding moments, and writing the cuts...");
    try {
      const nextResult = await analyzeShortsWithAi({
        mainVideo,
        brollVideo,
        whisperModel,
        layoutMode: layout,
        objective,
        visionModel: activeVisionModel
      });
      if (nextResult.success === false) {
        setStatus(nextResult.message || "AI Shorts analysis failed.");
        setDiagnostics(nextResult.warnings ?? []);
        setResult(null);
        setEditableShorts([]);
        return;
      }
      setResult(nextResult);
      const nextShorts = nextResult.aiPlan?.shorts ?? [];
      setEditableShorts(nextShorts);
      setRenderResult(null);
      setPreviewResult(null);
      setProjectId("");
      setProjectTitle(nextResult.aiPlan?.video_title || mainVideo.name.replace(/\.[^.]+$/, "") || "Untitled Shorts Project");
      setDiagnostics(nextResult.warnings ?? []);
      setStatus(nextResult.message || `AI plan ready: ${nextResult.aiPlan?.shorts?.length ?? 0} cut(s) selected.`);
      if (nextShorts.length) {
        refreshCutPreviews(nextResult.main_video_path, nextShorts);
      }
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "AI Shorts analysis failed.");
    } finally {
      setAnalyzing(false);
    }
  }

  function updateShort(index: number, patch: Partial<ShortsPlanClip>) {
    setEditableShorts((current) => current.map((clip, clipIndex) => clipIndex === index ? { ...clip, ...patch } : clip));
    setPreviewResult(null);
  }

  function updateCaptionLines(index: number, value: string) {
    updateShort(index, { caption_lines: value.split("\n").map((line) => line.trim()).filter(Boolean) });
  }

  function removeShort(index: number) {
    setEditableShorts((current) => current.filter((_, clipIndex) => clipIndex !== index));
    setPreviewResult(null);
  }

  function duplicateShort(index: number) {
    setEditableShorts((current) => {
      const clip = current[index];
      if (!clip) return current;
      const duplicate = {
        ...clip,
        title: clip.title ? `${clip.title} Copy` : `Cut ${index + 1} Copy`,
      };
      return [...current.slice(0, index + 1), duplicate, ...current.slice(index + 1)];
    });
    setPreviewResult(null);
  }

  function addManualCut() {
    setEditableShorts((current) => [
      ...current,
      {
        segment_id: current.length + 1,
        start: 0,
        end: 15,
        title: `Manual Cut ${current.length + 1}`,
        hook: "Start with the strongest lyric or beat drop",
        caption_lines: ["Hook line", "Payoff line"],
        reason: "Manual cut added in Shorts Architect.",
        score: 60,
      }
    ]);
    setPreviewResult(null);
    setStatus("Added a manual cut. Adjust the timing before preview or render.");
  }

  function restoreAiPlan() {
    setEditableShorts(result?.aiPlan?.shorts ?? []);
    setRenderResult(null);
    setPreviewResult(null);
    setStatus("Restored the original AI-selected Shorts plan.");
  }

  async function saveCurrentProject() {
    if (!result || projectBusy) return;
    setProjectBusy(true);
    setStatus("Saving Shorts project locally...");
    try {
      const saved = await saveShortsProject({
        id: projectId,
        title: projectTitle,
        payload: {
          result,
          editableShorts,
          renderResult,
          previewResult,
          layout,
          captionTone,
          objective,
          whisperModel,
          visionModel
        }
      });
      setProjectId(saved.project.id);
      setProjectTitle(saved.project.title);
      setSavedProjects(saved.projects);
      setStatus(saved.message);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Could not save Shorts project.");
    } finally {
      setProjectBusy(false);
    }
  }

  async function openProject(nextProjectId: string) {
    if (!nextProjectId || projectBusy) return;
    setProjectBusy(true);
    setStatus("Opening saved Shorts project...");
    try {
      const loaded = await loadShortsProject(nextProjectId);
      if (!loaded.project) {
        setStatus(loaded.message);
        return;
      }
      const payload = loaded.project.payload;
      setProjectId(loaded.project.id);
      setProjectTitle(loaded.project.title);
      setResult(payload.result ?? null);
      setEditableShorts(payload.editableShorts ?? payload.result?.aiPlan?.shorts ?? []);
      setRenderResult(payload.renderResult ?? null);
      setPreviewResult(payload.previewResult ?? null);
      setLayout(payload.layout ?? "Solo Mode");
      setCaptionTone(payload.captionTone ?? "#ffd166");
      setObjective(payload.objective ?? "Retention hook");
      setWhisperModel(payload.whisperModel ?? "small");
      setVisionModel(payload.visionModel ?? "");
      setStatus(loaded.message);
      if (!payload.previewResult?.frames?.length && payload.result?.main_video_path && (payload.editableShorts ?? payload.result?.aiPlan?.shorts ?? []).length) {
        refreshCutPreviews(payload.result.main_video_path, payload.editableShorts ?? payload.result.aiPlan?.shorts ?? []);
      }
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Could not open Shorts project.");
    } finally {
      setProjectBusy(false);
    }
  }

  async function removeCurrentProject() {
    if (!projectId || projectBusy) return;
    setProjectBusy(true);
    setStatus("Deleting saved Shorts project...");
    try {
      const deleted = await deleteShortsProject(projectId);
      setSavedProjects(deleted.projects);
      setProjectId("");
      setStatus(deleted.message);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Could not delete Shorts project.");
    } finally {
      setProjectBusy(false);
    }
  }

  async function refreshCutPreviews(mainVideoPath = result?.main_video_path ?? "", shorts = editableShorts) {
    if (!mainVideoPath || !shorts.length || previewing) return;
    setPreviewing(true);
    try {
      const nextPreview = await previewShortsFromAiPlan({
        mainVideoPath,
        shorts
      });
      setPreviewResult(nextPreview);
      setStatus(nextPreview.message);
      if (!nextPreview.success) {
        setDiagnostics((current) => [nextPreview.message, ...current].slice(0, 5));
      }
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Could not build cut previews.");
    } finally {
      setPreviewing(false);
    }
  }

  async function renderAiPlan() {
    if (!result || !aiShorts.length || hasInvalidCuts || duetMissingBroll || duetCutsExceedBroll || rendering) return;
    setRendering(true);
    setStatus("Rendering the AI-selected Shorts into local MP4 exports...");
    try {
      const nextRender = await renderShortsFromAiPlan({
        mainVideoPath: result.main_video_path,
        brollVideoPath: result.broll_video_path,
        shorts: editableShorts,
        layoutMode: layout,
        textColor: captionTone
      });
      setRenderResult(nextRender);
      setStatus(nextRender.message);
      if (!nextRender.success) {
        setDiagnostics((current) => [nextRender.message, ...current].slice(0, 5));
      }
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Shorts render failed.");
    } finally {
      setRendering(false);
    }
  }

  return (
    <section className="page-stack">
      <SectionHeader title="Shorts Architect" copy="Upload the full performance. A.R.I.A. listens, finds moments, writes captions, and chooses the cuts." />
      {status ? <div className="status">{status}</div> : null}
      {diagnostics.length ? (
        <Panel title="Shorts Diagnostics">
          <div className="caption-lines">
            {diagnostics.map((item, index) => <p key={`${item}-${index}`}>{item}</p>)}
          </div>
        </Panel>
      ) : null}
      <div className="shorts-shell">
        <Panel title="AI Director">
          <div className="form-grid">
            <label className="field">
              <span>Saved Project</span>
              <select value={projectId} onChange={(event) => openProject(event.target.value)} disabled={projectBusy || !savedProjects.length}>
                <option value="">{savedProjects.length ? "Open saved Shorts project" : "No saved Shorts projects"}</option>
                {savedProjects.map((project) => (
                  <option value={project.id} key={project.id}>{project.title} | {project.updated_at}</option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Project Title</span>
              <input value={projectTitle} onChange={(event) => setProjectTitle(event.target.value)} />
            </label>
            <div className="button-row">
              <button disabled={!result || projectBusy} onClick={saveCurrentProject}>{projectBusy ? "Working..." : "Save Project"}</button>
              <button disabled={!projectId || projectBusy} onClick={removeCurrentProject}>Delete Saved Project</button>
            </div>
            {result ? (
              <div className="shorts-source-summary">
                <div className="source-chip">
                  <strong>Main Video</strong>
                  <span>{result.mainVideo?.filename || result.main_video_path.split(/[\\/]/).pop() || "Uploaded video"}</span>
                  <small>{mainVideoDuration ? `${mainVideoDuration.toFixed(1)}s loaded` : "Duration unavailable"}</small>
                </div>
                <div className="source-chip">
                  <strong>B-Roll</strong>
                  <span>{result.brollVideo?.filename || (result.broll_video_path ? result.broll_video_path.split(/[\\/]/).pop() : "Not loaded")}</span>
                  <small>{brollVideoDuration ? `${brollVideoDuration.toFixed(1)}s loaded` : "Optional for Solo Mode"}</small>
                </div>
              </div>
            ) : null}
            <label className="field">
              <span>Main Performance Video</span>
              <input type="file" accept="video/*" onChange={(event) => setMainVideo(event.target.files?.[0] ?? null)} />
            </label>
            <label className="field">
              <span>B-Roll / Reference Video</span>
              <input type="file" accept="video/*" onChange={(event) => setBrollVideo(event.target.files?.[0] ?? null)} />
            </label>
            <label className="field">
              <span>Objective</span>
              <select value={objective} onChange={(event) => setObjective(event.target.value)}>
                {["Retention hook", "Comment magnet", "Chorus payoff", "Fanskies teaser"].map((item) => <option key={item}>{item}</option>)}
              </select>
            </label>
            <div className="segmented">
              {["Solo Mode", "Duet Mode"].map((item) => (
                <button className={layout === item ? "active" : ""} onClick={() => setLayout(item)} key={item}>{item}</button>
              ))}
            </div>
            <label className="field">
              <span>Whisper Model</span>
              <select value={whisperModel} onChange={(event) => setWhisperModel(event.target.value)}>
                {["tiny", "base", "small", "medium"].map((item) => <option key={item}>{item}</option>)}
              </select>
            </label>
            <label className="field">
              <span>Vision Model</span>
              <select value={visionModel} onChange={(event) => setVisionModel(event.target.value)} disabled={!availableModels.length}>
                <option value="">{availableModels.length ? "Visual pass off" : "No models found"}</option>
                {availableModels.map((model) => <option value={model} key={model}>{model}</option>)}
              </select>
            </label>
            <div className="swatch-row">
              {["#ffd166", "#f8fafc", "#38bdf8", "#fb7185"].map((color) => (
                <button
                  aria-label={`Caption color ${color}`}
                  className={captionTone === color ? "active" : ""}
                  key={color}
                  onClick={() => setCaptionTone(color)}
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
            <button className="primary" disabled={!mainVideo || analyzing} onClick={runAiDirector}>
              {analyzing ? "A.R.I.A. Is Directing..." : "Let A.R.I.A. Create The Shorts"}
            </button>
            <button disabled={!aiShorts.length || hasInvalidCuts || duetMissingBroll || duetCutsExceedBroll || rendering || analyzing} onClick={renderAiPlan}>
              {rendering ? "Rendering MP4s..." : "Render AI Plan"}
            </button>
          </div>
        </Panel>
        <div className="shorts-preview">
          <div className={layout === "Duet Mode" ? "phone-frame duet" : "phone-frame"}>
            <div className="preview-video-layer">
              <span>{layout === "Duet Mode" ? "Reference" : "Performance"}</span>
            </div>
            {layout === "Duet Mode" ? <div className="preview-video-layer bottom"><span>Ralskies</span></div> : null}
            <div className="caption-preview" style={{ color: captionTone }}>{aiShorts[0]?.hook ?? "A.R.I.A. picks the hook"}</div>
          </div>
        </div>
      </div>
      <Panel title="AI-Selected Cuts">
        <div className="clip-editor-topline">
          <span>
            {hasInvalidCuts
              ? `${invalidCutCount} cut(s) need timing fixes before render`
              : duetMissingBroll
                ? "Duet Mode needs B-Roll before render"
                : duetCutsExceedBroll
                  ? "At least one cut is longer than the loaded B-Roll"
                  : aiShorts.length
                    ? `${aiShorts.length} editable cut(s)`
                    : "No cuts selected yet"}
          </span>
          <div className="button-row">
            <button disabled={!result?.main_video_path || !aiShorts.length || hasInvalidCuts || previewing} onClick={() => refreshCutPreviews()}>
              {previewing ? "Building Previews..." : "Refresh Previews"}
            </button>
            <button disabled={!result?.aiPlan?.shorts?.length} onClick={restoreAiPlan}>Restore AI Plan</button>
            <button onClick={addManualCut}>Add Manual Cut</button>
          </div>
        </div>
        <div className="clip-editor-grid">
          {aiShorts.length ? aiShorts.map((clip, index) => (
            <article className="clip-editor-card" key={`${clip.segment_id ?? index}-${index}`}>
              <div className="clip-editor-heading">
                <span>Cut {index + 1}</span>
                <strong>{Number(clip.score ?? 0).toFixed(0)}/100</strong>
              </div>
              <div className="clip-meta-row">
                <span>{Math.max(Number(clip.end ?? 0) - Number(clip.start ?? 0), 0).toFixed(1)}s duration</span>
                <span>
                  {mainVideoDuration && Number(clip.end ?? 0) > mainVideoDuration
                    ? `Exceeds main video (${mainVideoDuration.toFixed(1)}s)`
                    : layout === "Duet Mode" && brollVideoDuration && (Number(clip.end ?? 0) - Number(clip.start ?? 0)) > brollVideoDuration
                      ? `Longer than B-Roll (${brollVideoDuration.toFixed(1)}s)`
                      : "Timing looks valid"}
                </span>
              </div>
              {previewFramesByIndex.get(index) ? (
                <figure className="cut-preview-frame">
                  <img src={previewFramesByIndex.get(index)?.imageDataUrl} alt={`Preview frame for cut ${index + 1}`} />
                  <figcaption>{Number(previewFramesByIndex.get(index)?.timestamp ?? 0).toFixed(1)}s preview frame</figcaption>
                </figure>
              ) : null}
              <div className="time-grid">
                <label className="field">
                  <span>Start</span>
                  <input type="number" min="0" step="0.1" value={Number(clip.start ?? 0)} onChange={(event) => updateShort(index, { start: Number(event.target.value) })} />
                </label>
                <label className="field">
                  <span>End</span>
                  <input type="number" min="0" step="0.1" value={Number(clip.end ?? 0)} onChange={(event) => updateShort(index, { end: Number(event.target.value) })} />
                </label>
              </div>
              <label className="field">
                <span>Title</span>
                <input value={clip.title ?? ""} onChange={(event) => updateShort(index, { title: event.target.value })} />
              </label>
              <label className="field">
                <span>Hook</span>
                <input value={clip.hook ?? ""} onChange={(event) => updateShort(index, { hook: event.target.value })} />
              </label>
              <label className="field">
                <span>Captions</span>
                <textarea rows={4} value={(clip.caption_lines ?? []).join("\n")} onChange={(event) => updateCaptionLines(index, event.target.value)} />
              </label>
              <label className="field">
                <span>Reason</span>
                <textarea rows={3} value={clip.reason ?? ""} onChange={(event) => updateShort(index, { reason: event.target.value })} />
              </label>
              <div className="button-row">
                <button onClick={() => duplicateShort(index)}>Duplicate Cut</button>
                <button onClick={() => removeShort(index)}>Remove Cut</button>
              </div>
            </article>
          )) : <p>Upload a full performance and let A.R.I.A. select the cuts.</p>}
        </div>
      </Panel>
      <div className="grid two-col">
        <Panel title="Posting Notes">
          <div className="caption-lines">
            {result?.aiPlan?.posting_notes?.length ? result.aiPlan.posting_notes.map((note, index) => (
              <p key={`${note}-${index}`}>{note}</p>
            )) : <p>AI posting notes will appear here after analysis.</p>}
          </div>
        </Panel>
        <Panel title="Local Render Path">
          <div className="render-spec">
            <InfoRow label="Director" value="A.R.I.A. chooses cuts, titles, hooks, captions" />
            <InfoRow label="Listening" value="Librosa + Faster Whisper" />
            <InfoRow label="Visual Pass" value={activeVisionModel || "Off until a local vision model is set"} />
            <InfoRow label="Layout" value={layout} />
            <InfoRow label="Main Runtime" value={mainVideoDuration ? `${mainVideoDuration.toFixed(1)}s` : "Load a main video"} />
            <InfoRow label="B-Roll Runtime" value={brollVideoDuration ? `${brollVideoDuration.toFixed(1)}s` : "Optional"} />
            <InfoRow label="Export" value="MoviePy + FFmpeg" />
            <InfoRow label="Output" value={renderResult?.outputs.length ? `${renderResult.outputs.length} file(s) in shorts_output/` : "shorts_output/"} />
            <InfoRow label="Render Readiness" value={duetMissingBroll ? "Needs B-Roll for Duet Mode" : duetCutsExceedBroll ? "Shorten cuts or load longer B-Roll" : hasInvalidCuts ? "Fix cut timing" : aiShorts.length ? "Ready after review" : "Run AI Director first"} />
          </div>
        </Panel>
      </div>
      {renderResult?.outputs.length ? (
        <Panel title="Rendered Exports">
          <div className="freshness-list">
            {renderResult.outputs.map((output) => (
              <article className="freshness-row" key={output}>
                <div>
                  <strong>{output.split(/[\\/]/).pop()}</strong>
                  <span>Local MP4 export</span>
                </div>
                <p>{output}</p>
              </article>
            ))}
          </div>
        </Panel>
      ) : null}
      {result?.visualNotes ? (
        <Panel title="AI Visual / Context Notes">
          <pre>{result.visualNotes}</pre>
        </Panel>
      ) : null}
    </section>
  );
}

function WorkspacePage({ title, mode }: { title: string; data: BootstrapPayload; mode: string }) {
  return (
    <section className="page-stack">
      <SectionHeader title={title} copy="This workspace is ready for the next React polish pass." />
      <Panel title="Migration Slot">
        <p>{mode} will keep using the existing Python engine while the UI becomes editable React components.</p>
      </Panel>
    </section>
  );
}

function Hero({ data }: { data: BootstrapPayload }) {
  return (
    <header className="hero">
      <span>{data.profile.handle}</span>
      <h1>{data.profile.title}</h1>
      <p>A.R.I.A. turns channel pulse, upload history, and repertoire context into decisions you can act on.</p>
    </header>
  );
}

function SectionHeader({ title, copy }: { title: string; copy: string }) {
  return (
    <header className="section-header">
      <h1>{title}</h1>
      <p>{copy}</p>
    </header>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <article className="panel">
      <h2>{title}</h2>
      {children}
    </article>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="info-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function RecordSummary({ record }: { record: Record<string, unknown> }) {
  return (
    <div className="record-summary">
      <strong>{String(record.title ?? "Untitled")}</strong>
      <span>{Number(record.views ?? 0).toLocaleString()} views</span>
      <span>{Number(record.retention ?? 0).toFixed(1)}% retention</span>
    </div>
  );
}

function Sparkline({ rows, metric }: { rows: Record<string, unknown>[]; metric: string }) {
  const values = rows
    .map((row) => row[metric])
    .filter((value) => value !== null && value !== undefined && value !== "")
    .map((value) => Number(value))
    .filter((value) => Number.isFinite(value));
  if (values.length < 2) return <p>No chart data loaded for {metric.replaceAll("_", " ")}.</p>;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const spread = max - min || 1;
  const points = values.map((value, index) => {
    const x = (index / Math.max(values.length - 1, 1)) * 100;
    const y = 100 - ((value - min) / spread) * 82 - 9;
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(" ");
  const latest = values[values.length - 1];
  const previous = values[values.length - 2];
  const direction = latest >= previous ? "up" : "down";

  return (
    <div className="sparkline-shell">
      <svg className="sparkline" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label={`${metric} trend`}>
        <polyline points={points} />
      </svg>
      <div className="sparkline-meta">
        <strong>{formatMetric(latest, metric)}</strong>
        <span className={direction}>{direction === "up" ? "Rising" : "Softening"} from prior point</span>
        <small>{rows.length} loaded day(s)</small>
      </div>
    </div>
  );
}

function MetricDetailTable({ rows, metric }: { rows: Record<string, unknown>[]; metric: string }) {
  const recentRows = rows
    .slice(-12)
    .filter((row) => row[metric] !== null && row[metric] !== undefined && row[metric] !== "")
    .map((row) => ({
      date: String(row.date ?? ""),
      [metric]: formatMetric(Number(row[metric]), metric)
    }));
  return <DataTable rows={recentRows} columns={["date", metric]} />;
}

function formatMetric(value: number, metric: string) {
  if (metric === "views") return Math.round(value).toLocaleString();
  if (metric === "watch_time_hours") return `${Math.round(value).toLocaleString()}h`;
  return `${Math.round(value)}%`;
}

function DataTable({ rows, columns }: { rows: Record<string, unknown>[]; columns: string[] }) {
  if (!rows.length) return <p>No rows loaded.</p>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column.replaceAll("_", " ")}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map((column) => (
                <td key={column}>{formatCellValue(row[column])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatCellValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "Unavailable";
  if (typeof value === "number") return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(1);
  return String(value);
}
