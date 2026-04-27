from __future__ import annotations

import textwrap
import requests
from typing import Iterable

from .llm_client import get_llm_client, is_custom_api, get_model_name


def get_system_prompt(vault_settings: dict[str, str]) -> str:
    channel_name = vault_settings.get("CHANNEL_NAME", "Ralskies")
    niche = vault_settings.get("NICHE", "Theatrical covers like Epic the Musical and Hazbin Hotel, plus dreamy original songs")
    target_audience = vault_settings.get("TARGET_AUDIENCE", "Fanskies")
    tone = vault_settings.get("TONE", "Emotional, dramatic, reimagined, and story-driven.")
    
    return (
        f"You are A.R.I.A. (Algorithmic Retention & Intelligence Assistant), the private AI strategy coach "
        f"for the YouTube channel '{channel_name}'. {channel_name} specializes in {niche}. "
        f"The community/target audience is called '{target_audience}'. Your job is to analyze retention and concept strength, "
        f"brainstorm high-retention video ideas, write SEO-optimized metadata, and help identify fan requests "
        f"from comments or request dumps. Be encouraging but highly strategic. Respect the creator's workflow. "
        f"When suggesting titles or concepts, lean into the following tone: {tone}"
    )


RESPONSE_STYLE_INSTRUCTIONS = {
    "Concise": "Keep answers brief and easy to scan. Prefer 3-5 short bullets or one short paragraph. Do not provide detailed reasoning unless the user asks for depth.",
    "Standard": "Keep answers clear and practical. Give enough reasoning to support the recommendation, but avoid long essays unless needed.",
    "Deep": "Give fuller strategic reasoning, more context, and a more detailed breakdown when useful.",
}


def stream_aria_response(
    prompt: str,
    model: str,
    response_style: str = "Concise",
    pattern_snapshot: dict[str, object] | None = None,
    upload_takeaways: dict[str, object] | None = None,
) -> Iterable[str]:
    try:
        from storage import load_vault_settings
        vault_settings = load_vault_settings()
        base_system_prompt = get_system_prompt(vault_settings)
        system_prompt = (
            f"{base_system_prompt} "
            f"{RESPONSE_STYLE_INSTRUCTIONS.get(response_style, RESPONSE_STYLE_INSTRUCTIONS['Concise'])}"
        )
        if pattern_snapshot:
            system_prompt = f"{system_prompt}\n\n{build_pattern_memory_context(pattern_snapshot)}"
        if upload_takeaways:
            system_prompt = f"{system_prompt}\n\n{build_upload_history_context(upload_takeaways)}"
        
        client = get_llm_client()
        url_str = str(client.base_url)
        if is_custom_api(url_str):
            # The custom API endpoint is exactly the URL provided in MODEL_ENDPOINT
            target_url = url_str.rstrip("/") 
            response = requests.post(
                target_url,
                json={
                    "model": get_model_name(),
                    "system_prompt": system_prompt,
                    "input": prompt,
                },
                timeout=60,
            )
            response.raise_for_status()
            payload = response.json()
            # If the custom API returns a direct string or a dict with 'response' key
            content = payload.get("response") or payload.get("content") or str(payload)
            yield str(content)
            return

        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
    except Exception as error:  # pragma: no cover
        yield f"Local model request failed: {error}"


def build_pattern_memory_context(pattern_snapshot: dict[str, object]) -> str:
    if not pattern_snapshot:
        return ""

    publish_memory = pattern_snapshot.get("publish_memory", {})
    title_patterns = pattern_snapshot.get("title_patterns", [])
    repeat_more = pattern_snapshot.get("repeat_more", [])
    reduce_or_fix = pattern_snapshot.get("reduce_or_fix", [])

    title_pattern_line = ", ".join(str(item.get("pattern", "")) for item in title_patterns[:4] if item.get("pattern")) or "none yet"
    repeat_line = " | ".join(str(item) for item in repeat_more[:3]) or "none yet"
    reduce_line = " | ".join(str(item) for item in reduce_or_fix[:3]) or "none yet"

    return textwrap.dedent(
        f"""
        Local Pattern Memory:
        - Best weekday to push strong uploads: {publish_memory.get('best_day', 'unknown')} (score: {publish_memory.get('best_score', 'n/a')})
        - Weakest weekday: {publish_memory.get('weak_day', 'unknown')} (score: {publish_memory.get('weak_score', 'n/a')})
        - Repeated title patterns: {title_pattern_line}
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
    from storage import load_vault_settings
    vault_settings = load_vault_settings()
    channel_name = vault_settings.get("CHANNEL_NAME", "Ralskies")
    target_audience = vault_settings.get("TARGET_AUDIENCE", "Fanskies")
    tone = vault_settings.get("TONE", "Emotional, dramatic, reimagined, and story-driven.")

    prompts = {
        "title_pack": f"""
        Generate 5 high-retention YouTube titles for {channel_name}.
        Lean into the following tone: {tone}
        Include a one-line angle note under each title.

        Topic: {topic}
        Working title: {working_title}
        """,
        "description_tags": f"""
        Create a YouTube-optimized description and a comma-separated list of SEO tags for {channel_name}.
        Favor discoverability, artist branding, and phrasing that aligns with: {tone}
        Keep the result clean and skimmable.

        Topic context: {topic}
        Working title: {working_title}
        """,
        "hook_pack": f"""
        Generate 10 opening hooks for a {channel_name} video.
        Make them sound natural, magnetically engaging, and aligned with: {tone}

        Topic: {topic}
        Working title: {working_title}
        """,
        "content_brief": f"""
        Build a practical YouTube content brief for a {channel_name} upload.
        Include target viewer, emotional promise, thumbnail concept, performance angle, outline, and call to action for {target_audience}.

        Topic: {topic}
        Working title: {working_title}
        """,
        "fan_request_spin": f"""
        A fan requested this idea for {channel_name}.
        Suggest a unique spin that aligns with the channel's tone: {tone}
        Include:
        1. Core reinterpretation angle
        2. Performance or visual direction
        3. Thumbnail and title framing
        4. Why {target_audience} would respond

        Request or idea: {topic}
        Working title: {working_title}
        """,
    }
    return textwrap.dedent(prompts[action]).strip()
