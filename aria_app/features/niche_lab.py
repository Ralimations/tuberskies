from __future__ import annotations

import streamlit as st

from aria_app.ai import build_coach_prompt, stream_aria_response
from aria_app.features.command_center_parts.keyword_tools import build_keyword_opportunity_df, build_title_scorecard
from aria_app.ui import render_editorial_list, render_panel_header, render_section_header


ACTION_LABELS = {
    "title_pack": "Title Pack",
    "hook_pack": "Hook Pack",
    "description_tags": "Description + Tags",
    "content_brief": "Content Brief",
    "fan_request_spin": "Niche Spin",
}


def _run_generation(prompt: str, model: str, last_action: str) -> None:
    with st.chat_message("assistant"):
        response = st.write_stream(stream_aria_response(prompt, model))
    st.session_state.niche_output = response or ""
    st.session_state.niche_last_action = last_action


def _render_concept_builder() -> tuple[str, str, str, str]:
    render_panel_header("Concept Builder", "Shape one song, cover, or request into stronger packaging before it becomes a production task.")
    topic = st.text_area(
        "Song concept, niche direction, or cover idea",
        placeholder="Example: male version of Pretty Little Baby with a softer Broadway ballad treatment",
        height=135,
        key="niche_topic",
    )
    col1, col2 = st.columns([1.05, 0.95])
    working_title = col1.text_input("Working title", placeholder="Pretty Little Baby (Male Version)", key="niche_title")
    model = col2.text_input("Local Ollama model", value=st.session_state.vault_settings.get("ollama_model", "gemma"), key="niche_model")
    selected_action = st.selectbox("Generation mode", options=list(ACTION_LABELS.keys()), format_func=lambda value: ACTION_LABELS[value], key="niche_action")

    button_col1, button_col2 = st.columns([1, 1])
    if button_col1.button("Ask A.R.I.A.", type="primary", use_container_width=True):
        _run_generation(build_coach_prompt(topic, working_title, selected_action), model, ACTION_LABELS[selected_action])
    if button_col2.button("Clear Output", use_container_width=True):
        st.session_state.niche_output = ""
        st.session_state.niche_last_action = "Output cleared."

    return topic, working_title, model, selected_action


def _render_keyword_desk(topic: str, working_title: str) -> None:
    render_panel_header("Keyword + Packaging Desk", "Score the current title and surface lightweight keyword opportunities from the concept.")
    keyword_df = build_keyword_opportunity_df(topic, working_title, st.session_state.calendar_df)
    scorecard_rows = build_title_scorecard(working_title, topic)

    left, right = st.columns([1.2, 0.8])
    with left:
        if keyword_df.empty:
            st.info("Add a topic or working title above to generate keyword opportunities.")
        else:
            st.dataframe(keyword_df, use_container_width=True, hide_index=True)
    with right:
        render_editorial_list("Title Scorecard", scorecard_rows)
        if not keyword_df.empty:
            render_editorial_list("Best Opportunities", [(row["keyword"], f"Score {row['score']:.1f}") for _, row in keyword_df.head(4).iterrows()])


def _render_output_desk() -> None:
    render_panel_header("Output Desk", "Keep the latest generation visible while you decide whether to package, publish, or move it into production.")
    st.text_area("Last Coach Output", value=st.session_state.niche_output, height=280, placeholder="Generated ideas will appear here...")
    left, right = st.columns([1, 1])
    with left:
        render_editorial_list("Generation State", [("Last Action", st.session_state.niche_last_action)])
    with right:
        render_editorial_list(
            "Prompt Hints",
            [
                ("Tone", "Broadway, intimate, celestial, theatrical"),
                ("Frame", "Male version, reimagined ballad, Epic-style storytelling"),
            ],
        )


def render_niche_lab() -> None:
    render_section_header("Ideation", "Niche Lab", "Develop covers, originals, and fan-requested songs into stronger theatrical concepts with A.R.I.A.")

    topic, working_title, model, _ = _render_concept_builder()
    _render_keyword_desk(topic, working_title)
    _render_output_desk()
