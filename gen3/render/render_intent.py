"""Model-independent render intent definitions for Character Gen 3.

Render intent deliberately lives outside Character DNA. DNA answers "who is
this character?"; render intent answers "what should the generator show?".
Model-specific prompt adapters can consume this semantic contract later.
"""

RENDER_INTENT_VERSION = 1

CHARACTER_PORTRAIT_INTENT = {
    "id": "character_portrait",
    "label": "Character Portrait",
    "description": (
        "A character-sheet portrait focused on the head, face and upper torso."
    ),
    "framing": "head and shoulders with upper torso visible",
    "camera": "front-facing or slight three-quarter view",
    "subject": "single character",
    "face_visibility": "face clearly visible",
    "background": "simple neutral background",
    "positive_prompt": (
        "character portrait, head and shoulders, upper torso visible, "
        "single character, centered subject, face clearly visible, "
        "front-facing or slight three-quarter view, simple neutral background"
    ),
    "negative_prompt": (
        "full body, full-length character, head-to-toe framing, multiple "
        "characters, cropped face, obscured face"
    ),
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
