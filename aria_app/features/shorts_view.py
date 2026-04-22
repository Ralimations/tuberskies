from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from aria_app.ui import render_editorial_list, render_insight_card, render_panel_header, render_section_header, render_status_strip
from shorts_architect import SHORTS_OUTPUT_DIR, analyze_video_pipeline, render_shorts, save_uploaded_file


def _shorts_status_items() -> list[tuple[str, str]]:
    transcript_ready = st.session_state.transcription_data is not None and not st.session_state.transcription_data.empty
    return [
        ("Transcript", "Ready" if transcript_ready else "Missing"),
        ("Main Video", "Loaded" if st.session_state.shorts_main_video_path else "Missing"),
        ("B-Roll", "Loaded" if st.session_state.shorts_broll_video_path else "Optional"),
        ("Exports", str(len(st.session_state.shorts_outputs))),
    ]


def _render_detected_segments() -> None:
    if not st.session_state.shorts_segments:
        return
    segment_df = pd.DataFrame(st.session_state.shorts_segments)
    avg_duration = (segment_df["end"] - segment_df["start"]).mean() if {"start", "end"}.issubset(segment_df.columns) else 0
    transcript_rows = len(st.session_state.transcription_data) if st.session_state.transcription_data is not None else 0
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    with stat_col1:
        render_insight_card("Candidate Moments", f"{len(segment_df):,}", "High-energy sections queued for Shorts.")
    with stat_col2:
        render_insight_card("Average Length", f"{avg_duration:.1f}s", "Balanced between hook density and replay value.")
    with stat_col3:
        render_insight_card("Transcript Lines", f"{transcript_rows:,}", "Editable caption lines ready for cleanup.")
    st.markdown("### Detected Viral Windows")
    st.dataframe(segment_df, use_container_width=True, hide_index=True)


def render_shorts_architect() -> None:
    render_section_header("Vertical Video", "The Shorts Architect", "Upload a long-form performance, detect high-energy moments, refine the lyrics, and render vertical Shorts locally.")
    active_section = st.session_state.shorts_section
    render_status_strip(_shorts_status_items())

    if active_section == "Ingest":
        render_panel_header("Step 1: Ingestion & Analysis", "Upload the performance master, optionally add B-roll, and let A.R.I.A. find the strongest music moments.")
        upload_col, analysis_col = st.columns([1.2, 0.9])
        with upload_col:
            main_video = st.file_uploader("Main Performance Video", type=["mp4", "mov", "mkv", "avi"], key="shorts_main_upload")
            broll_video = st.file_uploader("B-Roll / Reference Video (Optional for Duet Mode)", type=["mp4", "mov", "mkv", "avi"], key="shorts_broll_upload")
        with analysis_col:
            render_status_strip([("Main Video", main_video.name if main_video else "Waiting"), ("B-Roll", broll_video.name if broll_video else "Optional"), ("GPU Flow", "Transcribe then clear VRAM")])
            whisper_model = st.selectbox("Whisper model for local transcription", options=["tiny", "base", "small", "medium"], index=2, key="shorts_whisper_model")
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
        _render_detected_segments()
        return

    if active_section == "Cutting Room":
        if st.session_state.transcription_data is None or st.session_state.transcription_data.empty:
            st.info("Analyze a performance video in Ingest to unlock The Cutting Room.")
            return
        render_panel_header("Step 2: The Cutting Room", "Refine the transcript, choose the caption styling, and set the short layout before rendering.")
        _render_detected_segments()
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
            render_editorial_list("Current Styling", [("Palette", caption_color), ("Font", font_name), ("Outline", "On" if add_outline else "Off"), ("Layout", layout_mode)])
            if layout_mode == "Duet Mode" and not st.session_state.shorts_broll_video_path:
                st.caption("Duet Mode works best once a B-roll or reference clip has been uploaded in Ingest.")
        st.session_state.shorts_editor_payload = {
            "editable_df": editable_df,
            "caption_color": caption_color,
            "font_name": font_name,
            "add_outline": add_outline,
            "layout_mode": layout_mode,
        }
        return

    if st.session_state.transcription_data is None or st.session_state.transcription_data.empty:
        st.info("Finish analysis first, then return here to render your Shorts.")
        return
    render_panel_header("Step 3: The Render Engine", "Approve the edited lines and export 9:16 vertical shorts into your local output folder.")
    payload = st.session_state.get("shorts_editor_payload", {})
    render_editorial_list(
        "Render Preflight",
        [
            ("Transcript Ready", "Yes" if st.session_state.transcription_data is not None else "No"),
            ("Main Video", "Loaded" if st.session_state.shorts_main_video_path else "Missing"),
            ("B-Roll", "Loaded" if st.session_state.shorts_broll_video_path else "Not attached"),
            ("Layout", payload.get("layout_mode", "Solo Mode")),
            ("Caption Tone", payload.get("caption_color", "#FFD700")),
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
