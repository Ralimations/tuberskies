import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  askAria,
  coachRepertoire,
  draftComment,
  draftMetadata,
  loadBootstrap,
  loadComments,
  loadCreatorActions,
  loadMetadata,
  loadRepertoire,
  loadVault,
  publishComment,
  publishMetadata,
  saveRepertoire,
  saveVault
} from "./api";
import { Icon } from "./icons";
import type { BootstrapPayload, ChatMessage, CommentRow, CreatorActionsPayload, NavItem, RepertoirePayload, VaultPayload } from "./types";

const fallbackData: BootstrapPayload = {
  navigation: [
    { label: "Ask A.R.I.A.", path: "/", icon: "comments", group: "Home" },
    { label: "Analytics", path: "/analytics", icon: "chart", group: "Home" },
    { label: "Creator Actions", path: "/creator-actions", icon: "reply", group: "Home" },
    { label: "Upload Lab", path: "/upload-lab", icon: "upload", group: "More tools" },
    { label: "Pattern Memory", path: "/pattern-memory", icon: "memory", group: "More tools" },
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
  messages: {}
};

function currentPath() {
  return window.location.pathname || "/";
}

export function App() {
  const [data, setData] = useState<BootstrapPayload>(fallbackData);
  const [path, setPath] = useState(currentPath());
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

  function navigate(item: NavItem) {
    window.history.pushState({}, "", item.path);
    setPath(item.path);
  }

  return (
    <div className="studio-shell">
      <Sidebar items={data.navigation} activePath={path} onNavigate={navigate} />
      <main className="workspace">
        {loadError ? <div className="status error">{loadError}</div> : null}
        {loading ? <div className="status">Loading A.R.I.A. context...</div> : null}
        {path === "/" ? <AskPage data={data} /> : null}
        {path === "/analytics" ? <AnalyticsPage data={data} /> : null}
        {path === "/creator-actions" ? <CreatorActionsPage /> : null}
        {path === "/upload-lab" ? <UploadLabPage data={data} /> : null}
        {path === "/pattern-memory" ? <PatternPage data={data} /> : null}
        {path === "/ideation" ? <WorkspacePage title="Ideation" data={data} mode="ideation" /> : null}
        {path === "/repertoire" ? <RepertoirePage data={data} /> : null}
        {path === "/shorts" ? <WorkspacePage title="Shorts Architect" data={data} mode="shorts" /> : null}
        {path === "/vault" ? <VaultPage /> : null}
      </main>
    </div>
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
      <button className="new-brief" onClick={() => onNavigate(items[0])}>
        New Brief
      </button>
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
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Ask me what to fix, repeat, post, package, or turn into Shorts. I am reading the current analytics context for this session."
    }
  ]);
  const [draft, setDraft] = useState("");
  const [thinking, setThinking] = useState(false);

  async function submitMessage(message: string) {
    const clean = message.trim();
    if (!clean || thinking) return;
    const latestUser = [...messages].reverse().find((item) => item.role === "user");
    if (latestUser?.content === clean) return;

    const nextMessages: ChatMessage[] = [...messages, { role: "user", content: clean }];
    setMessages(nextMessages);
    setDraft("");
    setThinking(true);
    try {
      const response = await askAria(clean, nextMessages);
      setMessages([...nextMessages, response]);
    } catch (error) {
      setMessages([
        ...nextMessages,
        {
          role: "assistant",
          content: error instanceof Error ? error.message : "A.R.I.A. could not respond."
        }
      ]);
    } finally {
      setThinking(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    submitMessage(draft);
  }

  return (
    <section className="chat-room">
      <div className="chat-topline">
        <span>{data.profile.title}</span>
        <span>{data.profile.source}</span>
      </div>
      <div className="suggestions">
        {data.chatSuggestions.map((suggestion) => (
          <button key={suggestion} onClick={() => submitMessage(suggestion)}>
            {suggestion}
          </button>
        ))}
      </div>
      <div className="messages">
        {messages.map((message, index) => (
          <article className={`message ${message.role}`} key={`${message.role}-${index}`}>
            <div className="avatar">{message.role === "assistant" ? "A" : "R"}</div>
            <p>{message.content}</p>
          </article>
        ))}
        {thinking ? (
          <article className="message assistant">
            <div className="avatar">A</div>
            <p>Reading the latest channel context...</p>
          </article>
        ) : null}
      </div>
      <form className="composer" onSubmit={onSubmit}>
        <input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Ask A.R.I.A. about your analytics..." />
        <button type="submit" disabled={thinking}>
          Ask
        </button>
      </form>
    </section>
  );
}

function AnalyticsPage({ data }: { data: BootstrapPayload }) {
  return (
    <section className="page-stack">
      <Hero data={data} />
      <div className="grid stats-grid">
        {data.stats.map((stat) => (
          <div className="metric-card" key={stat.label}>
            <span>{stat.label}</span>
            <strong>{stat.value}</strong>
            <small>{stat.meta}</small>
          </div>
        ))}
      </div>
      <div className="grid two-col">
        <Panel title="Today Brief">
          <InfoRow label="Focus" value={data.today.focus_title} />
          <InfoRow label="Risk" value={data.today.risk_title} />
          <InfoRow label="Opportunity" value={data.today.opportunity_title} />
          <InfoRow label="Move" value={data.today.today_action} />
        </Panel>
        <Panel title="Recent Analytics">
          <DataTable rows={data.analyticsRows.slice(-7)} columns={["date", "views", "ctr", "retention"]} />
        </Panel>
      </div>
    </section>
  );
}

function UploadLabPage({ data }: { data: BootstrapPayload }) {
  const best = data.uploadTakeaways.best;
  const weak = data.uploadTakeaways.weak;
  return (
    <section className="page-stack">
      <SectionHeader title="Upload Lab" copy="Inspect release history, repeat what works, and find weak packaging before the next upload." />
      <div className="grid two-col">
        <Panel title="Best Upload">{best ? <RecordSummary record={best} /> : <p>No upload data loaded.</p>}</Panel>
        <Panel title="Weakest Upload">{weak ? <RecordSummary record={weak} /> : <p>No upload data loaded.</p>}</Panel>
      </div>
      <Panel title="Upload History">
        <DataTable rows={data.videoRows} columns={["title", "views", "retention", "engagement_score"]} />
      </Panel>
    </section>
  );
}

function PatternPage({ data }: { data: BootstrapPayload }) {
  return (
    <section className="page-stack">
      <SectionHeader title="Pattern Memory" copy="The remembered signals A.R.I.A. uses to avoid giving generic advice." />
      <Panel title="Latest Snapshot">
        <pre>{JSON.stringify(data.patternMemory ?? {}, null, 2)}</pre>
      </Panel>
    </section>
  );
}

function RepertoirePage({ data }: { data: BootstrapPayload }) {
  const [payload, setPayload] = useState<RepertoirePayload | null>(null);
  const [rows, setRows] = useState<Record<string, unknown>[]>(data.calendarRows);
  const [status, setStatus] = useState("");
  const [coachOutput, setCoachOutput] = useState("");
  const stages = payload?.stages ?? ["Song Idea", "Instrumental Prep", "BandLab Recording", "Video Editing", "Upload"];
  const priorities = payload?.priorities ?? ["Low", "Medium", "High"];

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
        <div className="metric-card"><span>Stages</span><strong>{stages.length}</strong><small>workflow lanes</small></div>
      </div>
      <Panel title="Idea Board">
        <div className="board-grid">
          {stages.map((stage) => (
            <div className="lane" key={stage}>
              <h3>{stage}</h3>
              {rows.filter((row) => row.stage === stage).slice(0, 5).map((row, index) => (
                <button className="song-chip" key={`${stage}-${index}`} onClick={() => coachRow(row)}>
                  <strong>{String(row.title || "Untitled")}</strong>
                  <span>{String(row.priority || "Medium")} priority</span>
                </button>
              ))}
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
            </div>
          ))}
        </div>
        <div className="button-row">
          <button onClick={addRow}>Add Song</button>
          <button className="primary" onClick={saveRows}>Save Repertoire</button>
        </div>
      </Panel>
      <Panel title="A.R.I.A. Notes">
        <pre>{coachOutput || "Select a song card to ask A.R.I.A. for focused feedback."}</pre>
      </Panel>
    </section>
  );
}

