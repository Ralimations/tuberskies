from __future__ import annotations

import textwrap
from datetime import date
from pathlib import Path
from typing import Iterable

import ollama
import pandas as pd
import plotly.express as px
import streamlit as st

from mock_data import generate_analytics_data, summarize_channel
from shorts_architect import SHORTS_OUTPUT_DIR, analyze_video_pipeline, render_shorts, save_uploaded_file
from storage import PRIORITIES, STAGES, load_calendar, load_vault_settings, save_calendar, save_vault_settings
from youtube_client import get_connection_status, load_live_analytics_placeholder


st.set_page_config(layout="wide", page_title="Ralskies | Starlight Studio")

ARIA_SYSTEM_PROMPT = (
    "You are A.R.I.A. (Algorithmic Retention & Intelligence Assistant), the private AI strategy coach "
    "for the YouTube channel 'Ralskies'. Ralskies is a male vocalist who specializes in theatrical "
    "covers like Epic the Musical and Hazbin Hotel, plus dreamy original songs. His community is called "
    "the Fanskies. Your job is to analyze retention and concept strength, brainstorm high-retention "
    "video ideas, write SEO-optimized metadata for musical covers, and help identify fan song requests "
    "from comments or request dumps. Be encouraging but highly strategic. Respect his DIY BandLab "
    "workflow. When suggesting titles or concepts, lean into emotional, dramatic, reimagined, and "
    "story-driven framing."
)

APP_CSS = """
<style>
:root {
    --bg: #0b1020;
    --surface: #141b33;
    --surface-soft: #1a2342;
    --ink: #eef2ff;
    --muted: #b4bfdc;
    --line: rgba(255, 255, 255, 0.08);
    --accent: #e7b45d;
    --accent-deep: #f3d08c;
    --sky: #6a8cff;
    --shadow: 0 18px 40px rgba(0, 0, 0, 0.22);
    --radius-lg: 24px;
    --radius-md: 18px;
}

.stApp {
    background: linear-gradient(180deg, #0b1020 0%, #101936 52%, #0d1530 100%);
    color: var(--ink);
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stToolbar"] {
    display: none;
}

[data-testid="stDecoration"] {
    display: none;
}

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
    padding-top: 0.75rem;
    padding-bottom: 2rem;
    max-width: 1460px;
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

.hero-shell {
    background: linear-gradient(135deg, #151d39 0%, #10172d 100%);
    border: 1px solid var(--line);
    border-radius: 26px;
    padding: 1.35rem 1.4rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}

.hero-kicker {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    color: var(--accent-deep);
    font-weight: 700;
    margin-bottom: 0.65rem;
}

.hero-title {
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
    font-size: clamp(2.2rem, 4vw, 3.6rem);
    line-height: 0.98;
    color: var(--ink);
    max-width: 11ch;
    margin: 0 0 0.6rem 0;
}

.hero-signature {
    display: inline-block;
    font-family: Georgia, "Times New Roman", serif;
    font-style: italic;
    color: var(--accent-deep);
    margin-right: 0.3rem;
}

.hero-copy {
    max-width: 62ch;
    font-size: 1rem;
    color: var(--muted);
    line-height: 1.7;
}

.hero-note {
    margin-top: 1.2rem;
    display: inline-flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.58rem 0.9rem;
    border-radius: 999px;
    border: 1px solid rgba(246, 207, 135, 0.18);
    background: rgba(255, 255, 255, 0.05);
    color: var(--muted);
    font-size: 0.84rem;
}

.section-chip {
    display: inline-block;
    padding: 0.35rem 0.72rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--line);
    border-radius: 999px;
    font-size: 0.78rem;
    color: var(--accent-deep);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}

.section-title {
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
    font-size: clamp(1.9rem, 2.4vw, 2.8rem);
    color: var(--ink);
    margin: 0 0 0.25rem 0;
}

.section-copy {
    color: var(--muted);
    margin-bottom: 0.75rem;
    max-width: 64ch;
}

.panel-shell {
    background: linear-gradient(180deg, #17203d 0%, #121a32 100%);
    border: 1px solid var(--line);
    border-radius: 22px;
    padding: 1rem 1.05rem 0.85rem 1.05rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}

.panel-title {
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
    color: var(--ink);
    font-size: 1.12rem;
    margin-bottom: 0.2rem;
}

.panel-copy {
    color: var(--muted);
    font-size: 0.92rem;
    margin-bottom: 0.75rem;
}

.masthead-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.7fr) minmax(260px, 0.8fr);
    gap: 1rem;
    align-items: center;
}

.masthead-meta {
    display: grid;
    gap: 0.55rem;
}

.masthead-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.5rem 0.82rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--line);
    color: var(--accent-deep);
    font-size: 0.8rem;
    width: fit-content;
}

.board-lane {
    background: linear-gradient(180deg, #17203d 0%, #121a32 100%);
    border: 1px solid var(--line);
    border-radius: 22px;
    padding: 0.85rem;
    min-height: 220px;
    box-shadow: var(--shadow);
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
    border-radius: 18px;
    padding: 0.7rem 0.75rem;
    margin-bottom: 0.65rem;
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
    background: linear-gradient(180deg, #17203d 0%, #121a32 100%);
    border: 1px solid var(--line);
    border-radius: 22px;
    padding: 1rem;
    box-shadow: var(--shadow);
}

.snapshot-title {
    color: var(--ink);
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
    font-size: 1.2rem;
    margin-bottom: 0.45rem;
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
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 0.75rem 0.8rem;
    margin-bottom: 0.7rem;
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

.status-strip {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.7rem;
    margin-bottom: 0.9rem;
}

.status-chip {
    background: linear-gradient(180deg, #17203d 0%, #121a32 100%);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 0.85rem 0.9rem;
    box-shadow: 0 14px 30px rgba(0, 0, 0, 0.18);
}

.status-chip-label {
    color: var(--muted);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.35rem;
}

.status-chip-value {
    color: var(--ink);
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
    font-size: 1rem;
}

.stat-card {
    background: linear-gradient(180deg, #17203d 0%, #121a32 100%);
    border: 1px solid var(--line);
    border-radius: var(--radius-lg);
    padding: 1rem 1.1rem;
    box-shadow: var(--shadow);
    min-height: 132px;
}

.stat-label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--muted);
    margin-bottom: 0.7rem;
}

.stat-value {
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
    font-size: 2rem;
    line-height: 1;
    color: var(--ink);
    margin-bottom: 0.45rem;
}

.stat-meta {
    color: var(--accent-deep);
    font-weight: 600;
    font-size: 0.92rem;
}

.insight-card {
    background: linear-gradient(180deg, #17203d 0%, #121a32 100%);
    border: 1px solid var(--line);
    border-radius: var(--radius-md);
    padding: 1rem 1.05rem;
    min-height: 110px;
    margin-bottom: 0.7rem;
}

.insight-title {
    font-size: 0.84rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--muted);
    margin-bottom: 0.55rem;
}

.insight-value {
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
    color: var(--ink);
    font-size: 1.55rem;
    margin-bottom: 0.25rem;
}

.insight-copy {
    color: var(--muted);
    font-size: 0.92rem;
}

[data-testid="stTabs"] [role="tablist"] {
    gap: 0.55rem;
    padding: 0.25rem;
    background: #121a32;
    border: 1px solid var(--line);
    border-radius: 999px;
    width: fit-content;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.2);
}

[data-testid="stTabs"] > div[data-baseweb="tab-list"] {
    gap: 0.55rem;
}

[data-testid="stTabs"] [role="tab"] {
    height: 44px;
    padding: 0 1rem;
    border-radius: 999px;
    color: var(--muted);
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
}

[data-testid="stTabs"] [aria-selected="true"] {
    background: linear-gradient(135deg, var(--accent), var(--accent-deep));
    color: #241507 !important;
    box-shadow: 0 10px 28px rgba(233, 176, 79, 0.26);
}

[data-testid="stMetric"] {
    background: linear-gradient(180deg, #17203d 0%, #121a32 100%);
    border: 1px solid var(--line);
    border-radius: var(--radius-md);
    padding: 0.95rem 1rem;
    box-shadow: var(--shadow);
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

[data-testid="stDataFrame"], [data-testid="stPlotlyChart"], [data-testid="stChatMessage"] {
    background: linear-gradient(180deg, #17203d 0%, #121a32 100%);
    border: 1px solid var(--line);
    border-radius: var(--radius-md);
    padding: 0.35rem;
    box-shadow: var(--shadow);
}

[data-testid="stAlert"] {
    border-radius: 18px;
    border: 1px solid var(--line);
}

[data-testid="stFileUploader"] {
    background: linear-gradient(180deg, #17203d 0%, #121a32 100%);
    border: 1px dashed rgba(246, 207, 135, 0.24);
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

@media (max-width: 900px) {
    .masthead-grid {
        grid-template-columns: 1fr;
    }

    .hero-title {
        max-width: 100%;
    }
}
</style>
"""


