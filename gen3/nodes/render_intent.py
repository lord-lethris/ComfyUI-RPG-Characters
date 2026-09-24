"""ComfyUI node for selecting a Gen 3 downstream render intent."""

from ..render.render_intent import RENDER_INTENTS, make_render_intent


class RPGCharacterRenderIntent:
    """Select what a downstream image generator should show."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "intent": (
                    [item["label"] for item in RENDER_INTENTS.values()],
                ),
            },
        }

    RETURN_TYPES = ("RENDER_INTENT",)
    RETURN_NAMES = ("RENDER_INTENT",)
    FUNCTION = "create"
    CATEGORY = "RPG/Gen 3/Render"
    DESCRIPTION = (
        "Select presentation intent independently from Character DNA. "
        "Render intent describes framing and presentation, not character identity."
    )

    def create(self, intent):
        intent_id = next(
            (
                item_id
                for item_id, item in RENDER_INTENTS.items()
                if item["label"] == intent
            ),
            None,
        )
        if intent_id is None:
            raise ValueError(f"Unknown render intent label: {intent}")

        return (make_render_intent(intent_id),)


NODE_CLASS_MAPPINGS = {
    "RPGCharacterRenderIntent": RPGCharacterRenderIntent,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGCharacterRenderIntent": "Character Render Intent (Gen 3)",
}
