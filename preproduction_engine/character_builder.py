def build_characters(intent: dict):
    """Build character/subject profiles from intent."""
    characters = []
    mood = intent.get("mood", "neutral")
    style = intent.get("style", "reel")
    
    # Define primary subject archetypes based on style/mood
    if style == "cinematic":
        characters.append({"role": "protagonist", "mood": mood, "screen_time_pct": 70, "lighting": "dramatic"})
    elif style == "trailer":
        characters.append({"role": "hero", "mood": "intense", "screen_time_pct": 60, "lighting": "high-contrast"})
    else:  # reel
        characters.append({"role": "subject", "mood": "vibrant", "screen_time_pct": 80, "lighting": "bright"})
    
    # Secondary elements
    characters.append({"role": "supporting_visuals", "mood": mood, "screen_time_pct": 30, "lighting": "supporting"})
    
    return {"count": len(characters), "primary_mood": mood, "characters": characters}