def initialize_state() -> None:
    if "analytics_df" not in st.session_state:
        st.session_state.analytics_df = generate_analytics_data()
    if "analytics_source" not in st.session_state:
        st.session_state.analytics_source = "Mock Data"
    if "calendar_df" not in st.session_state:
        st.session_state.calendar_df = load_calendar()
    if "vault_settings" not in st.session_state:
        st.session_state.vault_settings = load_vault_settings()
    if "niche_output" not in st.session_state:
        st.session_state.niche_output = ""
    if "niche_last_action" not in st.session_state:
        st.session_state.niche_last_action = "No generation yet."
    if "calendar_coach_output" not in st.session_state:
        st.session_state.calendar_coach_output = ""
    if "calendar_coach_context" not in st.session_state:
        st.session_state.calendar_coach_context = "No repertoire coaching run yet."
    if "transcription_data" not in st.session_state:
        st.session_state.transcription_data = None
    if "shorts_segments" not in st.session_state:
        st.session_state.shorts_segments = []
    if "shorts_main_video_path" not in st.session_state:
        st.session_state.shorts_main_video_path = ""
    if "shorts_broll_video_path" not in st.session_state:
        st.session_state.shorts_broll_video_path = ""
    if "shorts_outputs" not in st.session_state:
        st.session_state.shorts_outputs = []
    if "shorts_analysis_error" not in st.session_state:
        st.session_state.shorts_analysis_error = ""


