from __future__ import annotations


APP_CSS = """
<style>
:root {
    --bg: #0d1324;
    --surface: #151d34;
    --surface-soft: #1b2542;
    --ink: #edf2ff;
    --muted: #a8b5d3;
    --line: rgba(255, 255, 255, 0.08);
    --accent: #e2b15b;
    --accent-deep: #f2cf8c;
    --sky: #79a0ff;
    --shadow: 0 18px 40px rgba(0, 0, 0, 0.2);
    --radius-lg: 22px;
    --radius-md: 16px;
}

.stApp {
    background:
        radial-gradient(circle at top right, rgba(121, 160, 255, 0.1), transparent 22%),
        linear-gradient(180deg, #0d1324 0%, #101935 52%, #0d1530 100%);
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
    background: linear-gradient(135deg, #151d34 0%, #12192d 100%);
    border: 1px solid var(--line);
    border-radius: 18px;
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
    border-radius: 12px;
    display: grid;
    place-items: center;
    background: linear-gradient(135deg, rgba(226, 177, 91, 0.24), rgba(121, 160, 255, 0.18));
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

.board-lane,
.snapshot-card,
.stat-card,
.insight-card,
[data-testid="stMetric"],
[data-testid="stDataFrame"],
[data-testid="stPlotlyChart"],
[data-testid="stChatMessage"],
[data-testid="stFileUploader"] {
    background: linear-gradient(180deg, #17203d 0%, #121a32 100%);
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
    min-height: 94px;
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
    font-size: 1.42rem;
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
    background: #0f172d;
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
    background: linear-gradient(180deg, #17203d 0%, #121a32 100%);
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
    .action-strip {
        flex-direction: column;
        align-items: flex-start;
    }
}
</style>
"""
