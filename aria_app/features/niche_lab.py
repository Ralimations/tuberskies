from __future__ import annotations

import textwrap

import streamlit as st

from aria_app.ai import build_coach_prompt, stream_ollama_response
from aria_app.features.command_center import build_keyword_opportunity_df, build_title_scorecard
from aria_app.ui import render_editorial_list, render_panel_header, render_section_header


def render_niche_lab() -> None:
    render_section_header("Ideation", "Niche Lab", "Develop covers, originals, and fan-requested songs into stronger theatrical concepts with A.R.I.A.")
    action_labels = {
        "title_pack": "Title Pack",
        "hook_pack": "Hook Pack",
        "description_tags": "Description + Tags",
        "content_brief": "Content Brief",
        "fan_request_spin": "Ralskies Spin",
    }

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

    st.markdown('<div class="subnav-wrap">', unsafe_allow_html=True)
    active_section = st.segmented_control(
        "Niche Lab Section",
        options=["Idea Forge", "Request Signals", "Keyword Desk", "Output Desk"],
        default="Idea Forge",
        key="niche_lab_section",
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if active_section == "Idea Forge":
        render_panel_header("Concept Builder", "Shape a cover, original, or reimagined concept into stronger packaging and clearer strategic direction.")
        topic = st.text_area(
            "Song concept, niche direction, or cover idea",
            placeholder="Example: male version of Pretty Little Baby with a softer Broadway ballad treatment",
            height=140,
            key="niche_topic",
        )
        col1, col2 = st.columns(2)
        working_title = col1.text_input("Working title", placeholder="Pretty Little Baby (Male Version)", key="niche_title")
        model = col2.text_input("Local Ollama model", value=st.session_state.vault_settings.get("ollama_model", "gemma"), key="niche_model")
        selected_action = st.selectbox("Generation mode", options=list(action_labels.keys()), format_func=lambda value: action_labels[value], key="niche_action")
        col1, col2 = st.columns([1, 1.1])
        run_primary = col1.button("Ask A.R.I.A.", type="primary")
        clear_output = col2.button("Clear Output")
    elif active_section == "Request Signals":
        render_panel_header("Fan Request Signals", "Review Ko-fi requests and pasted comment threads to spot the strongest audience demand.")
        fan_request = st.text_area("Ko-fi / Fanskies request dropbox", placeholder="Paste song requests here, one line or one paragraph at a time...", height=110, key="niche_request")
        comment_dump = st.text_area("Comments / request extraction inbox", placeholder="Paste YouTube comments here and A.R.I.A. will try to spot recurring song requests or audience signals...", height=140, key="niche_comments")
        request_col1, request_col2 = st.columns(2)
        run_secondary = request_col1.button("Fan Request Spin")
        extract_requests = request_col2.button("Extract Requests From Comments")
    elif active_section == "Keyword Desk":
        topic = st.session_state.get("niche_topic", "")
        working_title = st.session_state.get("niche_title", "")
        render_panel_header("Keyword Desk", "A local opportunity view inspired by keyword explorers and packaging scorecards in creator growth tools.")
        keyword_df = build_keyword_opportunity_df(topic, working_title, st.session_state.calendar_df)
        scorecard_rows = build_title_scorecard(working_title, topic)
        left, right = st.columns([1.2, 0.8])
        with left:
            if keyword_df.empty:
                st.info("Add a topic or working title in Idea Forge to generate keyword opportunities.")
            else:
                st.dataframe(keyword_df, use_container_width=True, hide_index=True)
        with right:
            render_editorial_list("Title Scorecard", scorecard_rows)
            if not keyword_df.empty:
                render_editorial_list("Best Opportunities", [(row["keyword"], f"Score {row['score']:.1f}") for _, row in keyword_df.head(4).iterrows()])
    else:
        render_panel_header("Output Desk", "Keep the latest generation visible while you iterate on concepts and request signals.")
        st.text_area("Last Coach Output", value=st.session_state.niche_output, height=320, placeholder="Generated ideas will appear here...")
        meta_col1, meta_col2 = st.columns([1, 1])
        with meta_col1:
            st.markdown(f"**Last action:** {st.session_state.niche_last_action}")
        with meta_col2:
            st.caption("The best prompts usually include the song, the emotional tone, and whether the framing should feel Broadway, intimate, or celestial.")
        with st.expander("Suggested Prompt Language"):
            st.caption("Try phrases like male version, reimagined ballad, Hazbin-style intensity, Epic-style storytelling, or dreamy late-night original.")

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
        request_topic = fan_request if fan_request.strip() else st.session_state.get("niche_topic", "")
        prompt = build_coach_prompt(request_topic, st.session_state.get("niche_title", ""), "fan_request_spin")
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
