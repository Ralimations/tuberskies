from __future__ import annotations


APP_CSS = """
<style>
:root {
    --bg: #090c14;
    --sidebar: #070a12;
    --surface: #151922;
    --surface-2: #1b202b;
    --surface-3: #202633;
    --ink: #f6f7fb;
    --muted: #a7afbf;
    --faint: #6f7889;
    --line: #252b37;
    --line-soft: #1d2330;
    --accent: #2d7df0;
    --accent-soft: #10264f;
    --good: #22c55e;
    --warn: #f59e0b;
    --mono: "Cascadia Mono", "SFMono-Regular", Consolas, monospace;
    --sans: "Inter", "Segoe UI", Arial, sans-serif;
}

html,
body,
#root,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.stApp {
    background: var(--bg) !important;
}

.stApp {
    background: var(--bg);
    color: var(--ink);
    font-family: var(--sans);
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stSidebar"] {
    display: none;
}

[data-testid="stAppViewContainer"] > .main {
    padding-top: 0;
}

.block-container {
    max-width: 980px;
    padding: 70px 28px 48px 28px;
    margin-left: calc(236px + ((100vw - 236px - 980px) / 2));
    margin-right: auto;
}

h1, h2, h3, p, label, .stMarkdown, .stCaption {
    color: var(--ink);
    letter-spacing: 0;
}

a {
    color: inherit;
}

.app-sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    width: 236px;
    padding: 18px 14px;
    z-index: 90;
    border-right: 1px solid var(--line);
    background: var(--sidebar);
    display: flex;
    flex-direction: column;
    gap: 18px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: var(--surface-3) transparent;
}

.sidebar-brand {
    min-height: 36px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.sidebar-brand-text {
    color: var(--faint);
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0;
}

.appbar-mark {
    width: 22px;
    height: 22px;
    display: grid;
    place-items: center;
    border-radius: 6px;
    background: var(--accent);
    color: white;
    font-family: var(--mono);
    font-size: 0.72rem;
    font-weight: 800;
}

.new-chat-link {
    display: flex;
    align-items: center;
    min-height: 34px;
    padding: 0 10px;
    color: var(--ink) !important;
    font-size: 0.86rem;
    font-weight: 700;
    text-decoration: none !important;
}

.new-chat-link:hover {
    color: var(--accent) !important;
}

.header-menu-shell {
    display: grid;
    gap: 18px;
}

.header-menu-group {
    display: grid;
    gap: 8px;
}

.header-menu-label {
    padding: 0 6px;
    color: var(--faint);
    font-size: 0.78rem;
    font-weight: 600;
    line-height: 1.2;
}

.header-menu-links {
    display: grid;
    gap: 7px;
}

.header-menu-link {
    min-height: 30px;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 8px;
    border-radius: 6px;
    color: var(--ink) !important;
    font-size: 0.86rem;
    font-weight: 700;
    text-decoration: none !important;
}

.sidebar-icon {
    width: 17px;
    height: 17px;
    flex: 0 0 auto;
    fill: none;
    stroke: currentColor;
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
}

.header-menu-link:hover,
.header-menu-link.active {
    background: var(--surface-2);
    color: white !important;
}

.header-menu-link.active {
    box-shadow: inset 3px 0 0 var(--accent);
}

.sidebar-upgrade {
    margin-top: auto;
    padding: 12px 10px;
    border-radius: 999px;
    background: var(--surface-2);
    color: var(--muted);
    font-size: 0.78rem;
    font-weight: 700;
    text-align: center;
}

.jumpbar-shell {
    display: none;
}

.creator-hero {
    display: grid;
    grid-template-columns: 1fr;
    gap: 22px;
    margin: 0 0 28px 0;
}

.creator-hero-main {
    text-align: center;
}

.creator-hero-main,
.creator-hero-stats,
.stat-card,
.insight-card,
.leaderboard-card,
.editorial-list,
.snapshot-card,
.board-lane,
.panel-shell,
[data-testid="stMetric"],
[data-testid="stDataFrame"],
[data-testid="stPlotlyChart"],
[data-testid="stChatMessage"],
[data-testid="stFileUploader"],
[data-testid="stAlert"],
[data-testid="stExpander"] {
    border: 1px solid var(--line-soft);
    border-radius: 16px;
    background: var(--surface);
    box-shadow: none;
}

[data-testid="stChatMessage"] {
    border-radius: 14px;
    margin-bottom: 10px;
}

[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"],
[data-testid="stBottom"] > div,
[data-testid="stBottom"] section,
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div {
    background: var(--bg) !important;
}

[data-testid="stBottom"] {
    left: 236px !important;
    border-top: 1px solid var(--line-soft);
}

[data-testid="stBottomBlockContainer"] {
    padding: 0 !important;
}

[data-testid="stChatInput"] {
    max-width: 980px;
    margin: 0 auto;
    padding: 12px 28px 16px 28px;
}

[data-testid="stChatInput"] textarea {
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    background: var(--surface) !important;
    color: var(--ink) !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: var(--faint) !important;
}

.creator-hero-main {
    padding: 18px 18px 0 18px;
    border: 0;
    background: transparent;
}

.creator-eyebrow,
.section-chip,
.stat-label,
.insight-title {
    color: var(--muted);
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0;
}

.creator-hero-main h1 {
    margin: 6px 0 10px 0;
    color: var(--ink);
    font-size: clamp(2.4rem, 5vw, 4.6rem);
    font-weight: 800;
    line-height: 0.96;
    letter-spacing: 0;
}

.creator-hero-main p,
.section-copy,
.panel-copy,
.action-strip-copy,
.insight-copy,
.song-card-meta,
.snapshot-notes {
    color: var(--muted);
    font-size: 0.92rem;
    line-height: 1.5;
}

.creator-hero-main p {
    max-width: 760px;
    margin-left: auto;
    margin-right: auto;
}

.creator-hero-meta {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
    margin-top: 18px;
}

.creator-hero-meta span,
.masthead-pill,
.snapshot-tag {
    padding: 6px 11px;
    border: 1px solid var(--line);
    border-radius: 999px;
    background: var(--surface-2);
    color: var(--muted);
    font-size: 0.76rem;
    font-weight: 700;
}

.creator-hero-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    border: 0;
    background: transparent;
}

.creator-hero-stat {
    min-height: 138px;
    padding: 18px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    border: 1px solid var(--line-soft);
    border-radius: 12px;
    background: var(--surface);
    text-align: center;
}

.creator-hero-stat::after,
.stat-card::after {
    content: "";
    height: 8px;
    margin-top: 12px;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--accent) 0 56%, var(--surface-3) 56% 100%);
}

.creator-hero-stat span {
    color: var(--muted);
    font-size: 0.72rem;
    font-weight: 800;
}

.creator-hero-stat strong,
.stat-value,
.insight-value,
.leaderboard-value,
.editorial-item span:last-child {
    color: var(--ink);
    font-family: var(--mono);
    font-weight: 800;
    line-height: 1.05;
    font-variant-numeric: tabular-nums;
}

.creator-hero-stat strong {
    margin-top: 8px;
    font-size: 2.2rem;
}

.creator-hero-stat small,
.stat-meta {
    color: var(--faint);
    font-size: 0.76rem;
}

.action-strip {
    margin-bottom: 22px;
    padding: 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    border: 1px solid #1f4a88;
    border-radius: 8px;
    background: var(--accent-soft);
}

.feed-alert {
    min-height: 56px;
    margin: 2px 0 22px 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    border: 1px solid #1f4a88;
    border-radius: 8px;
    background: var(--accent-soft);
    color: var(--ink);
    font-size: 0.92rem;
}

.feed-alert span {
    width: 10px;
    height: 10px;
    border-radius: 999px;
    background: var(--accent);
}

.feed-alert strong {
    font-weight: 800;
}

.feed-card {
    margin-bottom: 18px;
    padding: 20px;
    border: 1px solid var(--line-soft);
    border-radius: 16px;
    background: var(--surface);
}

.feed-card-top {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 16px;
    align-items: start;
    margin-bottom: 16px;
}

.feed-card h3 {
    margin: 0 0 8px 0;
    color: var(--ink);
    font-size: 1rem;
    font-weight: 800;
    line-height: 1.3;
}

.feed-card p {
    margin: 0;
    color: var(--muted);
    font-size: 0.88rem;
    line-height: 1.45;
}

.feed-age {
    color: var(--faint);
    font-size: 0.78rem;
    font-weight: 700;
    white-space: nowrap;
}

.feed-card-body {
    display: grid;
    grid-template-columns: 150px minmax(0, 1fr);
    gap: 18px;
    align-items: center;
}

.feed-thumb {
    width: 150px;
    aspect-ratio: 16 / 9;
    border-radius: 12px;
    object-fit: cover;
    background: var(--surface-3);
}

.feed-thumb-empty {
    position: relative;
    display: block;
}

.feed-thumb-empty::after {
    content: "A.R.I.A.";
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    color: var(--faint);
    font-size: 0.76rem;
    font-weight: 800;
}

.feed-card-meta {
    min-width: 0;
    display: grid;
    gap: 16px;
}

.feed-card-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.feed-card-tags span {
    min-height: 30px;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 0 10px;
    border-radius: 8px;
    background: var(--surface-2);
    color: var(--ink);
    font-size: 0.78rem;
    font-weight: 700;
}

.feed-card-tags b {
    color: var(--good);
    font-weight: 800;
}

.feed-card-button {
    min-height: 38px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: min(100%, 320px);
    padding: 0 18px;
    border-radius: 999px;
    background: var(--accent);
    color: white !important;
    font-size: 0.86rem;
    font-weight: 800;
    text-decoration: none !important;
}

.feed-card-button:hover {
    filter: brightness(1.08);
}

.action-strip-title,
.panel-title,
.leaderboard-title,
.board-lane-title,
.song-card-title,
.snapshot-title {
    color: var(--ink);
    font-size: 0.98rem;
    font-weight: 800;
}

.action-strip-pills {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 8px;
}

.section-chip {
    display: inline-block;
    margin-bottom: 6px;
    color: var(--accent);
}

.section-title {
    margin: 0 0 5px 0;
    color: var(--ink);
    font-size: clamp(1.55rem, 2.2vw, 2.25rem);
    font-weight: 800;
    line-height: 1.08;
}

.section-copy {
    max-width: 74ch;
    margin-bottom: 22px;
}

.panel-shell {
    margin-bottom: 12px;
    padding: 18px;
}

.stat-card,
.insight-card,
.leaderboard-card,
.snapshot-card,
.board-lane {
    padding: 18px;
}

.stat-card {
    min-height: 124px;
}

.stat-value {
    margin: 10px 0 7px 0;
    font-size: 2rem;
}

.insight-card {
    min-height: 112px;
    margin-bottom: 14px;
}

.insight-value {
    margin: 8px 0 6px 0;
    font-size: 1.18rem;
}

.leaderboard-card,
.editorial-list {
    margin-bottom: 16px;
}

.leaderboard-row,
.editorial-item {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 14px;
    align-items: center;
    padding: 11px 0;
    border-top: 1px solid var(--line-soft);
}

.leaderboard-row:first-of-type,
.editorial-item:first-child {
    border-top: 0;
}

.leaderboard-label,
.editorial-item span:first-child {
    min-width: 0;
    color: var(--muted);
    font-size: 0.88rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.editorial-list {
    padding: 6px 16px;
}

.board-lane {
    min-height: 170px;
}

.song-card {
    margin-top: 10px;
    padding: 12px;
    border: 1px solid var(--line-soft);
    border-radius: 10px;
    background: var(--surface-2);
}

.snapshot-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 12px 0;
}

.stButton > button {
    min-height: 38px;
    border: 1px solid var(--line);
    border-radius: 999px;
    background: var(--surface-2);
    color: var(--ink);
    font-weight: 800;
    box-shadow: none;
}

.stButton > button:hover {
    border-color: var(--accent);
    color: white;
}

.stButton > button[kind="primary"] {
    border-color: var(--accent);
    background: var(--accent);
    color: white;
}

[data-testid="stSegmentedControl"] {
    position: static;
    margin: 0 0 18px 0;
    padding: 8px 0;
    background: transparent;
}

[data-testid="stSegmentedControl"] [role="radiogroup"] {
    gap: 10px;
    border-bottom: 0;
}

[data-testid="stSegmentedControl"] button {
    border-radius: 999px !important;
    background: var(--surface-2) !important;
    color: var(--ink) !important;
    font-weight: 800 !important;
}

[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
    background: var(--accent) !important;
    color: white !important;
}

.stTextInput input,
.stTextArea textarea,
.stDateInput input,
.stSelectbox div[data-baseweb="select"] > div,
[data-baseweb="textarea"] textarea {
    border: 1px solid var(--line);
    border-radius: 10px;
    background: var(--surface);
    color: var(--ink);
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: var(--accent);
}

[data-testid="stRadio"] > div {
    padding: 8px;
    border: 1px solid var(--line);
    border-radius: 12px;
    background: var(--surface);
}

[data-testid="stDataFrame"],
[data-testid="stPlotlyChart"],
[data-testid="stChatMessage"],
[data-testid="stFileUploader"],
[data-testid="stExpander"] {
    padding: 4px;
}

[data-testid="stAlert"] {
    color: var(--ink);
}

[data-testid="stHorizontalBlock"] {
    gap: 14px;
}

.compact-note {
    color: var(--muted);
    font-size: 0.82rem;
    margin: -4px 0 10px 0;
}

@media (max-width: 980px) {
    .app-sidebar {
        position: sticky;
        width: auto;
        height: auto;
        inset: auto;
        padding: 10px 12px;
        border-right: 0;
        border-bottom: 1px solid var(--line);
    }

    .header-menu-shell {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .block-container {
        max-width: none;
        margin-left: 0;
        padding: 20px 16px 40px 16px;
    }

    [data-testid="stBottom"] {
        left: 0 !important;
    }

    [data-testid="stChatInput"] {
        max-width: none;
        padding-left: 16px;
        padding-right: 16px;
    }

    .creator-hero-stats {
        grid-template-columns: 1fr;
    }

    .action-strip {
        flex-direction: column;
        align-items: flex-start;
    }

    .feed-card-body {
        grid-template-columns: 1fr;
    }

    .feed-thumb {
        width: 100%;
    }
}
</style>
"""
