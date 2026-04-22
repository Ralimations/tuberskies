from __future__ import annotations


APP_CSS = """
<style>
:root {
    --bg: #0b1020;
    --surface: #121a2b;
    --surface-soft: #182338;
    --ink: #f5f7fb;
    --muted: #aab4c8;
    --line: rgba(255, 255, 255, 0.08);
    --accent: #f2b84b;
    --accent-deep: #ffd98c;
    --sky: #5ec4ff;
    --mint: #61d394;
    --rose: #ff7a90;
    --shadow: 0 18px 42px rgba(0, 0, 0, 0.24);
    --radius-lg: 18px;
    --radius-md: 12px;
}

.stApp {
    background:
        linear-gradient(135deg, rgba(94, 196, 255, 0.1), transparent 28%),
        linear-gradient(180deg, #0b1020 0%, #101827 52%, #0c1324 100%);
    color: var(--ink);
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] {
    display: none;
}

[data-testid="stAppViewContainer"] {
    margin-top: 0;
}

[data-testid="stAppViewContainer"] > .main {
    padding-top: 0.35rem;
}

.block-container {
    padding-top: 0.35rem;
    padding-bottom: 1.2rem;
    max-width: 1440px;
    margin: 0 auto;
}

h1, h2, h3 {
    font-family: "Segoe UI", "Trebuchet MS", sans-serif !important;
    color: var(--ink);
    letter-spacing: -0.03em;
}

p, label, .stCaption, .stMarkdown {
    color: var(--muted);
}

.appbar-shell {
    background: rgba(14, 21, 35, 0.86);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 0.6rem 0.8rem;
    box-shadow: var(--shadow);
    margin-bottom: 0.45rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.8rem;
}

.appbar-left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.appbar-mark {
    width: 42px;
    height: 42px;
    border-radius: 10px;
    display: grid;
    place-items: center;
    background: linear-gradient(135deg, rgba(242, 184, 75, 0.22), rgba(94, 196, 255, 0.16));
    border: 1px solid rgba(255,255,255,0.08);
    color: var(--accent-deep);
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
}

.appbar-title {
    color: var(--ink);
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 0.08rem;
}

.appbar-copy {
    color: var(--muted);
    font-size: 0.78rem;
    line-height: 1.35;
}

.appbar-right {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 0.45rem;
}

.action-strip {
    position: sticky;
    top: 0.35rem;
    z-index: 12;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.7rem;
    padding: 0.5rem 0.7rem;
    border-radius: 16px;
    background: rgba(15, 23, 45, 0.82);
    border: 1px solid var(--line);
    backdrop-filter: blur(12px);
    box-shadow: 0 12px 26px rgba(0,0,0,0.18);
}

.jumpbar-shell {
    margin-bottom: 0.4rem;
}

.jumpbar-title {
    color: var(--ink);
    font-size: 0.8rem;
    font-weight: 700;
    margin-bottom: 0.08rem;
}

.jumpbar-copy {
    color: var(--muted);
    font-size: 0.75rem;
    line-height: 1.3;
    margin-bottom: 0.35rem;
}

.action-strip-title {
    color: var(--ink);
    font-size: 0.82rem;
    font-weight: 700;
}

.action-strip-copy {
    color: var(--muted);
    font-size: 0.76rem;
}

.action-strip-pills {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    flex-wrap: wrap;
}

.section-chip {
    display: inline-block;
    padding: 0.26rem 0.58rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--line);
    border-radius: 999px;
    font-size: 0.72rem;
    color: var(--accent-deep);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
}

.section-title {
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
    font-size: clamp(1.18rem, 1.6vw, 1.6rem);
    color: var(--ink);
    margin: 0 0 0.15rem 0;
}

.section-copy {
    color: var(--muted);
    margin-bottom: 0.45rem;
    max-width: 64ch;
    font-size: 0.86rem;
}

.panel-shell {
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 0;
    box-shadow: none;
    margin-bottom: 0.7rem;
}

.panel-title {
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
    color: var(--ink);
    font-size: 1rem;
    margin-bottom: 0.12rem;
}

.panel-copy {
    color: var(--muted);
    font-size: 0.84rem;
    margin-bottom: 0.42rem;
}

.masthead-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.34rem 0.58rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--line);
    color: var(--accent-deep);
    font-size: 0.72rem;
    width: fit-content;
}

.creator-hero {
    display: grid;
    grid-template-columns: minmax(0, 1.25fr) minmax(320px, 0.75fr);
    gap: 1rem;
    align-items: stretch;
    padding: 1.05rem;
    margin-bottom: 0.75rem;
    border-radius: 18px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background:
        linear-gradient(135deg, rgba(94, 196, 255, 0.14), transparent 38%),
        linear-gradient(145deg, #151f32 0%, #101827 58%, #10151f 100%);
    box-shadow: var(--shadow);
}

.creator-hero-main h1 {
    margin: 0.16rem 0 0.4rem 0;
    font-size: clamp(2rem, 4vw, 4.2rem);
    line-height: 0.95;
    letter-spacing: 0;
    color: var(--ink);
}

.creator-eyebrow {
    color: var(--accent-deep);
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}

.creator-hero-main p {
    max-width: 66ch;
    margin: 0;
    color: #c4ccda;
    font-size: 0.95rem;
    line-height: 1.52;
}

.creator-hero-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-top: 0.8rem;
}

.creator-hero-meta span {
    padding: 0.36rem 0.58rem;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 999px;
    color: #d9e4f5;
    background: rgba(255,255,255,0.05);
    font-size: 0.76rem;
}

.creator-hero-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.62rem;
}

.creator-hero-stat {
    min-height: 106px;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.09);
    background: rgba(7, 12, 22, 0.42);
    padding: 0.74rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.creator-hero-stat span {
    color: var(--muted);
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

.creator-hero-stat strong {
    color: var(--ink);
    font-size: 1.36rem;
    line-height: 1.05;
}

.creator-hero-stat small {
    color: var(--accent-deep);
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
    background: linear-gradient(180deg, #151f32 0%, #101827 100%);
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
}

.board-lane {
    border-radius: 18px;
    padding: 0.72rem;
    min-height: 150px;
}

.board-lane-title {
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
    color: var(--ink);
    font-size: 0.95rem;
    margin-bottom: 0.75rem;
}

.song-card {
    background: rgba(255, 255, 255, 0.045);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 0.6rem 0.65rem;
    margin-bottom: 0.55rem;
}

.song-card-title {
    color: var(--ink);
    font-weight: 600;
    margin-bottom: 0.28rem;
}

.song-card-meta {
    color: var(--muted);
    font-size: 0.82rem;
    line-height: 1.4;
}

.snapshot-card {
    border-radius: 18px;
    padding: 0.78rem;
}

.snapshot-title {
    color: var(--ink);
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
    font-size: 1.05rem;
    margin-bottom: 0.35rem;
}

.snapshot-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-bottom: 0.7rem;
}

.snapshot-tag {
    padding: 0.3rem 0.58rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid var(--line);
    color: var(--accent-deep);
    font-size: 0.78rem;
}

.snapshot-notes {
    color: var(--muted);
    font-size: 0.92rem;
    line-height: 1.7;
}

.editorial-list {
    background: rgba(255, 255, 255, 0.035);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 0.55rem 0.65rem;
    margin-bottom: 0.45rem;
}

.leaderboard-card {
    background: linear-gradient(180deg, #17203d 0%, #121a32 100%);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 0.62rem 0.72rem;
    box-shadow: var(--shadow);
    margin-bottom: 0.45rem;
}

.leaderboard-dense .leaderboard-row {
    padding: 0.28rem 0;
}

.leaderboard-title {
    color: var(--ink);
    font-size: 0.82rem;
    font-weight: 700;
    margin-bottom: 0.38rem;
    letter-spacing: 0.02em;
}

.leaderboard-row {
    display: flex;
    justify-content: space-between;
    gap: 0.7rem;
    padding: 0.38rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.leaderboard-row:last-child {
    border-bottom: none;
}

.leaderboard-label {
    color: var(--muted);
    font-size: 0.8rem;
    line-height: 1.35;
}

.leaderboard-value {
    color: var(--ink);
    font-size: 0.8rem;
    font-weight: 600;
    text-align: right;
    line-height: 1.35;
}

.editorial-item {
    display: flex;
    justify-content: space-between;
    gap: 0.8rem;
    color: var(--muted);
    font-size: 0.85rem;
    padding: 0.28rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.editorial-item:last-child {
    border-bottom: none;
}

.stat-card {
    border-radius: var(--radius-lg);
    padding: 0.78rem 0.88rem;
    min-height: 100px;
}

.stat-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--muted);
    margin-bottom: 0.45rem;
}

.stat-value {
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
    font-size: 1.5rem;
    line-height: 1;
    color: var(--ink);
    margin-bottom: 0.28rem;
}

.stat-meta {
    color: var(--accent-deep);
    font-weight: 600;
    font-size: 0.8rem;
}

.insight-card {
    border-radius: var(--radius-md);
    padding: 0.76rem 0.88rem;
    min-height: 82px;
    margin-bottom: 0.4rem;
}

.leaderboard-card {
    border-radius: var(--radius-md);
    padding: 0.78rem 0.88rem;
    margin-bottom: 0.48rem;
}

.leaderboard-title {
    color: var(--ink);
    font-size: 0.86rem;
    font-weight: 800;
    margin-bottom: 0.45rem;
}

.leaderboard-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 0.65rem;
    align-items: center;
    border-top: 1px solid rgba(255,255,255,0.06);
    padding: 0.38rem 0;
}

.leaderboard-row:first-of-type {
    border-top: none;
}

.leaderboard-label {
    min-width: 0;
    color: var(--muted);
    font-size: 0.82rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.leaderboard-value {
    color: var(--accent-deep);
    font-size: 0.8rem;
    font-weight: 700;
}

.insight-title {
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--muted);
    margin-bottom: 0.4rem;
}

.insight-value {
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
    color: var(--ink);
    font-size: 1.06rem;
    margin-bottom: 0.16rem;
}

.insight-copy {
    color: var(--muted);
    font-size: 0.82rem;
    line-height: 1.35;
}

.subnav-wrap [data-testid="stSegmentedControl"] {
    margin-bottom: 0.55rem;
    position: sticky;
    top: 0.35rem;
    z-index: 10;
    padding: 0.2rem 0;
    background: linear-gradient(180deg, rgba(13, 19, 36, 0.94), rgba(13, 19, 36, 0.72));
    backdrop-filter: blur(10px);
}

[data-testid="stMetric"] {
    border-radius: var(--radius-md);
    padding: 0.95rem 1rem;
}

[data-testid="stMetricLabel"] {
    color: var(--muted);
}

[data-testid="stMetricValue"] {
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
}

.stButton > button {
    border-radius: 999px;
    border: 1px solid rgba(233, 176, 79, 0.16);
    background: #17203d;
    color: var(--ink);
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
    font-weight: 600;
    min-height: 42px;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.22);
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent), var(--accent-deep));
    color: #241507;
    border-color: rgba(0, 0, 0, 0);
    box-shadow: 0 10px 28px rgba(233, 176, 79, 0.26);
}

.stTextInput input, .stTextArea textarea, .stDateInput input, .stSelectbox div[data-baseweb="select"] > div {
    background: #0f1630;
    border-radius: 16px;
    color: var(--ink);
    border: 1px solid rgba(126, 133, 255, 0.22);
}

[data-testid="stDataFrame"],
[data-testid="stPlotlyChart"],
[data-testid="stChatMessage"] {
    border-radius: var(--radius-md);
    padding: 0.2rem;
}

[data-testid="stAlert"] {
    border-radius: 18px;
    border: 1px solid var(--line);
}

[data-testid="stFileUploader"] {
    border-radius: 24px;
    padding: 0.35rem;
}

[data-testid="stRadio"] > div {
    background: rgba(16, 18, 50, 0.52);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 0.5rem 0.7rem;
}

[data-testid="stExpander"] {
    border-radius: 18px;
    overflow: hidden;
}

[data-testid="stSidebar"] {
    background: #0c1322;
    border-right: 1px solid var(--line);
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1rem;
}

.sidebar-brand {
    margin-bottom: 1rem;
}

.sidebar-kicker {
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--accent-deep);
    margin-bottom: 0.3rem;
    font-weight: 700;
}

.sidebar-title {
    color: var(--ink);
    font-size: 1.35rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
}

.sidebar-copy {
    color: var(--muted);
    font-size: 0.86rem;
    line-height: 1.45;
}

.sidebar-section {
    margin: 0.75rem 0 0.42rem 0;
    color: var(--accent-deep);
    font-size: 0.76rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-weight: 700;
}

.sidebar-card {
    background: linear-gradient(180deg, #151f32 0%, #101827 100%);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 0.68rem;
    margin-top: 0.45rem;
}

[data-testid="stHorizontalBlock"] {
    gap: 0.75rem;
}

.compact-note {
    color: var(--muted);
    font-size: 0.8rem;
    margin-top: -0.1rem;
    margin-bottom: 0.35rem;
}

.sidebar-card strong {
    color: var(--ink);
}

.sidebar-card p {
    margin: 0.2rem 0 0 0;
    font-size: 0.84rem;
}

.sidebar-status-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.42rem;
    margin-top: 0.45rem;
}

.sidebar-status-pill {
    border-radius: 12px;
    padding: 0.5rem 0.58rem;
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--line);
}

.sidebar-status-pill strong {
    display: block;
    color: var(--ink);
    font-size: 0.76rem;
    margin-bottom: 0.08rem;
}

.sidebar-status-pill span {
    color: var(--muted);
    font-size: 0.74rem;
}

[data-testid="stRadio"] label p,
[data-testid="stSelectbox"] label p,
[data-testid="stTextInput"] label p,
[data-testid="stTextArea"] label p,
[data-testid="stDateInput"] label p {
    color: var(--muted);
}

@media (max-width: 900px) {
    .appbar-shell,
    .action-strip,
    .creator-hero {
        flex-direction: column;
        align-items: flex-start;
        grid-template-columns: 1fr;
    }

    .creator-hero-stats {
        grid-template-columns: 1fr;
    }
}
</style>
"""
