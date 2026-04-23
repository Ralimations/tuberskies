from __future__ import annotations

import json
import math
import uuid
from pathlib import Path
from typing import Any

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
SHORTS_WORKDIR = BASE_DIR / "data" / "shorts_workdir"
SHORTS_OUTPUT_DIR = BASE_DIR / "shorts_output"
SHORTS_WORKDIR.mkdir(parents=True, exist_ok=True)
SHORTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_uploaded_file(uploaded_file: Any, prefix: str) -> Path:
    suffix = Path(uploaded_file.name).suffix or ".bin"
    destination = SHORTS_WORKDIR / f"{prefix}_{uuid.uuid4().hex}{suffix}"
    destination.write_bytes(uploaded_file.getbuffer())
    return destination


def save_uploaded_bytes(filename: str, content: bytes, prefix: str) -> Path:
    suffix = Path(filename).suffix or ".bin"
    destination = SHORTS_WORKDIR / f"{prefix}_{uuid.uuid4().hex}{suffix}"
    destination.write_bytes(content)
    return destination


def sample_video_frames(video_path: Path, frame_count: int = 6) -> list[Path]:
    from moviepy.editor import VideoFileClip

    frame_paths: list[Path] = []
    with VideoFileClip(str(video_path)) as clip:
        duration = max(float(clip.duration or 0), 0)
        if duration <= 0:
            return []
        for index in range(frame_count):
            timestamp = min(duration - 0.05, duration * ((index + 1) / (frame_count + 1)))
            frame_path = SHORTS_WORKDIR / f"{video_path.stem}_frame_{index + 1}.jpg"
            clip.save_frame(str(frame_path), t=max(timestamp, 0))
            frame_paths.append(frame_path)
    return frame_paths


