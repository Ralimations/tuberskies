from __future__ import annotations

import textwrap
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from aria_app.ai import stream_aria_response
from aria_app.ui import (
    render_editorial_list,
    render_insight_card,
    render_panel_header,
    render_section_header,
    render_song_snapshot,
)
from storage import PRIORITIES, STAGES, save_calendar


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
                    target = row["target_upload_date"].strftime("%Y-%m-%d") if pd.notna(row["target_upload_date"]) else "Unscheduled"
                    pillar = row["content_pillar"] or "Unlabeled"
                    cards_html += (
                        '<div class="song-card">'
                        f'<div class="song-card-title">{row["title"]}</div>'
                        f'<div class="song-card-meta">{row["priority"]} priority</div>'
                        f'<div class="song-card-meta">{pillar}</div>'
                        f'<div class="song-card-meta">{target}</div>'
                        '</div>'
                    )
            st.markdown(f'<div class="board-lane"><div class="board-lane-title">{stage}</div>{cards_html}</div>', unsafe_allow_html=True)


def render_timeline_chart(df: pd.DataFrame) -> None:
    timeline_df = df.copy()
    today = pd.Timestamp(date.today()).normalize()
    stage_offsets = {"Song Idea": 14, "Instrumental Prep": 10, "BandLab Recording": 7, "Video Editing": 4, "Upload": 1}
    timeline_df["end_date"] = timeline_df["target_upload_date"].fillna(today + pd.to_timedelta(10, unit="D"))
    timeline_df["start_date"] = timeline_df.apply(lambda row: row["end_date"] - pd.Timedelta(days=stage_offsets.get(row["stage"], 7)), axis=1)
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
                response = st.write_stream(stream_aria_response(prompt, model))
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
                response = st.write_stream(stream_aria_response(prompt, model))
            st.session_state.calendar_coach_output = response or ""
            st.session_state.calendar_coach_context = "A.R.I.A. Timeline Planner"


def render_repertoire_header_metrics(edited_df: pd.DataFrame, today: pd.Timestamp) -> None:
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
        render_insight_card("Ready to Upload", str(ready_count), "Songs ready for release scheduling.")
    with top_row3:
        render_insight_card("Due in 14 Days", f"{len(due_soon):,}", "Upcoming deadlines worth protecting this week.")


def render_quick_add_song(today: pd.Timestamp) -> None:
    with st.expander("Add or edit songs", expanded=False):
        default_due = today + pd.Timedelta(days=7)
        quick_add_col1, quick_add_col2, quick_add_col3, quick_add_col4, quick_add_col5 = st.columns([1.35, 0.95, 0.85, 1, 0.8])
        quick_title = quick_add_col1.text_input("Quick add title", placeholder="New song or cover idea")
        quick_stage = quick_add_col2.selectbox("Quick stage", options=STAGES, index=0)
        quick_priority = quick_add_col3.selectbox("Priority", options=PRIORITIES, index=1)
        quick_date = quick_add_col4.date_input("Target date", value=default_due.to_pydatetime())
        quick_pillar = quick_add_col5.text_input("Pillar", placeholder="Epic Cover")
        if st.button("Add Song"):
            if quick_title.strip():
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
            else:
                st.warning("Add a title before saving a new song.")

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
        col1, col2 = st.columns([1, 1.5])
        if col1.button("Save Repertoire"):
            st.session_state.calendar_df = edited_df
            save_calendar(edited_df)
            st.success("Repertoire saved locally.")
        if col2.button("Autosave Current Table"):
            st.session_state.calendar_df = edited_df
            save_calendar(edited_df)
            st.success("Current repertoire state saved.")


def render_repertoire_overview(edited_df: pd.DataFrame) -> None:
    stage_counts = edited_df["stage"].value_counts().reindex(STAGES, fill_value=0)
    render_panel_header("Visual Board", "Scan the current repertoire by stage, then drop into coaching or schedule pressure only when needed.")
    render_repertoire_stage_board(edited_df)
    left, right = st.columns([1.2, 1])
    with left:
        stage_chart = px.bar(x=stage_counts.index, y=stage_counts.values, labels={"x": "Repertoire Stage", "y": "Songs"}, title="Repertoire Load", template="plotly_dark")
        stage_chart.update_traces(marker_color="#2d7df0")
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
        stage_rows = [(stage, f"{int(stage_counts.get(stage, 0))} song(s)") for stage in STAGES]
        render_editorial_list("Stage Load", stage_rows)


def render_repertoire() -> None:
    render_section_header("Production", "Repertoire", "Keep every song moving from first spark to final upload, with workflow pressure and release timing always in view.")

    today = pd.Timestamp(date.today())
    edited_df = normalize_calendar_df(st.session_state.calendar_df)
    render_repertoire_header_metrics(edited_df, today)
    render_quick_add_song(today)

    active_section = st.session_state.repertoire_section

    if active_section == "Idea Board":
        render_repertoire_overview(edited_df)
        render_idea_board(edited_df)
    elif active_section == "Timeline":
        render_timeline_planner(edited_df)
    else:
        st.markdown(f"### {st.session_state.calendar_coach_context}")
        st.text_area("Latest Coach Feedback", value=st.session_state.calendar_coach_output, height=260, placeholder="Run song or timeline coaching to keep suggestions here.")
