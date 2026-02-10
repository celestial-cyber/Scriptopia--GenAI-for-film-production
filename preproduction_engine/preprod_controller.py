from .screenplay_generator import generate_screenplay
from .workflow_planner import plan_workflow
from .character_builder import build_characters
from .sound_design_planner import plan_sound


def run_preproduction(prompt: str, intent: dict = None):
    """Run full preproduction pipeline."""
    if intent is None:
        intent = {}
    
    result = {
        "prompt": prompt,
        "screenplay": generate_screenplay(prompt, intent),
        "workflow": plan_workflow(intent),
        "characters": build_characters(intent),
        "sound_design": plan_sound(intent)
    }
    
    return result