def preview_shorts_frames(video_path: Path, shorts_plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from moviepy.editor import VideoFileClip

    previews: list[dict[str, Any]] = []
    with VideoFileClip(str(video_path)) as clip:
        duration = max(float(clip.duration or 0), 0)
        if duration <= 0:
            return []
        for index, plan in enumerate(shorts_plan, start=1):
            start = max(0.0, float(plan.get("start", 0) or 0))
            end = min(duration, float(plan.get("end", start + 35) or start + 35))
            if end <= start:
                continue
            timestamp = min(duration - 0.05, start + ((end - start) / 2))
            frame_path = SHORTS_WORKDIR / f"{video_path.stem}_cut_{index}_preview_{uuid.uuid4().hex[:8]}.jpg"
            clip.save_frame(str(frame_path), t=max(timestamp, 0))
            previews.append(
                {
                    "index": index - 1,
                    "start": round(start, 2),
                    "end": round(end, 2),
                    "timestamp": round(timestamp, 2),
                    "path": str(frame_path),
                }
            )
    return previews


def extract_audio_from_video(video_path: Path) -> Path:
    from moviepy.editor import VideoFileClip

    audio_path = SHORTS_WORKDIR / f"{video_path.stem}_audio.wav"
    with VideoFileClip(str(video_path)) as clip:
        if clip.audio is None:
            raise ValueError("The uploaded performance video has no audio track.")
        clip.audio.write_audiofile(str(audio_path), fps=16000, logger=None)
    return audio_path


def detect_high_energy_segments(
    audio_path: Path,
    segment_count: int = 5,
    min_duration: int = 30,
    max_duration: int = 60,
) -> list[dict[str, float]]:
    import librosa
    import numpy as np

    audio, sample_rate = librosa.load(str(audio_path), sr=16000, mono=True)
    duration = librosa.get_duration(y=audio, sr=sample_rate)
    if duration <= 0:
        return []

    frame_length = 2048
    hop_length = 512
    rms = librosa.feature.rms(y=audio, frame_length=frame_length, hop_length=hop_length)[0]
    spectral = librosa.onset.onset_strength(y=audio, sr=sample_rate, hop_length=hop_length)
    combined = (rms[: len(spectral)] * 0.65) + (spectral * 0.35)
    frame_times = librosa.frames_to_time(range(len(combined)), sr=sample_rate, hop_length=hop_length)

    desired_duration = min(max_duration, max(min_duration, int(duration / max(segment_count, 1))))
    candidates: list[dict[str, float]] = []
    for index, score in enumerate(combined):
        center = float(frame_times[index])
        start = max(0.0, center - desired_duration / 2)
        end = min(duration, start + desired_duration)
        start = max(0.0, end - desired_duration)
        candidates.append({"start": round(start, 2), "end": round(end, 2), "score": float(score)})

    selected: list[dict[str, float]] = []
    for candidate in sorted(candidates, key=lambda item: item["score"], reverse=True):
        overlaps = any(
            not (candidate["end"] <= chosen["start"] or candidate["start"] >= chosen["end"])
            for chosen in selected
        )
        if overlaps:
            continue
        selected.append(candidate)
        if len(selected) >= segment_count:
            break

    if not selected:
        selected.append({"start": 0.0, "end": min(duration, float(max_duration)), "score": 0.0})

    return sorted(selected, key=lambda item: item["start"])


def transcribe_segments(video_path: Path, segments: list[dict[str, float]], model_size: str = "small") -> pd.DataFrame:
    import torch
    from faster_whisper import WhisperModel
    from moviepy.editor import VideoFileClip

    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    rows: list[dict[str, Any]] = []
    try:
        with VideoFileClip(str(video_path)) as clip:
            for segment_index, segment in enumerate(segments, start=1):
                segment_path = SHORTS_WORKDIR / f"{video_path.stem}_segment_{segment_index}.wav"
                clip.audio.subclip(segment["start"], segment["end"]).write_audiofile(
                    str(segment_path),
                    fps=16000,
                    logger=None,
                )

                whisper_segments, _ = model.transcribe(
                    str(segment_path),
                    word_timestamps=True,
                    vad_filter=True,
                )
                for item in whisper_segments:
                    words = []
                    for word in item.words or []:
                        words.append(
                            {
                                "start": round(segment["start"] + float(word.start), 2),
                                "end": round(segment["start"] + float(word.end), 2),
                                "word": word.word.strip(),
                            }
                        )
                    rows.append(
                        {
                            "segment_id": segment_index,
                            "start_time": round(segment["start"] + float(item.start), 2),
                            "end_time": round(segment["start"] + float(item.end), 2),
                            "text": item.text.strip(),
                            "words_json": json.dumps(words),
                        }
                    )
    finally:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    if not rows:
        return pd.DataFrame(columns=["segment_id", "start_time", "end_time", "text", "words_json"])

    return pd.DataFrame(rows)


def analyze_video_pipeline(video_path: Path, whisper_model: str = "small") -> tuple[list[dict[str, float]], pd.DataFrame]:
    audio_path = extract_audio_from_video(video_path)
    segments = detect_high_energy_segments(audio_path)
    transcription_df = transcribe_segments(video_path, segments, model_size=whisper_model)
    return segments, transcription_df


def words_for_row(row: pd.Series) -> list[dict[str, Any]]:
    raw_words = row.get("words_json", "[]") or "[]"
    try:
        original_words = json.loads(raw_words)
    except json.JSONDecodeError:
        original_words = []

    edited_words = [word for word in str(row.get("text", "")).split() if word.strip()]
    if not edited_words:
        return []

    if original_words and len(original_words) == len(edited_words):
        remapped = []
        for original, replacement in zip(original_words, edited_words):
            remapped.append(
                {
                    "start": float(original["start"]),
                    "end": float(original["end"]),
                    "word": replacement,
                }
            )
        return remapped

    start_time = float(row["start_time"])
    end_time = float(row["end_time"])
    total_duration = max(end_time - start_time, 0.2)
    chunk = total_duration / max(len(edited_words), 1)
    rebuilt = []
    for index, word in enumerate(edited_words):
        word_start = start_time + (index * chunk)
        word_end = start_time + ((index + 1) * chunk)
        rebuilt.append({"start": round(word_start, 2), "end": round(word_end, 2), "word": word})
    return rebuilt


def _caption_style_kwargs(add_outline: bool, text_color: str, font_name: str) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "font": font_name,
        "fontsize": 62,
        "color": text_color,
        "method": "caption",
        "align": "center",
        "size": (920, None),
    }
    if add_outline:
        kwargs["stroke_color"] = "black"
        kwargs["stroke_width"] = 3
    return kwargs