def inject_theme() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-shell">
            <div class="masthead-grid">
                <div>
                    <div class="hero-kicker">Project A.R.I.A. • Private Strategy Studio</div>
                    <div class="hero-title"><span class="hero-signature">Ralskies</span> Control Room</div>
                    <div class="hero-copy">
                        A cinematic planning deck for theatrical covers, genderbent arrangements, dreamy originals,
                        and fan-requested releases. Designed to feel like the artist portfolio, but rebuilt as a private
                        operating system where A.R.I.A. can guide the next upload, the next Short, and the next era.
                    </div>
                    <div class="hero-note">Offline-first workflow • BandLab-native production • Built for the Fanskies era</div>
                </div>
                <div class="masthead-meta">
                    <div class="masthead-pill">A.R.I.A. retention intelligence online</div>
                    <div class="masthead-pill">Repertoire, shorts, and analytics in one room</div>
                    <div class="masthead-pill">Theatrical cover strategy with zero cloud dependency</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(chip: str, title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="section-chip">{chip}</div>
        <div class="section-title">{title}</div>
        <div class="section-copy">{copy}</div>
        """,
        unsafe_allow_html=True,
    )


def render_stat_card(label: str, value: str, meta: str) -> None:
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
            <div class="stat-meta">{meta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_insight_card(title: str, value: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">{title}</div>
            <div class="insight-value">{value}</div>
            <div class="insight-copy">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stream_ollama_response(prompt: str, model: str) -> Iterable[str]:
    try:
        stream = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": ARIA_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
        for chunk in stream:
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content
    except Exception as error:  # pragma: no cover
        yield f"Local Ollama request failed: {error}"


def build_metric_row(df: pd.DataFrame) -> None:
    snapshot = summarize_channel(df)
    col1, col2, col3 = st.columns(3)
    with col1:
        render_stat_card("Views | Last 30 Days", f"{snapshot.views:,}", "Fanskies discovery is trending upward")
    with col2:
        render_stat_card("Subscribers | Last 30 Days", f"{snapshot.subscribers:,}", "New listeners are converting into community")
    with col3:
        render_stat_card("Watch Time | Last 30 Days", f"{snapshot.watch_time_hours:,}", "Emotional performance depth remains the biggest lever")


def build_health_snapshot(df: pd.DataFrame) -> None:
    latest = df.tail(7)
    previous = df.tail(14).head(7)
    if latest.empty or previous.empty:
        return

    ctr_delta = latest["ctr"].mean() - previous["ctr"].mean()
    retention_delta = latest["retention"].mean() - previous["retention"].mean()
    views_delta = latest["views"].sum() - previous["views"].sum()

    col1, col2, col3 = st.columns(3)
    with col1:
        render_insight_card("CTR Momentum", f"{latest['ctr'].mean():.2f}%", f"{ctr_delta:+.2f} pts versus the previous 7-day window.")
    with col2:
        render_insight_card("Retention Momentum", f"{latest['retention'].mean():.2f}%", f"{retention_delta:+.2f} pts versus the previous 7-day window.")
    with col3:
        render_insight_card("Views Momentum", f"{latest['views'].sum():,}", f"{views_delta:+,} views compared with the previous 7 days.")

def build_analytics_chart(df: pd.DataFrame, metric_name: str) -> None:
    labels = {"ctr": "CTR (%)", "retention": "Retention (%)", "views": "Views"}
    chart = px.line(
        df,
        x="date",
        y=metric_name,
        markers=True,
        title=f"{labels[metric_name]} Over Time",
        template="plotly_white",
    )
    chart.update_traces(line=dict(color="#4DB8FF", width=3), marker=dict(size=6, color="#FFD700"))
    chart.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(26,34,53,0.65)",
        font=dict(color="#edf2ff", family="Inter, Segoe UI, sans-serif"),
        title_font=dict(family="Montserrat, Bahnschrift, sans-serif", size=22),
        xaxis_title=None,
        yaxis_title=None,
    )
    chart.update_xaxes(showgrid=False)
    chart.update_yaxes(gridcolor="rgba(237,242,255,0.08)")
    st.plotly_chart(chart, use_container_width=True)


def get_alert_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df["ctr"] < 5.0) | (df["retention"] < 42.0)].sort_values("date", ascending=False)


def build_coach_prompt(topic: str, working_title: str, action: str) -> str:
    prompts = {
        "title_pack": f"""
        Generate 5 high-retention YouTube titles for Ralskies.
        Lean into emotional, dramatic, theatrical, or reimagined framing.
        Include a one-line angle note under each title.

        Topic: {topic}
        Working title: {working_title}
        """,
        "description_tags": f"""
        Create a YouTube-optimized description and a comma-separated list of SEO tags for Ralskies.
        Favor music-cover discoverability, artist branding, and dramatic emotional phrasing.
        Keep the result clean and skimmable.

        Topic context: {topic}
        Working title: {working_title}
        """,
        "hook_pack": f"""
        Generate 10 opening hooks for a Ralskies video.
        Make them sound natural, emotionally magnetic, theatrical, and high-retention.

        Topic: {topic}
        Working title: {working_title}
        """,
        "content_brief": f"""
        Build a practical YouTube content brief for a Ralskies upload.
        Include target viewer, emotional promise, thumbnail concept, performance angle, outline, and call to action for the Fanskies.

        Topic: {topic}
        Working title: {working_title}
        """,
        "fan_request_spin": f"""
        A fan requested this song for Ralskies.
        Suggest a unique Ralskies spin that transforms it into something theatrical, emotional, or dreamlike.
        Include:
        1. Core reinterpretation angle
        2. Vocal or performance direction
        3. Thumbnail and title framing
        4. Why the Fanskies would respond

        Ko-fi request or song idea: {topic}
        Working title: {working_title}
        """,
    }
    return textwrap.dedent(prompts[action]).strip()


def normalize_calendar_df(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized["title"] = normalized["title"].fillna("").astype(str)
    normalized["stage"] = normalized["stage"].replace("", STAGES[0]).fillna(STAGES[0])
    normalized["priority"] = normalized["priority"].replace("", "Medium").fillna("Medium")
    normalized["content_pillar"] = normalized["content_pillar"].fillna("").astype(str)
    normalized["notes"] = normalized["notes"].fillna("").astype(str)
    normalized["target_upload_date"] = pd.to_datetime(normalized["target_upload_date"], errors="coerce")
    return normalized


def build_idea_prompt(row: pd.Series) -> str:
    target_date = row["target_upload_date"].strftime("%Y-%m-%d") if pd.notna(row["target_upload_date"]) else "Not scheduled yet"
    return textwrap.dedent(
        f"""
        You are A.R.I.A. helping Ralskies sharpen one repertoire idea.
        Review the idea below and respond with:
        1. A blunt potential score out of 10
        2. The biggest upside
        3. The biggest risk
        4. Three concrete improvements
        5. The best immediate next step

        Title: {row["title"]}
        Stage: {row["stage"]}
        Priority: {row["priority"]}
        Content pillar: {row["content_pillar"]}
        Target upload date: {target_date}
        Notes: {row["notes"]}
        """
    ).strip()


def build_timeline_prompt(df: pd.DataFrame) -> str:
    snapshot = df.copy()
    snapshot["target_upload_date"] = snapshot["target_upload_date"].dt.strftime("%Y-%m-%d")
    schedule = snapshot.fillna("").to_csv(index=False)
    return textwrap.dedent(
        f"""
        You are A.R.I.A. reviewing Ralskies' repertoire timeline.
        Respond with:
        1. Overall schedule health
        2. Bottlenecks or risky clusters
        3. Missing deadlines or stage imbalances across song prep, BandLab recording, and editing
        4. Three practical scheduling suggestions for the next two weeks

        Pipeline data:
        {schedule}
        """
    ).strip()


def render_timeline_chart(df: pd.DataFrame) -> None:
    timeline_df = df.copy()
    today = pd.Timestamp(date.today()).normalize()
    stage_offsets = {
        "Song Idea": 14,
        "Instrumental Prep": 10,
        "BandLab Recording": 7,
        "Video Editing": 4,
        "Upload": 1,
    }
    timeline_df["end_date"] = timeline_df["target_upload_date"].fillna(today + pd.to_timedelta(10, unit="D"))
    timeline_df["start_date"] = timeline_df.apply(
        lambda row: row["end_date"] - pd.Timedelta(days=stage_offsets.get(row["stage"], 7)),
        axis=1,
    )
    timeline_df["timeline_label"] = timeline_df["title"].where(timeline_df["title"].str.strip() != "", "Untitled Project")

    chart = px.timeline(
        timeline_df,
        x_start="start_date",
        x_end="end_date",
        y="timeline_label",
        color="stage",
        hover_data=["priority", "content_pillar"],
        color_discrete_map={
            "Song Idea": "#FFD700",
            "Instrumental Prep": "#FFB347",
            "BandLab Recording": "#4DB8FF",
            "Video Editing": "#7f8cff",
            "Upload": "#9ae6b4",
        },
    )
    chart.update_yaxes(autorange="reversed")
    chart.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(26,34,53,0.65)",
        font=dict(color="#edf2ff", family="Inter, Segoe UI, sans-serif"),
        legend_title_text="Stage",
    )
    chart.update_xaxes(gridcolor="rgba(237,242,255,0.08)")
    st.plotly_chart(chart, use_container_width=True)

def render_idea_board(df: pd.DataFrame) -> None:
    priority_rank = {"High": 0, "Medium": 1, "Low": 2}
    ideas = (
        df.assign(priority_rank=df["priority"].map(priority_rank).fillna(1))
        .sort_values(["priority_rank", "stage", "title"], ascending=[True, True, True])
        .drop(columns=["priority_rank"])
        .reset_index(drop=True)
    )
    if ideas.empty:
        st.info("No songs in the board yet. Add a new idea above to start the repertoire.")
        return

    labels = []
    for _, row in ideas.iterrows():
        target = row["target_upload_date"].strftime("%Y-%m-%d") if pd.notna(row["target_upload_date"]) else "Unscheduled"
        labels.append(f"{row['title']} | {row['stage']} | {row['priority']} | {target}")

    selected_label = st.selectbox("Select a song to review", options=labels, key="idea_board_select")
    selected_row = ideas.iloc[labels.index(selected_label)]

    left, right = st.columns([1.05, 1])
    with left:
        st.markdown("### Song Snapshot")
        render_song_snapshot(selected_row)

        coach_col1, coach_col2 = st.columns(2)
        analyze_idea = coach_col1.button("Coach This Song", use_container_width=True)
        next_step = coach_col2.button("Suggest Next Step", use_container_width=True)

        if analyze_idea or next_step:
            model = st.session_state.vault_settings.get("ollama_model", "gemma")
            prompt = build_idea_prompt(selected_row)
            if next_step:
                prompt += "\n\nKeep the answer especially focused on the next concrete action for today."
            with st.chat_message("assistant"):
                response = st.write_stream(stream_ollama_response(prompt, model))
            st.session_state.calendar_coach_output = response or ""
            st.session_state.calendar_coach_context = f"Idea Board: {selected_row['title']}"

    with right:
        st.markdown("### Board View")
        stage_board = ideas.groupby("stage")["title"].apply(list).reindex(STAGES, fill_value=[]).to_dict()
        board_cols = st.columns(len(STAGES))
        for index, stage in enumerate(STAGES):
            with board_cols[index]:
                st.markdown(f"**{stage}**")
                items = stage_board.get(stage, [])
                if not items:
                    st.caption("No items")
                else:
                    for item in items[:5]:
                        st.caption(f"- {item}")


def render_timeline_planner(df: pd.DataFrame) -> None:
    st.markdown("### Timeline Planner")
    scheduled = df[df["target_upload_date"].notna()].sort_values("target_upload_date")
    if scheduled.empty:
        st.info("Add target upload dates to unlock the repertoire timeline.")
        return

    left, right = st.columns([1.25, 1])
    with left:
        render_timeline_chart(scheduled)
    with right:
        st.markdown("### Schedule Pressure")
        next_two_weeks = scheduled[scheduled["target_upload_date"] <= pd.Timestamp(date.today()) + pd.Timedelta(days=14)]
        overdue = scheduled[scheduled["target_upload_date"] < pd.Timestamp(date.today())]
        render_insight_card("Upcoming Projects", str(len(next_two_weeks)), "Songs landing within the next 14 days.")
        render_insight_card("Overdue Targets", str(len(overdue)), "Scheduled targets that have already passed.")
        if st.button("Coach the Timeline", use_container_width=True):
            model = st.session_state.vault_settings.get("ollama_model", "gemma")
            prompt = build_timeline_prompt(scheduled)
            with st.chat_message("assistant"):
                response = st.write_stream(stream_ollama_response(prompt, model))
            st.session_state.calendar_coach_output = response or ""
            st.session_state.calendar_coach_context = "A.R.I.A. Timeline Planner"


def render_command_center() -> None:
    render_section_header(
        "Performance",
        "Command Center",
        "Track discovery, retention, and audience response for theatrical covers, reimagined performances, and original releases.",
    )

    source = st.segmented_control(
        "Data source",
        options=["Mock Data", "Live YouTube"],
        default=st.session_state.analytics_source,
        key="analytics_source_picker",
    )
    st.session_state.analytics_source = source

    live_df, live_message = load_live_analytics_placeholder(st.session_state.vault_settings)
    using_live = source == "Live YouTube" and live_df is not None
    analytics_df = live_df if using_live else st.session_state.analytics_df

    if source == "Live YouTube" and live_df is None:
        st.info(live_message)

    build_metric_row(analytics_df)
    build_health_snapshot(analytics_df)

    selected_metric = st.radio(
        "Chart focus",
        options=["ctr", "retention", "views"],
        format_func=lambda value: value.upper() if value == "ctr" else value.title(),
        horizontal=True,
    )

    left, right = st.columns([1.5, 1])
    with left:
        build_analytics_chart(analytics_df, selected_metric)
    with right:
        render_panel_header(
            "Signal Desk",
            "A tighter read on what A.R.I.A. should pay attention to before you ask for analysis.",
        )
        latest_rows = analytics_df.tail(5).copy()
        latest_rows["date"] = latest_rows["date"].dt.strftime("%Y-%m-%d")
        render_editorial_list(
            "Latest Trend Read",
            [
                (row["date"], f'{row[selected_metric]:,.2f}' if selected_metric != "views" else f'{int(row[selected_metric]):,}')
                for _, row in latest_rows.iterrows()
            ],
        )

        alerts = get_alert_rows(analytics_df).head(5)
        if alerts.empty:
            st.success("No major mock-data alerts right now.")
        else:
            st.warning("Potential weak spots detected in recent performance.")
            alert_rows = []
            for _, row in alerts.iterrows():
                alert_rows.append(
                    (
                        row["date"].strftime("%Y-%m-%d"),
                        f'CTR {row["ctr"]:.2f}% | Retention {row["retention"]:.2f}%',
                    )
                )
            render_editorial_list("Recent Alert Days", alert_rows)

        if st.button("Analyze with A.R.I.A.", key="command_center_coach"):
            model = st.session_state.vault_settings.get("ollama_model", "gemma")
            sample = analytics_df[["date", selected_metric]].tail(14).to_csv(index=False)
            prompt = textwrap.dedent(
                f"""
                Review this Ralskies performance trend and explain what may be happening.
                Focus on practical actions for the next upload cycle.

                Metric: {selected_metric}
                Data:
                {sample}
                """
            ).strip()
            with st.chat_message("assistant"):
                st.write_stream(stream_ollama_response(prompt, model))


def render_panel_header(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="panel-shell">
            <div class="panel-title">{title}</div>
            <div class="panel-copy">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_song_snapshot(selected_row: pd.Series) -> None:
    target = (
        selected_row["target_upload_date"].strftime("%Y-%m-%d")
        if pd.notna(selected_row["target_upload_date"])
        else "Unscheduled"
    )
    pillar = selected_row["content_pillar"] or "Unlabeled"
    notes = selected_row["notes"] or "No notes yet."
    st.markdown(
        f"""
        <div class="snapshot-card">
            <div class="snapshot-title">{selected_row["title"]}</div>
            <div class="snapshot-tags">
                <div class="snapshot-tag">{selected_row["stage"]}</div>
                <div class="snapshot-tag">{selected_row["priority"]} priority</div>
                <div class="snapshot-tag">{pillar}</div>
                <div class="snapshot-tag">{target}</div>
            </div>
            <div class="snapshot-notes">{notes}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_editorial_list(title: str, rows: list[tuple[str, str]]) -> None:
    items = "".join(
        f'<div class="editorial-item"><span>{label}</span><span>{value}</span></div>'
        for label, value in rows
    )
    st.markdown(f"**{title}**")
    st.markdown(f'<div class="editorial-list">{items}</div>', unsafe_allow_html=True)


def render_status_strip(items: list[tuple[str, str]]) -> None:
    html = "".join(
        f"""
        <div class="status-chip">
            <div class="status-chip-label">{label}</div>
            <div class="status-chip-value">{value}</div>
        </div>
        """
        for label, value in items
    )
    st.markdown(f'<div class="status-strip">{html}</div>', unsafe_allow_html=True)


def render_repertoire_stage_board(df: pd.DataFrame) -> None:
    board_cols = st.columns(len(STAGES))
    for index, stage in enumerate(STAGES):
        stage_rows = (
            df[df["stage"] == stage]
            .sort_values(["priority", "target_upload_date", "title"], ascending=[True, True, True])
            .head(4)
        )
        with board_cols[index]:
            cards_html = ""
            if stage_rows.empty:
                cards_html = '<div class="song-card"><div class="song-card-meta">No songs here yet.</div></div>'
            else:
                for _, row in stage_rows.iterrows():
                    target = (
                        row["target_upload_date"].strftime("%Y-%m-%d")
                        if pd.notna(row["target_upload_date"])
                        else "Unscheduled"
                    )
                    pillar = row["content_pillar"] or "Unlabeled"
                    cards_html += f"""
                    <div class="song-card">
                        <div class="song-card-title">{row['title']}</div>
                        <div class="song-card-meta">{row['priority']} priority</div>
                        <div class="song-card-meta">{pillar}</div>
                        <div class="song-card-meta">{target}</div>
                    </div>
                    """

            st.markdown(
                f"""
                <div class="board-lane">
                    <div class="board-lane-title">{stage}</div>
                    {cards_html}
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_shorts_architect() -> None:
    render_section_header(
        "Vertical Video",
        "The Shorts Architect",
        "Upload a long-form performance, detect high-energy moments, refine the lyrics, and render vertical Shorts locally.",
    )

    ingest_tab, cutting_tab, render_tab = st.tabs(["Ingest", "Cutting Room", "Render"])

    with ingest_tab:
        render_panel_header(
            "Step 1: Ingestion & Analysis",
            "Upload the performance master, optionally add B-roll, and let A.R.I.A. find the strongest music moments.",
        )
        upload_col, analysis_col = st.columns([1.2, 0.9])
        with upload_col:
            main_video = st.file_uploader(
                "Main Performance Video",
                type=["mp4", "mov", "mkv", "avi"],
                key="shorts_main_upload",
            )
            broll_video = st.file_uploader(
                "B-Roll / Reference Video (Optional for Duet Mode)",
                type=["mp4", "mov", "mkv", "avi"],
                key="shorts_broll_upload",
            )
        with analysis_col:
            render_status_strip(
                [
                    ("Main Video", main_video.name if main_video else "Waiting"),
                    ("B-Roll", broll_video.name if broll_video else "Optional"),
                    ("GPU Flow", "Transcribe then clear VRAM"),
                ]
            )
            whisper_model = st.selectbox(
                "Whisper model for local transcription",
                options=["tiny", "base", "small", "medium"],
                index=2,
                key="shorts_whisper_model",
            )
            st.caption("`small` is usually the best balance for a first run. Use `medium` only if you want stronger accuracy and have more headroom.")
            if st.button("Analyze Audio & Transcribe", type="primary", key="shorts_analyze"):
                if not main_video:
                    st.error("Upload a main performance video first.")
                else:
                    try:
                        main_path = save_uploaded_file(main_video, "main_video")
                        broll_path = save_uploaded_file(broll_video, "broll_video") if broll_video else None
                        segments, transcription_df = analyze_video_pipeline(main_path, whisper_model=whisper_model)
                        st.session_state.transcription_data = transcription_df
                        st.session_state.shorts_segments = segments
                        st.session_state.shorts_main_video_path = str(main_path)
                        st.session_state.shorts_broll_video_path = str(broll_path) if broll_path else ""
                        st.session_state.shorts_outputs = []
                        st.session_state.shorts_analysis_error = ""
                        st.success("Audio analysis and transcription finished.")
                    except Exception as error:
                        st.session_state.shorts_analysis_error = str(error)
                        st.error(f"Shorts analysis failed: {error}")

        if st.session_state.shorts_analysis_error:
            st.warning(st.session_state.shorts_analysis_error)
        if st.session_state.shorts_segments:
            segment_df = pd.DataFrame(st.session_state.shorts_segments)
            avg_duration = (
                (segment_df["end"] - segment_df["start"]).mean()
                if {"start", "end"}.issubset(segment_df.columns)
                else 0
            )
            transcript_rows = (
                len(st.session_state.transcription_data)
                if st.session_state.transcription_data is not None
                else 0
            )
            stat_col1, stat_col2, stat_col3 = st.columns(3)
            with stat_col1:
                render_insight_card("Candidate Moments", f"{len(segment_df):,}", "High-energy sections currently queued for Shorts.")
            with stat_col2:
                render_insight_card("Average Length", f"{avg_duration:.1f}s", "Balanced between hook density and replay value.")
            with stat_col3:
                render_insight_card("Transcript Lines", f"{transcript_rows:,}", "Editable lyric or caption lines ready for cleanup.")
            st.markdown("### Detected Viral Windows")
            st.dataframe(segment_df, use_container_width=True, hide_index=True)

    with cutting_tab:
        if st.session_state.transcription_data is None or st.session_state.transcription_data.empty:
            st.info("Analyze a performance video in the Ingest tab to unlock The Cutting Room.")
        else:
            render_panel_header(
                "Step 2: The Cutting Room",
                "Refine the transcript, choose the caption styling, and set the short layout before rendering.",
            )
            cutting_room_col, style_col = st.columns([1.55, 1])
            display_df = st.session_state.transcription_data[["segment_id", "start_time", "end_time", "text"]].copy()
            with cutting_room_col:
                editable_df = st.data_editor(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    num_rows="fixed",
                    disabled=["segment_id", "start_time", "end_time"],
                    column_config={
                        "segment_id": st.column_config.NumberColumn("Segment", format="%d"),
                        "start_time": st.column_config.NumberColumn("Start", format="%.2f s"),
                        "end_time": st.column_config.NumberColumn("End", format="%.2f s"),
                        "text": st.column_config.TextColumn("Editable Lyrics / Caption Text", width="large"),
                    },
                    key="shorts_transcription_editor",
                )
            with style_col:
                st.markdown("### Styling Sidebar")
                caption_color = st.color_picker("Caption Color", value="#FFD700")
                font_name = st.selectbox("Font", options=["Montserrat-Bold", "Impact", "Arial-Bold", "Helvetica-Bold"])
                add_outline = st.checkbox("Add Drop Shadow/Outline", value=True)
                layout_mode = st.radio("Layout", options=["Solo Mode", "Duet Mode"], horizontal=False)
                render_editorial_list(
                    "Current Styling",
                    [
                        ("Palette", caption_color),
                        ("Font", font_name),
                        ("Outline", "On" if add_outline else "Off"),
                        ("Layout", layout_mode),
                    ],
                )
                if layout_mode == "Duet Mode" and not st.session_state.shorts_broll_video_path:
                    st.caption("Duet Mode works best once a B-roll or reference clip has been uploaded in Ingest.")

            st.session_state.shorts_editor_payload = {
                "editable_df": editable_df,
                "caption_color": caption_color,
                "font_name": font_name,
                "add_outline": add_outline,
                "layout_mode": layout_mode,
            }

    with render_tab:
        if st.session_state.transcription_data is None or st.session_state.transcription_data.empty:
            st.info("Finish analysis first, then return here to render your Shorts.")
        else:
            render_panel_header(
                "Step 3: The Render Engine",
                "Approve the edited lines and export 9:16 vertical shorts into your local output folder.",
            )
            payload = st.session_state.get("shorts_editor_payload", {})
            render_status_strip(
                [
                    ("Layout", payload.get("layout_mode", "Solo Mode")),
                    ("Caption Tone", payload.get("caption_color", "#FFD700")),
                    ("Exports", str(len(st.session_state.shorts_outputs))),
                ]
            )
            render_editorial_list(
                "Render Preflight",
                [
                    ("Transcript Ready", "Yes" if st.session_state.transcription_data is not None else "No"),
                    ("Main Video", "Loaded" if st.session_state.shorts_main_video_path else "Missing"),
                    ("B-Roll", "Loaded" if st.session_state.shorts_broll_video_path else "Not attached"),
                    ("Output Folder", SHORTS_OUTPUT_DIR.name),
                ],
            )
            if st.button("Approve & Render Shorts", type="primary", key="shorts_render"):
                try:
                    editable_df = payload.get("editable_df")
                    render_df = st.session_state.transcription_data.copy()
                    if editable_df is not None:
                        render_df["text"] = editable_df["text"].fillna("").astype(str)
                    main_video_path = Path(st.session_state.shorts_main_video_path)
                    broll_path = Path(st.session_state.shorts_broll_video_path) if st.session_state.shorts_broll_video_path else None
                    output_paths = render_shorts(
                        main_video_path=main_video_path,
                        broll_video_path=broll_path,
                        transcript_df=render_df,
                        layout_mode=payload.get("layout_mode", "Solo Mode"),
                        text_color=payload.get("caption_color", "#FFD700"),
                        font_name=payload.get("font_name", "Montserrat-Bold"),
                        add_outline=payload.get("add_outline", True),
                    )
                    st.session_state.transcription_data = render_df
                    st.session_state.shorts_outputs = [str(path) for path in output_paths]
                    st.balloons()
                    st.success(f"Rendered {len(output_paths)} short(s) to {SHORTS_OUTPUT_DIR}.")
                except Exception as error:
                    st.error(f"Render failed: {error}")

            if st.session_state.shorts_outputs:
                st.markdown("### Rendered Shorts")
                for output in st.session_state.shorts_outputs:
                    st.video(output)
                    st.caption(output)

def render_niche_lab() -> None:
    render_section_header(
        "Ideation",
        "Niche Lab",
        "Develop covers, originals, and fan-requested songs into stronger theatrical concepts with A.R.I.A.",
    )
    action_labels = {
        "title_pack": "Title Pack",
        "hook_pack": "Hook Pack",
        "description_tags": "Description + Tags",
        "content_brief": "Content Brief",
        "fan_request_spin": "Ralskies Spin",
    }

    idea_tab, request_tab, output_tab = st.tabs(["Idea Forge", "Request Signals", "Output Desk"])

    topic = ""
    fan_request = ""
    comment_dump = ""
    working_title = ""
    model = st.session_state.vault_settings.get("ollama_model", "gemma")
    selected_action = "title_pack"
    run_primary = False
    run_secondary = False
    clear_output = False
    extract_requests = False

    with idea_tab:
        render_panel_header(
            "Concept Builder",
            "Shape a cover, original, or reimagined concept into stronger packaging and clearer strategic direction.",
        )
        topic = st.text_area(
            "Song concept, niche direction, or cover idea",
            placeholder="Example: male version of Pretty Little Baby with a softer Broadway ballad treatment",
            height=140,
        )
        col1, col2 = st.columns(2)
        working_title = col1.text_input("Working title", placeholder="Pretty Little Baby (Male Version)")
        model = col2.text_input("Local Ollama model", value=st.session_state.vault_settings.get("ollama_model", "gemma"))
        selected_action = st.selectbox(
            "Generation mode",
            options=list(action_labels.keys()),
            format_func=lambda value: action_labels[value],
        )
        col1, col2 = st.columns([1, 1.1])
        run_primary = col1.button("Ask A.R.I.A.", type="primary")
        clear_output = col2.button("Clear Output")

    with request_tab:
        render_panel_header(
            "Fan Request Signals",
            "Review Ko-fi requests and pasted comment threads to spot the strongest audience demand.",
        )
        fan_request = st.text_area(
            "Ko-fi / Fanskies request dropbox",
            placeholder="Paste song requests here, one line or one paragraph at a time...",
            height=110,
        )
        comment_dump = st.text_area(
            "Comments / request extraction inbox",
            placeholder="Paste YouTube comments here and A.R.I.A. will try to spot recurring song requests or audience signals...",
            height=140,
        )
        request_col1, request_col2 = st.columns(2)
        run_secondary = request_col1.button("Fan Request Spin")
        extract_requests = request_col2.button("Extract Requests From Comments")

    with output_tab:
        render_panel_header(
            "Output Desk",
            "Keep the latest generation visible while you iterate on concepts and request signals.",
        )
        st.text_area(
            "Last Coach Output",
            value=st.session_state.niche_output,
            height=320,
            placeholder="Generated ideas will appear here...",
        )
        meta_col1, meta_col2 = st.columns([1, 1])
        with meta_col1:
            st.markdown(f"**Last action:** {st.session_state.niche_last_action}")
        with meta_col2:
            st.caption(
                "The best prompts usually include the song, the emotional tone, and whether the framing should feel Broadway, intimate, or celestial."
            )
        with st.expander("Suggested Prompt Language"):
            st.caption(
                "Try phrases like male version, reimagined ballad, Hazbin-style intensity, Epic-style storytelling, or dreamy late-night original."
            )

    if clear_output:
        st.session_state.niche_output = ""
        st.session_state.niche_last_action = "Output cleared."

    if run_primary:
        prompt = build_coach_prompt(topic, working_title, selected_action)
        with st.chat_message("assistant"):
            response = st.write_stream(stream_ollama_response(prompt, model))
        st.session_state.niche_output = response or ""
        st.session_state.niche_last_action = action_labels[selected_action]

    if run_secondary:
        request_topic = fan_request if fan_request.strip() else topic
        prompt = build_coach_prompt(request_topic, working_title, "fan_request_spin")
        with st.chat_message("assistant"):
            response = st.write_stream(stream_ollama_response(prompt, model))
        st.session_state.niche_output = response or ""
        st.session_state.niche_last_action = "Ralskies Spin"

    if extract_requests:
        extraction_prompt = textwrap.dedent(
            f"""
            Review the pasted YouTube comments for Ralskies and extract likely fan song requests.
            Return:
            1. A deduplicated list of requested songs or artists
            2. The most repeated request themes
            3. Which request seems strongest for retention potential
            4. One suggested 'Ralskies spin' for the top request

            Comments:
            {comment_dump}
            """
        ).strip()
        with st.chat_message("assistant"):
            response = st.write_stream(stream_ollama_response(extraction_prompt, model))
        st.session_state.niche_output = response or ""
        st.session_state.niche_last_action = "Comment Request Extraction"



def render_content_calendar() -> None:
    render_section_header(
        "Production",
        "Repertoire",
        "Keep every song moving from first spark to final upload, with workflow pressure and release timing always in view.",
    )

    today = pd.Timestamp(date.today())
    default_due = today + pd.Timedelta(days=7)

    quick_add_col1, quick_add_col2, quick_add_col3, quick_add_col4, quick_add_col5 = st.columns([1.35, 0.95, 0.85, 1, 0.8])
    quick_title = quick_add_col1.text_input("Quick add title", placeholder="New song or cover idea")
    quick_stage = quick_add_col2.selectbox("Quick stage", options=STAGES, index=0)
    quick_priority = quick_add_col3.selectbox("Priority", options=PRIORITIES, index=1)
    quick_date = quick_add_col4.date_input("Target date", value=default_due.to_pydatetime())
    quick_pillar = quick_add_col5.text_input("Pillar", placeholder="Epic Cover")
    add_project = st.button("Add Song")

    if add_project and quick_title.strip():
        new_row = pd.DataFrame(
            [
                {
                    "title": quick_title.strip(),
                    "stage": quick_stage,
                    "priority": quick_priority,
                    "content_pillar": quick_pillar.strip(),
                    "target_upload_date": pd.Timestamp(quick_date),
                    "notes": "",
                }
            ]
        )
        st.session_state.calendar_df = pd.concat([st.session_state.calendar_df, new_row], ignore_index=True)
        save_calendar(st.session_state.calendar_df)
        st.success("Song added to your local repertoire.")

    edited_df = st.data_editor(
        st.session_state.calendar_df,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "title": st.column_config.TextColumn("Song / Video Title", required=True, width="medium"),
            "stage": st.column_config.SelectboxColumn("Stage", options=STAGES, required=True),
            "priority": st.column_config.SelectboxColumn("Priority", options=PRIORITIES, required=True),
            "content_pillar": st.column_config.TextColumn("Pillar", width="small"),
            "target_upload_date": st.column_config.DateColumn("Target Upload Date", format="YYYY-MM-DD"),
            "notes": st.column_config.TextColumn("Notes", width="large"),
        },
        key="content_calendar_editor",
    )
    edited_df = normalize_calendar_df(edited_df)

    stage_counts = edited_df["stage"].value_counts().reindex(STAGES, fill_value=0)
    due_soon = edited_df[
        edited_df["target_upload_date"].notna()
        & (edited_df["target_upload_date"] >= today)
        & (edited_df["target_upload_date"] <= today + pd.Timedelta(days=14))
    ].sort_values("target_upload_date")
    ready_count = int(stage_counts.get("Upload", 0))

    top_row1, top_row2, top_row3 = st.columns(3)
    with top_row1:
        render_insight_card("Total Songs", f"{len(edited_df):,}", "All active concepts currently in the local repertoire.")
    with top_row2:
        render_insight_card("Ready to Upload", str(ready_count), "Songs that are ready for release scheduling.")
    with top_row3:
        render_insight_card("Due in 14 Days", f"{len(due_soon):,}", "Upcoming deadlines worth protecting this week.")

    render_panel_header(
        "Visual Board",
        "Scan the current repertoire by stage before dropping into the detailed editor and planning tools.",
    )
    render_repertoire_stage_board(edited_df)

    left, right = st.columns([1.2, 1])
    with left:
        stage_chart = px.bar(
            x=stage_counts.index,
            y=stage_counts.values,
            labels={"x": "Repertoire Stage", "y": "Songs"},
            title="Repertoire Load",
            template="plotly_white",
        )
        stage_chart.update_traces(marker_color="#4DB8FF")
        stage_chart.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(26,34,53,0.65)",
            font=dict(color="#edf2ff", family="Inter, Segoe UI, sans-serif"),
            title_font=dict(family="Montserrat, Bahnschrift, sans-serif", size=22),
        )
        stage_chart.update_xaxes(showgrid=False)
        stage_chart.update_yaxes(gridcolor="rgba(237,242,255,0.08)")
        st.plotly_chart(stage_chart, use_container_width=True)
    with right:
        st.markdown("### Upcoming Deadlines")
        if due_soon.empty:
            st.info("No songs due in the next 14 days.")
        else:
            st.dataframe(due_soon[["title", "stage", "target_upload_date"]], use_container_width=True, hide_index=True)

    board_tab, timeline_tab, coach_tab = st.tabs(["Idea Board", "Timeline", "A.R.I.A. Notes"])
    with board_tab:
        render_idea_board(edited_df)
    with timeline_tab:
        render_timeline_planner(edited_df)
    with coach_tab:
        st.markdown(f"### {st.session_state.calendar_coach_context}")
        st.text_area(
            "Latest Coach Feedback",
            value=st.session_state.calendar_coach_output,
            height=260,
            placeholder="Run song or timeline coaching to keep suggestions here.",
        )

    action_col1, action_col2 = st.columns([1, 1.5])
    if action_col1.button("Save Repertoire"):
        st.session_state.calendar_df = edited_df
        save_calendar(edited_df)
        st.success("Repertoire saved locally.")
    if action_col2.button("Autosave Current Table"):
        st.session_state.calendar_df = edited_df
        save_calendar(edited_df)
        st.success("Current repertoire state saved.")


def render_vault() -> None:
    render_section_header(
        "Infrastructure",
        "The Vault",
        "Store defaults, model preferences, and future API credentials locally so the studio stays private, reusable, and aligned with Ralskies and A.R.I.A.",
    )
    vault = st.session_state.vault_settings
    connection = get_connection_status(vault)

    left, right = st.columns([1.35, 0.85])
    with left:
        render_panel_header(
            "Local Defaults",
            "Keep reusable metadata and model settings here so each new upload starts from a consistent base.",
        )
        if connection.connected:
            st.success(connection.message)
        else:
            st.info(connection.message)

        default_description = st.text_area(
            "Default Description",
            value=vault.get("default_description", ""),
            height=220,
            placeholder="Standard links, music platform URLs, Discord, and gear list...",
        )
        ollama_model = st.selectbox(
            "Local LLM Model",
            options=["gemma", "gemma:7b", "llama3:8b", "gemma4:e2b"],
            index=["gemma", "gemma:7b", "llama3:8b", "gemma4:e2b"].index(vault.get("ollama_model", "gemma"))
            if vault.get("ollama_model", "gemma") in ["gemma", "gemma:7b", "llama3:8b", "gemma4:e2b"]
            else 0,
        )

    with right:
        render_panel_header(
            "API & Runtime",
            "Credentials can stay empty until you switch on live YouTube data. The app remains fully local without them.",
        )
        youtube_api_key = st.text_input("YouTube API Key", value=vault.get("youtube_api_key", ""), type="password", placeholder="Leave blank for now")
        youtube_client_id = st.text_input("YouTube Client ID", value=vault.get("youtube_client_id", ""), type="password", placeholder="Leave blank for now")
        youtube_client_secret = st.text_input("YouTube Client Secret", value=vault.get("youtube_client_secret", ""), type="password", placeholder="Leave blank for now")
        render_editorial_list(
            "Setup Notes",
            [
                ("Privacy", "Local-first by default"),
                ("Live Data", "Optional until API keys are added"),
                ("Model Runtime", "Depends on your local Ollama install"),
            ],
        )

    if st.button("Save Vault Settings"):
        updated = {
            "DEFAULT_DESCRIPTION": default_description,
            "YOUTUBE_API_KEY": youtube_api_key,
            "YOUTUBE_CLIENT_ID": youtube_client_id,
            "YOUTUBE_CLIENT_SECRET": youtube_client_secret,
            "OLLAMA_MODEL": ollama_model,
        }
        save_vault_settings(updated)
        st.session_state.vault_settings = load_vault_settings()
        st.success("Vault settings saved to your local .env file.")


def main() -> None:
    initialize_state()
    inject_theme()
    render_hero()

    command_center, niche_lab, repertoire, shorts_architect, vault = st.tabs(
        ["Command Center", "Niche Lab", "Repertoire", "Shorts Architect", "The Vault"]
    )

    with command_center:
        render_command_center()
    with niche_lab:
        render_niche_lab()
    with repertoire:
        render_content_calendar()
    with shorts_architect:
        render_shorts_architect()
    with vault:
        render_vault()


if __name__ == "__main__":
    main()