function CreatorActionsPage() {
  const [payload, setPayload] = useState<CreatorActionsPayload | null>(null);
  const [mode, setMode] = useState<"metadata" | "comments">("metadata");
  const [selectedVideoId, setSelectedVideoId] = useState("");
  const [selectedVideoLabel, setSelectedVideoLabel] = useState("");
  const [status, setStatus] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");
  const [metadataDraft, setMetadataDraft] = useState("");
  const [comments, setComments] = useState<CommentRow[]>([]);
  const [selectedCommentIndex, setSelectedCommentIndex] = useState(0);
  const [replyDraft, setReplyDraft] = useState("");
  const [reviewed, setReviewed] = useState(false);

  useEffect(() => {
    loadCreatorActions()
      .then((result) => {
        setPayload(result);
        const first = result.videos[0];
        if (first) {
          setSelectedVideoId(first.video_id);
          setSelectedVideoLabel(first.label);
        }
      })
      .catch((error: Error) => setStatus(error.message));
  }, []);

  function onVideoChange(videoId: string) {
    const selected = payload?.videos.find((video) => video.video_id === videoId);
    setSelectedVideoId(videoId);
    setSelectedVideoLabel(selected?.label ?? "");
  }

  async function handleLoadMetadata() {
    if (!selectedVideoId) return;
    setStatus("Loading metadata...");
    const result = await loadMetadata(selectedVideoId);
    setStatus(result.message);
    if (result.metadata) {
      setTitle(String(result.metadata.title ?? ""));
      setDescription(String(result.metadata.description ?? ""));
      setTags(Array.isArray(result.metadata.tags) ? result.metadata.tags.join(", ") : "");
    }
  }

  async function handleDraftMetadata() {
    setMetadataDraft("A.R.I.A. is drafting metadata...");
    const result = await draftMetadata(selectedVideoLabel);
    setMetadataDraft(result.content);
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

  async function handleLoadComments() {
    setStatus("Loading comments...");
    const result = await loadComments(selectedVideoId);
    setComments(result.rows);
    setSelectedCommentIndex(0);
    setStatus(result.message);
  }

  async function handleDraftComment() {
    const selected = comments[selectedCommentIndex];
    if (!selected) return;
    setReplyDraft("A.R.I.A. is drafting a reply...");
    const result = await draftComment(String(selected.author ?? "Unknown"), String(selected.text ?? ""));
    setReplyDraft(result.content);
  }

  async function handlePublishComment() {
    const selected = comments[selectedCommentIndex];
    if (!selected?.comment_id) return;
    setStatus("Posting reply...");
    const result = await publishComment({ comment_id: selected.comment_id, reply_text: replyDraft, reviewed });
    setStatus(result.message);
  }

  const selectedComment = comments[selectedCommentIndex];

  return (
    <section className="page-stack">
      <SectionHeader title="Creator Actions" copy="Draft, review, and publish YouTube metadata or comment replies with channel-safe guardrails." />
      {status ? <div className="status">{status}</div> : null}
      <Panel title="Safety Guardrails">
        <div className="guardrail-grid">
          {(payload?.guardrails ?? []).map(([label, value]) => <InfoRow key={label} label={label} value={value} />)}
        </div>
      </Panel>
      <div className="segmented">
        <button className={mode === "metadata" ? "active" : ""} onClick={() => setMode("metadata")}>Metadata</button>
        <button className={mode === "comments" ? "active" : ""} onClick={() => setMode("comments")}>Comments</button>
      </div>
      <Panel title={mode === "metadata" ? "Metadata Actions" : "Comment Reply Inbox"}>
        <label className="field">
          <span>Video</span>
          <select value={selectedVideoId} onChange={(event) => onVideoChange(event.target.value)}>
            {(payload?.videos ?? []).map((video) => <option value={video.video_id} key={video.video_id}>{video.label}</option>)}
          </select>
        </label>
        {mode === "metadata" ? (
          <div className="form-grid">
            <div className="button-row">
              <button onClick={handleLoadMetadata}>Load Current Metadata</button>
              <button onClick={handleDraftMetadata}>Draft Tags + Description</button>
            </div>
            <label className="field"><span>Title</span><input value={title} onChange={(event) => setTitle(event.target.value)} maxLength={100} /></label>
            <label className="field"><span>Description</span><textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={8} /></label>
            <label className="field"><span>Tags</span><textarea value={tags} onChange={(event) => setTags(event.target.value)} rows={4} /></label>
            <label className="check-row"><input type="checkbox" checked={reviewed} onChange={(event) => setReviewed(event.target.checked)} /> I reviewed this metadata and want to publish it.</label>
            <button className="primary" disabled={!reviewed || !selectedVideoId} onClick={handlePublishMetadata}>Publish Metadata Update</button>
            <pre>{metadataDraft || "A.R.I.A. metadata draft will appear here."}</pre>
          </div>
        ) : (
          <div className="form-grid">
            <div className="button-row">
              <button onClick={handleLoadComments}>Load Recent Comments</button>
              <button onClick={handleDraftComment} disabled={!selectedComment}>Draft Safe Reply</button>
            </div>
            <label className="field">
              <span>Comment</span>
              <select value={selectedCommentIndex} onChange={(event) => setSelectedCommentIndex(Number(event.target.value))}>
                {comments.map((comment, index) => <option value={index} key={String(comment.comment_id ?? index)}>{index + 1}. {comment.author ?? "Unknown"} | {comment.already_replied ? "replied" : "open"} | {String(comment.text ?? "").slice(0, 80)}</option>)}
              </select>
            </label>
            <textarea value={String(selectedComment?.text ?? "")} readOnly rows={5} />
            <label className="field"><span>Reviewed Reply</span><textarea value={replyDraft} onChange={(event) => setReplyDraft(event.target.value)} rows={4} /></label>
            <label className="check-row"><input type="checkbox" checked={reviewed} onChange={(event) => setReviewed(event.target.checked)} /> I reviewed this reply and want to post it.</label>
            <button className="primary" disabled={!reviewed || !selectedComment?.can_reply || !!selectedComment?.already_replied} onClick={handlePublishComment}>Post One Reply</button>
          </div>
        )}
      </Panel>
    </section>
  );
}

function VaultPage() {
  const [payload, setPayload] = useState<VaultPayload | null>(null);
  const [settings, setSettings] = useState<VaultPayload["settings"] | null>(null);
  const [status, setStatus] = useState("");

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
      const result = await saveVault(settings);
      setPayload(result);
      setSettings(result.settings);
      setStatus("Vault settings saved.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Vault save failed.");
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
      <Panel title="Settings">
        {settings ? (
          <div className="form-grid">
            <label className="field"><span>Ollama Model</span><input value={settings.ollama_model} onChange={(event) => updateSetting("ollama_model", event.target.value)} /></label>
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

function WorkspacePage({ title, mode }: { title: string; data: BootstrapPayload; mode: string }) {
  return (
    <section className="page-stack">
      <SectionHeader title={title} copy="This workspace is ready for the next migration pass from Streamlit into React." />
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
                <td key={column}>{String(row[column] ?? "")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
