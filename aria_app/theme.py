from __future__ import annotations


APP_CSS = """
<style>
:root {
    --page: #f4f1ea;
    --paper: #fffdf8;
    --paper-2: #f7f8fb;
    --ink: #16181d;
    --muted: #647084;
    --line: rgba(22, 24, 29, 0.12);
    --line-strong: rgba(22, 24, 29, 0.18);
    --rail: #151922;
    --rail-soft: #202635;
    --accent: #ff5f57;
    --accent-2: #1282a2;
    --accent-3: #7ea16b;
    --gold: #c58b2b;
    --shadow: 0 18px 48px rgba(21, 25, 34, 0.12);
    --radius-lg: 14px;
    --radius-md: 10px;
}

.stApp {
    background: var(--page);
    color: var(--ink);
    font-family: "Segoe UI", Arial, sans-serif;
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] {
    display: none;
}

[data-testid="stAppViewContainer"] > .main {
    padding-top: 0;
}

.block-container {
    max-width: 1500px;
    padding: 0.8rem 1.25rem 2rem 1.25rem;
}

h1, h2, h3, p, label, .stCaption, .stMarkdown {
    color: var(--ink);
    letter-spacing: 0;
}

.stCaption, .caption, small {
    color: var(--muted);
}

.appbar-shell {
    min-height: 92px;
    margin-bottom: 0.9rem;
    padding: 0.9rem 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    border: 1px solid var(--line);
    border-radius: 18px;
    background: var(--paper);
    box-shadow: var(--shadow);
}

.appbar-left {
    display: flex;
    align-items: center;
    gap: 0.85rem;
}

.appbar-mark {
    width: 52px;
    height: 52px;
    border-radius: 12px;
    display: grid;
    place-items: center;
    background: var(--rail);
    color: #fffdf8;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0;
}

.appbar-title {
    color: var(--ink);
    font-size: 1.15rem;
    font-weight: 800;
    margin-bottom: 0.12rem;
}

.appbar-copy {
    color: var(--muted);
    font-size: 0.86rem;
    line-height: 1.4;
}

.appbar-right,
.action-strip-pills,
.creator-hero-meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 0.45rem;
}

.masthead-pill {
    display: inline-flex;
    align-items: center;
    width: fit-content;
    min-height: 30px;
    padding: 0.34rem 0.58rem;
    border: 1px solid var(--line);
    border-radius: 999px;
    background: #f7f2e8;
    color: var(--ink);
    font-size: 0.74rem;
    font-weight: 700;
}

.jumpbar-shell {
    margin-bottom: 0.3rem;
    display: none;
}

.header-nav-shell {
    position: sticky;
    top: 0.35rem;
    z-index: 20;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 0.38rem;
    padding: 0.72rem 0.85rem;
    border: 1px solid var(--line);
    border-radius: 16px;
    background: rgba(255, 253, 248, 0.94);
    backdrop-filter: blur(16px);
    box-shadow: 0 12px 28px rgba(21, 25, 34, 0.08);
}

.header-nav-title {
    color: var(--ink);
    font-size: 0.92rem;
    font-weight: 900;
}

.header-nav-copy {
    color: var(--muted);
    font-size: 0.8rem;
    line-height: 1.35;
}

.header-nav-status {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 0.42rem;
}

.header-nav-status span {
    padding: 0.32rem 0.52rem;
    border: 1px solid var(--line);
    border-radius: 999px;
    background: #f7f2e8;
    color: var(--ink);
    font-size: 0.74rem;
    font-weight: 800;
}

.action-strip {
    position: sticky;
    top: 0.45rem;
    z-index: 12;
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    padding: 0.62rem 0.7rem;
    border: 1px solid var(--line);
    border-radius: 14px;
    background: rgba(255, 253, 248, 0.9);
    backdrop-filter: blur(14px);
    box-shadow: 0 12px 28px rgba(21, 25, 34, 0.08);
}

.action-strip-title,
.panel-title,
.leaderboard-title {
    color: var(--ink);
    font-size: 0.92rem;
    font-weight: 800;
}

.action-strip-copy,
.panel-copy,
.section-copy,
.insight-copy,
.song-card-meta {
    color: var(--muted);
    font-size: 0.84rem;
    line-height: 1.45;
}

.section-chip {
    display: inline-block;
    padding: 0.24rem 0.48rem;
    margin-bottom: 0.3rem;
    border: 1px solid var(--line);
    border-radius: 999px;
    background: var(--paper);
    color: var(--accent-2);
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0;
}

.section-title {
    color: var(--ink);
    font-size: clamp(1.45rem, 2.2vw, 2.2rem);
    line-height: 1.05;
    margin: 0 0 0.18rem 0;
    letter-spacing: 0;
}

.section-copy {
    max-width: 72ch;
    margin-bottom: 0.75rem;
}

.panel-shell {
    margin: 0 0 0.65rem 0;
    padding: 0;
    border: none;
    background: transparent;
}

.creator-hero {
    display: grid;
    grid-template-columns: minmax(0, 1.3fr) minmax(330px, 0.75fr);
    gap: 1rem;
    align-items: stretch;
    margin-bottom: 0.95rem;
    padding: 1.35rem;
    border: 1px solid var(--line);
    border-radius: 20px;
    background: #151922;
    box-shadow: var(--shadow);
}

.creator-hero-main h1 {
    margin: 0.2rem 0 0.55rem 0;
    color: #fffdf8;
    font-size: clamp(2.4rem, 5vw, 5.6rem);
    line-height: 0.92;
    letter-spacing: 0;
}

.creator-eyebrow {
    color: #f7d98b;
    font-size: 0.72rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0;
}

.creator-hero-main p {
    max-width: 68ch;
    margin: 0;
    color: #dfe5ee;
    font-size: 1rem;
    line-height: 1.52;
}

.creator-hero-meta {
    justify-content: flex-start;
    margin-top: 0.95rem;
}

.creator-hero-meta span {
    padding: 0.36rem 0.58rem;
    border: 1px solid rgba(255, 253, 248, 0.18);
    border-radius: 999px;
    background: rgba(255, 253, 248, 0.08);
    color: #fffdf8;
    font-size: 0.76rem;
}

.creator-hero-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.65rem;
}

.creator-hero-stat {
    min-height: 112px;
    padding: 0.82rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    border: 1px solid rgba(255, 253, 248, 0.16);
    border-radius: 14px;
    background: rgba(255, 253, 248, 0.08);
}

.creator-hero-stat span {
    color: #c9d2df;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0;
}

.creator-hero-stat strong {
    color: #fffdf8;
    font-size: 1.52rem;
    line-height: 1.05;
}

.creator-hero-stat small {
    color: #f7d98b;
    font-size: 0.76rem;
    line-height: 1.25;
}

.board-lane,
.snapshot-card,
.stat-card,
.insight-card,
.leaderboard-card,
[data-testid="stMetric"],
[data-testid="stDataFrame"],
[data-testid="stPlotlyChart"],
[data-testid="stChatMessage"],
[data-testid="stFileUploader"] {
    border: 1px solid var(--line);
    background: var(--paper);
    box-shadow: 0 10px 28px rgba(21, 25, 34, 0.07);
}

.stat-card,
.insight-card,
.leaderboard-card,
.snapshot-card {
    border-radius: var(--radius-lg);
}

.stat-card {
    min-height: 112px;
    padding: 0.9rem;
    border-left: 5px solid var(--accent-2);
}

.stat-label,
.insight-title {
    margin-bottom: 0.44rem;
    color: var(--muted);
    font-size: 0.72rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0;
}

.stat-value {
    margin-bottom: 0.32rem;
    color: var(--ink);
    font-size: 1.75rem;
    font-weight: 850;
    line-height: 1;
}

.stat-meta {
    color: var(--accent-2);
    font-size: 0.8rem;
    font-weight: 800;
}

.insight-card {
    min-height: 96px;
    margin-bottom: 0.52rem;
    padding: 0.86rem;
}

.insight-value {
    margin-bottom: 0.2rem;
    color: var(--ink);
    font-size: 1.16rem;
    font-weight: 800;
}

.leaderboard-card {
    margin-bottom: 0.58rem;
    padding: 0.84rem 0.9rem;
}

.leaderboard-row,
.editorial-item {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 0.7rem;
    align-items: center;
    border-top: 1px solid rgba(22, 24, 29, 0.08);
    padding: 0.42rem 0;
}

.leaderboard-row:first-of-type {
    border-top: none;
}

.leaderboard-label,
.editorial-item span:first-child {
    min-width: 0;
    color: var(--muted);
    font-size: 0.84rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.leaderboard-value,
.editorial-item span:last-child {
    color: var(--ink);
    font-size: 0.82rem;
    font-weight: 800;
}

.editorial-list {
    margin: 0.32rem 0 0.7rem 0;
    padding: 0.56rem 0.78rem;
    border: 1px solid var(--line);
    border-radius: var(--radius-md);
    background: var(--paper);
}

.board-lane {
    min-height: 160px;
    padding: 0.74rem;
    border-radius: 14px;
}

.board-lane-title,
.song-card-title,
.snapshot-title {
    color: var(--ink);
    font-weight: 850;
}

.song-card {
    margin-bottom: 0.54rem;
    padding: 0.58rem;
    border: 1px solid var(--line);
    border-radius: 10px;
    background: var(--paper-2);
}

.snapshot-card {
    padding: 0.9rem;
}

.snapshot-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.42rem;
    margin: 0.5rem 0 0.7rem 0;
}

.snapshot-tag {
    padding: 0.28rem 0.5rem;
    border: 1px solid var(--line);
    border-radius: 999px;
    background: #f7f2e8;
    color: var(--ink);
    font-size: 0.76rem;
    font-weight: 700;
}

[data-testid="stSidebar"] {
    display: none;
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1rem;
}

.sidebar-brand {
    margin-bottom: 1rem;
}

.sidebar-kicker,
.sidebar-section {
    color: #f7d98b;
    font-size: 0.72rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0;
}

.sidebar-title {
    color: #fffdf8;
    font-size: 1.45rem;
    font-weight: 850;
    margin: 0.22rem 0;
}

.sidebar-copy {
    color: #bfc7d4;
    font-size: 0.86rem;
    line-height: 1.45;
}

.sidebar-section {
    margin: 0.9rem 0 0.45rem 0;
}

.sidebar-card,
.sidebar-status-pill {
    border: 1px solid rgba(255, 253, 248, 0.1);
    border-radius: 12px;
    background: var(--rail-soft);
}

.sidebar-card {
    margin-top: 0.5rem;
    padding: 0.74rem;
}

.sidebar-card strong,
.sidebar-status-pill strong {
    color: #fffdf8;
}

.sidebar-card p,
.sidebar-status-pill span {
    color: #bfc7d4;
}

.sidebar-status-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.42rem;
    margin-top: 0.55rem;
}

.sidebar-status-pill {
    padding: 0.5rem;
}

.sidebar-status-pill strong {
    display: block;
    font-size: 0.74rem;
}

.sidebar-status-pill span {
    font-size: 0.72rem;
}

[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    gap: 0.25rem;
    padding: 0;
    border: 0;
    background: transparent;
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] label p {
    color: #e6ebf2;
}

[data-testid="stRadio"] > div {
    padding: 0.45rem;
    border: 1px solid var(--line);
    border-radius: 12px;
    background: var(--paper);
}

.stButton > button {
    min-height: 40px;
    border: 1px solid var(--line-strong);
    border-radius: 10px;
    background: var(--paper);
    color: var(--ink);
    font-weight: 800;
    box-shadow: none;
}

.stButton > button:hover {
    border-color: var(--accent-2);
    color: var(--accent-2);
}

.stButton > button[kind="primary"] {
    border-color: var(--accent);
    background: var(--accent);
    color: #fffdf8;
}

.stTextInput input,
.stTextArea textarea,
.stDateInput input,
.stSelectbox div[data-baseweb="select"] > div {
    border: 1px solid var(--line-strong);
    border-radius: 10px;
    background: var(--paper);
    color: var(--ink);
}

[data-testid="stTabs"] [role="tablist"],
[data-testid="stSegmentedControl"] {
    border-radius: 12px;
}

.subnav-wrap [data-testid="stSegmentedControl"] {
    position: sticky;
    top: 5.5rem;
    z-index: 10;
    margin-bottom: 0.75rem;
    padding: 0.2rem 0;
    background: rgba(244, 241, 234, 0.92);
    backdrop-filter: blur(12px);
}

[data-testid="stDataFrame"],
[data-testid="stPlotlyChart"],
[data-testid="stChatMessage"] {
    border-radius: var(--radius-lg);
    padding: 0.16rem;
}

[data-testid="stAlert"],
[data-testid="stExpander"],
[data-testid="stFileUploader"] {
    border-radius: var(--radius-md);
}

[data-testid="stHorizontalBlock"] {
    gap: 0.85rem;
}

.compact-note {
    color: var(--muted);
    font-size: 0.8rem;
    margin-top: -0.2rem;
    margin-bottom: 0.42rem;
}

@media (max-width: 900px) {
    .appbar-shell,
    .action-strip,
    .creator-hero,
    .header-nav-shell {
        grid-template-columns: 1fr;
        flex-direction: column;
        align-items: flex-start;
    }

    .header-nav-status {
        justify-content: flex-start;
    }

    .creator-hero-stats {
        grid-template-columns: 1fr;
    }

    .block-container {
        padding-left: 0.85rem;
        padding-right: 0.85rem;
    }
}
</style>
"""
