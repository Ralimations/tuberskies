from __future__ import annotations


APP_CSS = """
<style>
:root {
    --bg: #f7f7f4;
    --surface: #ffffff;
    --surface-soft: #f1f2ef;
    --ink: #141516;
    --muted: #6b706f;
    --faint: #9ba09f;
    --line: #dedfda;
    --line-soft: #ecece7;
    --accent: #176b87;
    --warn: #b54d2f;
    --good: #357a48;
    --mono: "Cascadia Mono", "SFMono-Regular", Consolas, monospace;
    --sans: "Inter", "Segoe UI", Arial, sans-serif;
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
    max-width: 1380px;
    padding: 0 28px 40px 28px;
}

h1, h2, h3, p, label, .stMarkdown, .stCaption {
    color: var(--ink);
    letter-spacing: 0;
}

.appbar-shell {
    min-height: 64px;
    margin: 0 -28px 0 -28px;
    padding: 0 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    border-bottom: 1px solid var(--line);
    background: rgba(247, 247, 244, 0.92);
    backdrop-filter: blur(14px);
    position: sticky;
    top: 0;
    z-index: 80;
}

.appbar-left {
    display: flex;
    align-items: center;
    gap: 12px;
}

.appbar-mark {
    width: 34px;
    height: 34px;
    display: grid;
    place-items: center;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: var(--surface);
    color: var(--ink);
    font-family: var(--mono);
    font-size: 0.86rem;
    font-weight: 700;
}

.appbar-title {
    color: var(--ink);
    font-size: 1rem;
    font-weight: 720;
    line-height: 1.2;
}

.appbar-copy {
    color: var(--muted);
    font-size: 0.78rem;
    line-height: 1.35;
}

.appbar-nav-anchor {
    color: var(--muted);
    font-size: 0.78rem;
    font-weight: 640;
    text-transform: uppercase;
}

.header-nav-shell {
    margin-bottom: 0.25rem;
}

.header-nav-title {
    color: var(--ink);
    font-size: 1.75rem;
    font-weight: 720;
    line-height: 1.1;
}

.header-nav-copy {
    color: var(--muted);
    font-size: 0.92rem;
    margin-top: 4px;
}

[data-testid="stSegmentedControl"]:has([aria-label="Studio Areas"]) {
    position: sticky;
    top: 64px;
    z-index: 79;
    margin: 0 -28px 24px -28px;
    padding: 0 28px;
    background: rgba(247, 247, 244, 0.92);
    backdrop-filter: blur(14px);
}

[data-testid="stSegmentedControl"]:has([aria-label="Studio Areas"]) [role="radiogroup"] {
    gap: 0;
    border-bottom: 1px solid var(--line);
}

[data-testid="stSegmentedControl"]:has([aria-label="Studio Areas"]) label {
    min-height: 42px;
    border: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
    color: var(--muted) !important;
    font-weight: 620 !important;
}

.jumpbar-shell {
    display: none;
}

.creator-hero {
    display: grid;
    grid-template-columns: minmax(0, 1.35fr) minmax(330px, 0.75fr);
    gap: 18px;
    margin-bottom: 28px;
    align-items: stretch;
}

.creator-hero-main,
.creator-hero-stats,
.stat-card,
.insight-card,
.leaderboard-card,
.editorial-list,
.snapshot-card,
.board-lane,
[data-testid="stMetric"],
[data-testid="stDataFrame"],
[data-testid="stPlotlyChart"],
[data-testid="stChatMessage"],
[data-testid="stFileUploader"] {
    border: 1px solid var(--line);
    background: var(--surface);
    box-shadow: none;
}

.creator-hero-main {
    padding: 28px;
    min-height: 230px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.creator-eyebrow,
.section-chip,
.stat-label,
.insight-title {
    color: var(--muted);
    font-size: 0.72rem;
    font-weight: 680;
    text-transform: uppercase;
    letter-spacing: 0;
}

.creator-hero-main h1 {
    margin: 8px 0 12px 0;
    color: var(--ink);
    font-size: clamp(2.5rem, 5vw, 6rem);
    font-weight: 720;
    line-height: 0.94;
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

.creator-hero-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 18px;
}

.creator-hero-meta span,
.masthead-pill,
.snapshot-tag {
    padding: 5px 9px;
    border: 1px solid var(--line);
    background: var(--surface-soft);
    color: var(--muted);
    font-size: 0.76rem;
    font-weight: 600;
}

.creator-hero-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    overflow: hidden;
}

.creator-hero-stat {
    min-height: 115px;
    padding: 18px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    border-right: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
}

.creator-hero-stat:nth-child(2n) {
    border-right: 0;
}

.creator-hero-stat:nth-last-child(-n+2) {
    border-bottom: 0;
}

.creator-hero-stat span {
    color: var(--muted);
    font-size: 0.72rem;
    font-weight: 680;
}

.creator-hero-stat strong,
.stat-value,
.insight-value,
.leaderboard-value,
.editorial-item span:last-child {
    color: var(--ink);
    font-family: var(--mono);
    font-weight: 680;
    line-height: 1.05;
    font-variant-numeric: tabular-nums;
}

.creator-hero-stat strong {
    font-size: 1.65rem;
}

.creator-hero-stat small,
.stat-meta {
    color: var(--faint);
    font-size: 0.76rem;
}

.action-strip {
    margin-bottom: 22px;
    padding: 14px 0;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 18px;
    border-top: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
    background: transparent;
}

.action-strip-title,
.panel-title,
.leaderboard-title,
.board-lane-title,
.song-card-title,
.snapshot-title {
    color: var(--ink);
    font-size: 0.98rem;
    font-weight: 700;
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
    font-weight: 720;
    line-height: 1.08;
}

.section-copy {
    max-width: 74ch;
    margin-bottom: 22px;
}

.panel-shell {
    margin-bottom: 12px;
}

.stat-card,
.insight-card,
.leaderboard-card,
.snapshot-card,
.board-lane {
    padding: 18px;
}

.stat-card {
    min-height: 112px;
}

.stat-value {
    margin: 10px 0 7px 0;
    font-size: 2rem;
}

.insight-card {
    min-height: 102px;
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
    background: var(--surface-soft);
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
    border-radius: 4px;
    background: var(--surface);
    color: var(--ink);
    font-weight: 640;
    box-shadow: none;
}

.stButton > button:hover {
    border-color: var(--accent);
    color: var(--accent);
}

.stButton > button[kind="primary"] {
    border-color: var(--accent);
    background: var(--accent);
    color: white;
}

.stTextInput input,
.stTextArea textarea,
.stDateInput input,
.stSelectbox div[data-baseweb="select"] > div {
    border: 1px solid var(--line);
    border-radius: 4px;
    background: var(--surface);
    color: var(--ink);
}

[data-testid="stRadio"] > div {
    padding: 8px;
    border: 1px solid var(--line);
    background: var(--surface);
}

[data-testid="stDataFrame"],
[data-testid="stPlotlyChart"],
[data-testid="stChatMessage"] {
    padding: 4px;
}

[data-testid="stAlert"],
[data-testid="stExpander"],
[data-testid="stFileUploader"] {
    border-radius: 4px;
}

[data-testid="stHorizontalBlock"] {
    gap: 18px;
}

.subnav-wrap [data-testid="stSegmentedControl"] {
    position: sticky;
    top: 107px;
    z-index: 78;
    margin: 0 -28px 18px -28px;
    padding: 8px 28px 0 28px;
    background: rgba(247, 247, 244, 0.94);
    backdrop-filter: blur(14px);
    border-bottom: 1px solid var(--line);
}

.subnav-wrap [data-testid="stSegmentedControl"] [role="radiogroup"] {
    border-bottom: 0;
}

.compact-note {
    color: var(--muted);
    font-size: 0.82rem;
    margin: -4px 0 10px 0;
}

@media (max-width: 900px) {
    .block-container {
        padding-left: 16px;
        padding-right: 16px;
    }

    .appbar-shell {
        margin-left: -16px;
        margin-right: -16px;
        padding-left: 16px;
        padding-right: 16px;
    }

    [data-testid="stSegmentedControl"]:has([aria-label="Studio Areas"]) {
        margin-left: -16px;
        margin-right: -16px;
        padding-left: 16px;
        padding-right: 16px;
    }

    .subnav-wrap [data-testid="stSegmentedControl"] {
        margin-left: -16px;
        margin-right: -16px;
        padding-left: 16px;
        padding-right: 16px;
    }

    .creator-hero,
    .creator-hero-stats {
        grid-template-columns: 1fr;
    }

    .creator-hero-stat {
        border-right: 0;
        border-bottom: 1px solid var(--line);
    }

    .creator-hero-stat:last-child {
        border-bottom: 0;
    }

    .action-strip {
        flex-direction: column;
    }
}
</style>
"""
