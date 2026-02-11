from .screenplay_generator import generate_screenplay
from .workflow_planner import plan_workflow
from .character_builder import build_characters
from .sound_design_planner import plan_sound


def run_preproduction(prompt: str, intent: dict = None, use_llm: bool = False):
    """Run full preproduction pipeline with optional Groq enhancement."""
    if intent is None:
        intent = {}

    if use_llm:
        try:
            from core.llm_client import request_preproduction_from_llm
        except Exception:
            request_preproduction_from_llm = None

        if request_preproduction_from_llm is not None:
            remote = request_preproduction_from_llm(prompt, intent=intent)
            if isinstance(remote, dict):
                remote["prompt"] = prompt
                return remote

    result = {
        "prompt": prompt,
        "screenplay": generate_screenplay(prompt, intent),
        "workflow": plan_workflow(intent),
        "characters": build_characters(intent),
        "sound_design": plan_sound(intent),
    }

    return result
