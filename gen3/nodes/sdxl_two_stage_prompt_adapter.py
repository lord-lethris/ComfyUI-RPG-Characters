"""Gen 3 SDXL prompt adapter for the one-prompt/two-step workflow.

The sampler intentionally uses ONE positive and ONE negative conditioning
through both sampling passes. This adapter therefore builds one complete SDXL
prompt containing:

- Character identity and phenotype.
- Presentation/render intent.
- Art style.
- Requested scene as environmental context.

The sampler decides how that prompt is sampled; this adapter decides what the
image should contain. Character DNA itself is never modified.
"""

from .model_prompt_adapter import RPGCharacterModelPromptAdapter


class RPGCharacterSDXLTwoStagePromptAdapter:
    """Build the single SDXL conditioning pair used by the two-step sampler."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "CHARACTER_INFO": ("CHARACTER_INFO",),
                "RENDER_INTENT": ("RENDER_INTENT",),
                "ART_STYLE": ("ART_STYLE",),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("POSITIVE_PROMPT", "NEGATIVE_PROMPT")
    FUNCTION = "build"
    CATEGORY = "RPG/Gen 3/Prompt"
    DESCRIPTION = (
        "Build one complete SDXL prompt for the Gen 3 two-step sampler. "
        "Character and scene stay together; the sampler reuses this prompt."
    )

    def build(self, CHARACTER_INFO, RENDER_INTENT, ART_STYLE):
        return RPGCharacterModelPromptAdapter().build(
            CHARACTER_INFO,
            RENDER_INTENT,
            ART_STYLE,
            "SDXL",
        )


NODE_CLASS_MAPPINGS = {
    "RPGCharacterSDXLTwoStagePromptAdapter":
        RPGCharacterSDXLTwoStagePromptAdapter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGCharacterSDXLTwoStagePromptAdapter":
        "SDXL Two-Step Prompt Adapter (Gen 3)",
}
