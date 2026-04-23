from __future__ import annotations

import textwrap
from typing import Iterable

import ollama


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

RESPONSE_STYLE_INSTRUCTIONS = {
    "Concise": "Keep answers brief and easy to scan. Prefer 3-5 short bullets or one short paragraph. Do not provide detailed reasoning unless the user asks for depth.",
    "Standard": "Keep answers clear and practical. Give enough reasoning to support the recommendation, but avoid long essays unless needed.",
    "Deep": "Give fuller strategic reasoning, more context, and a more detailed breakdown when useful.",
}


def stream_ollama_response(
    prompt: str,
    model: str,
    response_style: str = "Concise",
    pattern_snapshot: dict[str, object] | None = None,
    upload_takeaways: dict[str, object] | None = None,
) -> Iterable[str]:
    try:
        system_prompt = (
            f"{ARIA_SYSTEM_PROMPT} "
            f"{RESPONSE_STYLE_INSTRUCTIONS.get(response_style, RESPONSE_STYLE_INSTRUCTIONS['Concise'])}"
        )
        if pattern_snapshot:
            system_prompt = f"{system_prompt}\n\n{build_pattern_memory_context(pattern_snapshot)}"
        if upload_takeaways:
            system_prompt = f"{system_prompt}\n\n{build_upload_history_context(upload_takeaways)}"
        stream = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
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


def build_pattern_memory_context(pattern_snapshot: dict[str, object]) -> str:
    if not pattern_snapshot:
        return ""

    publish_memory = pattern_snapshot.get("publish_memory", {})
    stage_memory = pattern_snapshot.get("stage_memory", {})
    title_patterns = pattern_snapshot.get("title_patterns", [])
    pillar_memory = pattern_snapshot.get("pillar_memory", [])
    repeat_more = pattern_snapshot.get("repeat_more", [])
    reduce_or_fix = pattern_snapshot.get("reduce_or_fix", [])

    title_pattern_line = ", ".join(str(item.get("pattern", "")) for item in title_patterns[:4] if item.get("pattern")) or "none yet"
    pillar_line = ", ".join(str(item.get("pillar", "")) for item in pillar_memory[:4] if item.get("pillar")) or "none yet"
    repeat_line = " | ".join(str(item) for item in repeat_more[:3]) or "none yet"
    reduce_line = " | ".join(str(item) for item in reduce_or_fix[:3]) or "none yet"

    return textwrap.dedent(
        f"""
        Local Pattern Memory:
        - Best weekday to push strong uploads: {publish_memory.get('best_day', 'unknown')} (score: {publish_memory.get('best_score', 'n/a')})
        - Weakest weekday: {publish_memory.get('weak_day', 'unknown')} (score: {publish_memory.get('weak_score', 'n/a')})
        - Current production bottleneck: {stage_memory.get('bottleneck_stage', 'unknown')} with {stage_memory.get('bottleneck_count', 0)} item(s)
        - Overdue repertoire items: {stage_memory.get('overdue_count', 0)}
        - Repeated title patterns: {title_pattern_line}
        - Active content pillars: {pillar_line}
        - Repeat more often: {repeat_line}
        - Reduce or fix: {reduce_line}
        Use this local memory to make recommendations more tailored and less generic.
        """
    ).strip()


def build_upload_history_context(upload_takeaways: dict[str, object]) -> str:
    best = upload_takeaways.get("best")
    weak = upload_takeaways.get("weak")
    pattern_rows = upload_takeaways.get("pattern_rows", [])
    improvement_rows = upload_takeaways.get("improvement_rows", [])
    if best is None and weak is None:
        return ""

    pattern_line = " | ".join(f"{label}: {value}" for label, value in pattern_rows[:3]) or "none yet"
    improvement_line = " | ".join(f"{label}: {value}" for label, value in improvement_rows[:3]) or "none yet"

    best_line = "No best-upload summary yet."
    weak_line = "No weak-upload summary yet."
    if best is not None:
        best_line = (
            f"Best upload: {best.get('title', 'Unknown')} | views {best.get('views', 'n/a')} | "
            f"retention {best.get('retention', 'n/a')} | score {best.get('engagement_score', 'n/a')}"
        )
    if weak is not None:
        weak_line = (
            f"Weakest upload: {weak.get('title', 'Unknown')} | views {weak.get('views', 'n/a')} | "
            f"retention {weak.get('retention', 'n/a')} | score {weak.get('engagement_score', 'n/a')}"
        )

    return textwrap.dedent(
        f"""
        Local Upload History Summary:
        - {best_line}
        - {weak_line}
        - What seems to work: {pattern_line}
        - What needs improvement: {improvement_line}
        When suggesting new ideas, packaging, or analysis, prefer patterns closer to the stronger uploads.
        """
    ).strip()


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
