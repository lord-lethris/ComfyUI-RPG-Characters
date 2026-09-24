"""Model-independent render intent definitions for Character Gen 3.

Render intent deliberately lives outside Character DNA. DNA answers "who is
this character?"; render intent answers "what should the generator show?".
Model-specific prompt adapters can consume this semantic contract later.
"""

RENDER_INTENT_VERSION = 2

CHARACTER_PORTRAIT_INTENT = {
    "id": "character_portrait",
    "label": "Character Portrait",
    "description": (
        "A character-sheet portrait focused on the head, face and upper torso."
    ),
    "composition": {
        "framing": "head_and_shoulders",
        "crop": "upper_chest",
        "subject_scale": "large_in_frame",
        "camera": "front_or_three_quarter",
        "subject_count": 1,
        "primary_subject": "face",
    },
    "visibility": {
        "face": "clear",
        "required_regions": [
            "head",
            "face",
            "neck",
            "shoulders",
            "upper_chest",
        ],
        "excluded_regions": [
            "lower_body",
            "legs",
            "knees",
            "feet",
            "full_body",
        ],
    },
    "background": "simple_neutral",
    "character_constraints": {
        "facial_hair": "none",
    },
}

RENDER_INTENTS = {
    CHARACTER_PORTRAIT_INTENT["id"]: CHARACTER_PORTRAIT_INTENT,
}


def get_render_intent(intent_id):
    """Return a copy of a known render intent or raise a useful error."""
    try:
        return dict(RENDER_INTENTS[intent_id])
    except KeyError as exc:
        raise ValueError(f"Unknown render intent: {intent_id}") from exc


def make_render_intent(intent_id="character_portrait"):
    """Create a JSON-safe render intent document."""
    intent = get_render_intent(intent_id)
    return {
        "render_intent_version": RENDER_INTENT_VERSION,
        "type": "RPG_CHARACTER_RENDER_INTENT",
        **intent,
    }