def render_shorts(
    main_video_path: Path,
    broll_video_path: Path | None,
    transcript_df: pd.DataFrame,
    layout_mode: str,
    text_color: str,
    font_name: str,
    add_outline: bool,
) -> list[Path]:
    from moviepy.editor import ColorClip, CompositeVideoClip, TextClip, VideoFileClip

    outputs: list[Path] = []
    with VideoFileClip(str(main_video_path)) as main_clip:
        broll_clip = VideoFileClip(str(broll_video_path)) if broll_video_path else None
        try:
            for segment_id, group in transcript_df.groupby("segment_id", sort=True):
                clip_start = float(group["start_time"].min())
                clip_end = float(group["end_time"].max())
                performance_clip = main_clip.subclip(clip_start, clip_end)

                canvas_width = 1080
                canvas_height = 1920
                output_name = SHORTS_OUTPUT_DIR / f"short_{segment_id}_{uuid.uuid4().hex[:8]}.mp4"

                if layout_mode == "Solo Mode":
                    video_layer = performance_clip.resize(height=canvas_height)
                    if video_layer.w > canvas_width:
                        x_center = video_layer.w / 2
                        video_layer = video_layer.crop(
                            x_center=x_center,
                            width=canvas_width,
                            height=canvas_height,
                        )
                    else:
                        video_layer = video_layer.on_color(
                            size=(canvas_width, canvas_height),
                            color=(10, 15, 29),
                            pos=("center", "center"),
                        )
                else:
                    if broll_clip is None:
                        raise ValueError("Duet Mode requires a B-Roll / Reference Video upload.")
                    duet_clip = broll_clip.subclip(clip_start, clip_end)
                    top = duet_clip.resize(width=canvas_width).crop(width=canvas_width, height=canvas_height // 2)
                    bottom = performance_clip.resize(width=canvas_width).crop(width=canvas_width, height=canvas_height // 2)
                    top = top.set_position((0, 0))
                    bottom = bottom.set_position((0, canvas_height // 2))
                    base = ColorClip((canvas_width, canvas_height), color=(10, 15, 29), duration=performance_clip.duration)
                    video_layer = CompositeVideoClip([base, top, bottom], size=(canvas_width, canvas_height))

                caption_clips = []
                style_kwargs = _caption_style_kwargs(add_outline, text_color, font_name)
                for _, row in group.iterrows():
                    for word in words_for_row(row):
                        word_start = max(0.0, float(word["start"]) - clip_start)
                        word_duration = max(float(word["end"]) - float(word["start"]), 0.08)
                        text_clip = (
                            TextClip(word["word"], **style_kwargs)
                            .set_start(word_start)
                            .set_duration(word_duration)
                            .set_position(("center", canvas_height - 360))
                        )
                        caption_clips.append(text_clip)

                final_clip = CompositeVideoClip([video_layer, *caption_clips], size=(canvas_width, canvas_height))
                final_clip = final_clip.set_audio(performance_clip.audio)
                final_clip.write_videofile(
                    str(output_name),
                    fps=30,
                    codec="libx264",
                    audio_codec="aac",
                    logger=None,
                )
                outputs.append(output_name)
                final_clip.close()
        finally:
            if broll_clip is not None:
                broll_clip.close()

    return outputs


def _fit_vertical_clip(clip: Any, canvas_width: int, canvas_height: int) -> Any:
    video_layer = clip.resize(height=canvas_height)
    if video_layer.w > canvas_width:
        return video_layer.crop(x_center=video_layer.w / 2, width=canvas_width, height=canvas_height)
    return video_layer.on_color(
        size=(canvas_width, canvas_height),
        color=(10, 15, 29),
        pos=("center", "center"),
    )


def render_ai_shorts(
    main_video_path: Path,
    broll_video_path: Path | None,
    shorts_plan: list[dict[str, Any]],
    layout_mode: str,
    text_color: str,
    font_name: str = "Arial",
    add_outline: bool = True,
) -> list[Path]:
    from moviepy.editor import ColorClip, CompositeVideoClip, TextClip, VideoFileClip

    outputs: list[Path] = []
    canvas_width = 1080
    canvas_height = 1920

    with VideoFileClip(str(main_video_path)) as main_clip:
        broll_clip = VideoFileClip(str(broll_video_path)) if broll_video_path else None
        try:
            for index, plan in enumerate(shorts_plan, start=1):
                clip_start = max(0.0, float(plan.get("start", 0) or 0))
                clip_end = min(float(main_clip.duration or 0), float(plan.get("end", clip_start + 35) or clip_start + 35))
                if clip_end <= clip_start:
                    continue

                performance_clip = main_clip.subclip(clip_start, clip_end)
                output_name = SHORTS_OUTPUT_DIR / f"ai_short_{index}_{uuid.uuid4().hex[:8]}.mp4"

                if layout_mode == "Solo Mode":
                    video_layer = _fit_vertical_clip(performance_clip, canvas_width, canvas_height)
                else:
                    if broll_clip is None:
                        raise ValueError("Duet Mode requires a B-Roll / Reference Video upload.")
                    broll_start = min(clip_start, max(float(broll_clip.duration or 0) - 0.1, 0))
                    broll_end = min(broll_start + performance_clip.duration, float(broll_clip.duration or 0))
                    if broll_end <= broll_start:
                        raise ValueError("The B-Roll / Reference Video is too short for this selected cut.")
                    duet_clip = broll_clip.subclip(broll_start, broll_end)
                    top = duet_clip.resize(width=canvas_width).crop(width=canvas_width, height=canvas_height // 2)
                    bottom = performance_clip.resize(width=canvas_width).crop(width=canvas_width, height=canvas_height // 2)
                    base = ColorClip((canvas_width, canvas_height), color=(10, 15, 29), duration=performance_clip.duration)
                    video_layer = CompositeVideoClip(
                        [base, top.set_position((0, 0)), bottom.set_position((0, canvas_height // 2))],
                        size=(canvas_width, canvas_height),
                    )

                raw_lines = plan.get("caption_lines") or [plan.get("hook", "")]
                caption_lines = [str(line).strip() for line in raw_lines if str(line).strip()]
                if not caption_lines:
                    caption_lines = ["Wait for this moment"]

                caption_clips = []
                style_kwargs = _caption_style_kwargs(add_outline, text_color, font_name)
                line_duration = max(performance_clip.duration / max(len(caption_lines), 1), 1.0)
                for caption_index, caption in enumerate(caption_lines):
                    start = min(caption_index * line_duration, max(performance_clip.duration - 0.5, 0))
                    duration = min(line_duration + 0.25, max(performance_clip.duration - start, 0.5))
                    text_clip = (
                        TextClip(caption, **style_kwargs)
                        .set_start(start)
                        .set_duration(duration)
                        .set_position(("center", canvas_height - 420))
                    )
                    caption_clips.append(text_clip)

                final_clip = CompositeVideoClip([video_layer, *caption_clips], size=(canvas_width, canvas_height))
                final_clip = final_clip.set_audio(performance_clip.audio)
                final_clip.write_videofile(
                    str(output_name),
                    fps=30,
                    codec="libx264",
                    audio_codec="aac",
                    logger=None,
                )
                outputs.append(output_name)
                final_clip.close()
        finally:
            if broll_clip is not None:
                broll_clip.close()

    return outputs
