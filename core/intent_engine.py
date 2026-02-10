def interpret_intent(user_input: str):
    user_input = user_input.lower()
from typing import Optional
import re


def interpret_intent(user_input: str, defaults: Optional[dict] = None) -> dict:
    """Parse a free-text user intent into a structured dict of video requirements.

    Returns keys:
      - style, pace, fps, step
      - target_duration (seconds, optional)
      - mood, color_grade, transitions, narration (best-effort)
      - explanation: short human-readable summary

    `defaults` may provide fallback values for fps/step.
    """
    if defaults is None:
        defaults = {}

    text = (user_input or "").lower()

    intent = {
        "style": defaults.get("style", "reel"),
        "pace": defaults.get("pace", "medium"),
        "fps": defaults.get("fps", 12),
        "step": defaults.get("step", 8),
        "target_duration": None,
        "mood": None,
        "color_grade": None,
        "transitions": None,
        "narration": None,
    }

    # Style / pace shortcuts
    if "cinematic" in text:
        intent.update({"style": "cinematic", "pace": "slow", "fps": 8, "step": 12})
    elif "trailer" in text or "fast" in text or "energetic" in text:
        intent.update({"style": "trailer", "pace": "fast", "fps": 15, "step": 6})
    elif "reel" in text or "instagram" in text or "short" in text:
        intent.update({"style": "reel", "pace": "medium", "fps": 12, "step": 8})

    # FPS explicit
    m = re.search(r"(\d+)\s*fps", text)
    if m:
        try:
            intent["fps"] = int(m.group(1))
        except ValueError:
            pass

    # Target duration (e.g., 10s, 30s, 1m)
    m = re.search(r"(\d+)\s*(s|sec|secs|seconds)\b", text)
    if m:
        intent["target_duration"] = int(m.group(1))
    else:
        m = re.search(r"(\d+)\s*(m|min|mins|minutes)\b", text)
        if m:
            intent["target_duration"] = int(m.group(1)) * 60

    # Step (select every Nth frame)
    m = re.search(r"every\s+(\d+)\b", text)
    if m:
        try:
            intent["step"] = int(m.group(1))
        except ValueError:
            pass

    # Mood / color hints
    if "dramatic" in text or "intense" in text:
        intent["mood"] = "dramatic"
    if "bright" in text or "vibrant" in text:
        intent["color_grade"] = "bright"
    if "dark" in text or "moody" in text:
        intent["color_grade"] = "dark"
    if "warm" in text:
        intent["color_grade"] = "warm"
    if "cool" in text or "cold" in text:
        intent["color_grade"] = "cool"

    # Transitions and narration
    if "cut" in text and "smooth" not in text:
        intent["transitions"] = "cut"
    if "smooth" in text or "dissolve" in text or "crossfade" in text:
        intent["transitions"] = "dissolve"
    if "voice" in text or "narration" in text or "voiceover" in text:
        intent["narration"] = True

    # Build explanation
    expl_parts = [f"style={intent['style']}", f"pace={intent['pace']}", f"fps={intent['fps']}", f"step={intent['step']}"]
    if intent["target_duration"]:
        expl_parts.append(f"target_duration={intent['target_duration']}s")
    if intent["mood"]:
        expl_parts.append(f"mood={intent['mood']}")
    if intent["color_grade"]:
        expl_parts.append(f"color_grade={intent['color_grade']}")
    if intent["transitions"]:
        expl_parts.append(f"transitions={intent['transitions']}")
    if intent["narration"]:
        expl_parts.append("narration=yes")

    intent["explanation"] = ", ".join(expl_parts)

    return intent

