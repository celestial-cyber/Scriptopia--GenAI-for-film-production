import json
import os
import re
from typing import Optional

import requests


GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"


def _post_groq(messages, timeout: int = 30, temperature: float = 0.2) -> Optional[dict]:
    api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("LLM_API_KEY")
    if not api_key:
        return None

    api_url = os.environ.get("GROQ_API_URL", GROQ_CHAT_COMPLETIONS_URL)
    model = os.environ.get("GROQ_MODEL", DEFAULT_GROQ_MODEL)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model,
        "temperature": temperature,
        "messages": messages,
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
        if response.status_code != 200:
            print(f"[LLM CLIENT] Groq request failed: {response.status_code} {response.text}")
            return None
        return response.json()
    except Exception as exc:
        print(f"[LLM CLIENT] Groq request error: {exc}")
        return None


def _extract_json_object(text: str) -> Optional[dict]:
    if not text:
        return None
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None

    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _extract_content(raw: dict) -> Optional[str]:
    try:
        content = raw["choices"][0]["message"]["content"]
    except Exception:
        return None
    if isinstance(content, str) and content.strip():
        return content.strip()
    return None


def request_intent_from_llm(prompt: str, timeout: int = 30) -> Optional[dict]:
    """Return a structured video intent using Groq, or None on failure."""
    if not prompt:
        return None

    system_prompt = (
        "You convert user video-style prompts into JSON only. "
        "Return an object with keys: style, pace, fps, step, target_duration, mood, "
        "color_grade, transitions, narration, explanation. "
        "Use null for unknown values, keep fps and step as integers."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    raw = _post_groq(messages=messages, timeout=timeout, temperature=0.1)
    if not raw:
        return None

    content = _extract_content(raw)
    if not content:
        return None

    parsed = _extract_json_object(content)
    if not isinstance(parsed, dict):
        return None

    return parsed.get("intent") if isinstance(parsed.get("intent"), dict) else parsed


def request_text_from_llm(prompt: str, timeout: int = 30) -> Optional[str]:
    """Return plain assistant text from Groq for a user prompt."""
    if not prompt:
        return None

    messages = [
        {"role": "system", "content": "You are a concise, practical assistant."},
        {"role": "user", "content": prompt},
    ]
    raw = _post_groq(messages=messages, timeout=timeout, temperature=0.5)
    if not raw:
        return None

    return _extract_content(raw)


def request_preproduction_from_llm(prompt: str, intent: Optional[dict] = None, timeout: int = 45) -> Optional[dict]:
    """Return full preproduction plan JSON from Groq, or None on failure."""
    if not prompt:
        return None

    intent_json = json.dumps(intent or {}, ensure_ascii=True)
    system_prompt = (
        "You are a film preproduction planner. Return JSON only with keys: "
        "screenplay, workflow, characters, sound_design. "
        "screenplay must include title and scenes[] where each scene has id, description, rough_duration_s. "
        "workflow must include style, pace, total_steps, steps[] with phase, name, priority, notes. "
        "characters must include count, primary_mood, characters[] with role, mood, screen_time_pct, lighting. "
        "sound_design must include track_count, style, has_narration, tracks[] with name, type, intensity, volume_db."
    )
    user_prompt = (
        f"User creative prompt: {prompt}\n"
        f"Structured intent: {intent_json}\n"
        "Respond with valid JSON only."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    raw = _post_groq(messages=messages, timeout=timeout, temperature=0.3)
    if not raw:
        return None

    content = _extract_content(raw)
    if not content:
        return None

    parsed = _extract_json_object(content)
    if not isinstance(parsed, dict):
        return None
    required = {"screenplay", "workflow", "characters", "sound_design"}
    if not required.issubset(parsed.keys()):
        return None
    return parsed
