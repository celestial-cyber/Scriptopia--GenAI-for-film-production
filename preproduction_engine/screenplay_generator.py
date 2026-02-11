def generate_screenplay(prompt: str, intent: dict = None):
    """Generate a simple screenplay structure from a prompt and intent.

    This is deterministic and lightweight - intended as a preproduction stub.
    """
    title = prompt.strip()[:60] if prompt else "Untitled"
    scenes = []

    # Create a few scenes based on intent.target_duration or default count
    scene_count = 3
    if intent and intent.get("target_duration"):
        dur = intent.get("target_duration")
        # Make roughly one scene per 10 seconds (clamped).
        scene_count = max(1, min(8, dur // 10))

    for i in range(int(scene_count)):
        scenes.append(
            {
                "id": i + 1,
                "description": f"Scene {i + 1}: visual focus inspired by '{(prompt or '')[:40]}'",
                "rough_duration_s": int(
                    (intent.get("target_duration") // scene_count)
                    if intent and intent.get("target_duration")
                    else 5
                ),
            }
        )

    return {"title": title, "scenes": scenes}
