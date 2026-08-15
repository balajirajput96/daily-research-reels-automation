#!/usr/bin/env python3
"""Generate one source-grounded Hinglish short-video script.

The script deliberately fails when no model credential is configured. It does not
invent citations or silently fall back to unsupported medical claims.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

import requests

DISCLAIMER = (
    "This content is for general education only, not medical advice. "
    "For personal concerns, consult a qualified healthcare professional."
)


def choose_topic(path: Path, day: dt.date) -> dict[str, Any]:
    topics = json.loads(path.read_text(encoding="utf-8"))["topics"]
    if not topics:
        raise RuntimeError("Topic queue is empty")
    return topics[day.toordinal() % len(topics)]


def call_gemini(topic: dict[str, Any], model: str, api_key: str) -> dict[str, Any]:
    prompt = f"""
Create one approximately 60-second Instagram/Facebook Reel script in natural Hinglish.
Topic: {topic['topic']}
Angle: {topic['angle']}
Domain: {topic['domain']}
Authoritative starting sources: {json.dumps(topic.get('sources', []))}

Return JSON only with exactly these keys:
 title, hook, spoken_script, on_screen_lines, caption, claims, sources, confidence

Rules:
- Spoken script must be 120-150 words and easy to speak in 60 seconds.
- Use Hindi and English naturally; do not use exaggerated clickbait.
- Keep claims general and educational. Do not diagnose, prescribe medication, promise a cure,
  give an individualized diet plan, recommend unsafe restriction, or claim guaranteed outcomes.
- Do not invent studies, statistics, quotations, or source URLs.
- Every factual claim must map to one of the supplied source URLs. If the source is insufficient,
  mark the claim confidence as uncertain and phrase it cautiously.
- Add this exact disclaimer at the end of the spoken script and caption: {DISCLAIMER}
- Include 5-8 short on-screen caption lines.
- Add an explicit AI disclosure in the caption: "AI-assisted visuals/editing used; face/voice are owner-authorized."
- The claims field must be an array of objects with text, source_url, and confidence.
- The sources field must contain only supplied URLs.
""".strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    response = requests.post(
        url,
        params={"key": api_key},
        json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json"}},
        timeout=90,
    )
    response.raise_for_status()
    payload = response.json()
    try:
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Gemini returned non-JSON or incomplete output: {exc}") from exc
    required = {"title", "hook", "spoken_script", "on_screen_lines", "caption", "claims", "sources", "confidence"}
    missing = required.difference(result)
    if missing:
        raise RuntimeError(f"Generated script missing keys: {sorted(missing)}")
    return result


def validate_script(result: dict[str, Any], topic: dict[str, Any]) -> None:
    spoken = str(result["spoken_script"])
    caption = str(result["caption"])
    if not 120 <= len(spoken.split()) <= 180:
        raise RuntimeError("Spoken script is outside the safe 60-second word range")
    if DISCLAIMER not in spoken or DISCLAIMER not in caption:
        raise RuntimeError("Required medical disclaimer is missing")
    if "AI-assisted visuals/editing used" not in caption:
        raise RuntimeError("Required AI disclosure is missing")
    allowed = set(topic.get("sources", []))
    for claim in result["claims"]:
        if claim.get("source_url") not in allowed:
            raise RuntimeError("Generated claim cites a URL outside the approved source list")
    if not set(result["sources"]).issubset(allowed):
        raise RuntimeError("Generated sources contain an unapproved URL")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topics", default="config/topics.json")
    parser.add_argument("--output", default="artifacts/script.json")
    args = parser.parse_args()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("BLOCKED: GEMINI_API_KEY is not configured")
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    day = dt.date.today()
    topic = choose_topic(Path(args.topics), day)
    result = call_gemini(topic, model, api_key)
    validate_script(result, topic)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps({"date": day.isoformat(), "topic": topic, "script": result}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {args.output} for topic {topic['id']}")


if __name__ == "__main__":
    main()
