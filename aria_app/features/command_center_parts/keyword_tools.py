from __future__ import annotations

import re

import pandas as pd

def extract_keyword_candidates(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9']+", text.lower())
    stop_words = {
        "the", "and", "for", "with", "that", "this", "from", "your", "into", "then", "than",
        "male", "version", "cover", "song", "video", "a", "an", "of", "to", "in", "on", "or",
    }
    filtered = [word for word in words if len(word) > 2 and word not in stop_words]
    unique_words = list(dict.fromkeys(filtered))
    phrases: list[str] = []
    for size in (2, 3):
        for index in range(len(filtered) - size + 1):
            phrase = " ".join(filtered[index : index + size])
            if phrase not in phrases:
                phrases.append(phrase)
    return unique_words[:8] + phrases[:8]


def build_keyword_opportunity_df(topic: str, working_title: str, calendar_df: pd.DataFrame) -> pd.DataFrame:
    source_text = f"{topic} {working_title}".strip()
    if not source_text:
        return pd.DataFrame(columns=["keyword", "demand", "competition", "channel_fit", "score"])
    candidates = extract_keyword_candidates(source_text)
    channel_context = " ".join(calendar_df["content_pillar"].fillna("").astype(str).tolist()).lower()
    notes_context = " ".join(calendar_df["notes"].fillna("").astype(str).tolist()).lower()
    rows: list[dict[str, object]] = []
    for candidate in candidates:
        word_count = len(candidate.split())
        candidate_lower = candidate.lower()
        demand = min(10, 5 + word_count + (2 if any(term in candidate_lower for term in ["broadway", "hazbin", "epic", "disney"]) else 0))
        competition = max(1, 10 - word_count * 2 - (2 if "male version" in source_text.lower() or "reimagined" in source_text.lower() else 0))
        fit = 4
        if candidate_lower in channel_context:
            fit += 3
        if candidate_lower in notes_context:
            fit += 2
        if any(term in candidate_lower for term in ["theatrical", "ballad", "dreamy", "broadway", "male", "reimagined"]):
            fit += 2
        fit = min(10, fit)
        score = round(demand * 0.35 + (11 - competition) * 0.25 + fit * 0.4, 1)
        rows.append({"keyword": candidate, "demand": demand, "competition": competition, "channel_fit": fit, "score": score})
    frame = pd.DataFrame(rows).drop_duplicates(subset=["keyword"]).sort_values(["score", "channel_fit"], ascending=False)
    return frame.head(10).reset_index(drop=True)


def build_title_scorecard(title: str, topic: str) -> list[tuple[str, str]]:
    if not title.strip():
        return [("Title Score", "Add a working title to score packaging strength")]
    lowered_title = title.lower()
    title_length = len(title.strip())
    contains_keyword = any(keyword in lowered_title for keyword in extract_keyword_candidates(topic)[:5]) if topic.strip() else False
    emotional_language = any(term in lowered_title for term in ["male version", "reimagined", "broadway", "emotional", "ballad", "dramatic", "live"])
    concise = 35 <= title_length <= 70
    score = 0
    score += 3 if concise else 1
    score += 3 if contains_keyword else 1
    score += 3 if emotional_language else 1
    score += 1 if any(symbol in title for symbol in ["(", ")", "|", ":"]) else 0
    return [
        ("Packaging Score", f"{score}/10"),
        ("Length", "Strong" if concise else f"{title_length} chars"),
        ("Primary Keyword", "Present" if contains_keyword else "Weak"),
        ("Emotion / Framing", "Strong" if emotional_language else "Needs a hook"),
    ]
