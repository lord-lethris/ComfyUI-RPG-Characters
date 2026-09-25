"""Gen 3 SDXL two-stage prompt adapter.

Splits the same model-independent Character DNA into two SDXL conditioning
passes:
1. Character establishment: identity, phenotype, anatomy and render framing.
2. Style/scene reinterpretation: a compact character reminder plus Art Style,
   Scene and presentation cues.

Character DNA itself is never modified.
"""

from .dna_prompt_builder import RPGCharacterDNAPromptBuilder
from .model_prompt_adapter import RPGCharacterModelPromptAdapter


class RPGCharacterSDXLTwoStagePromptAdapter:
    """Build the four conditioning strings used by the Gen 3 SDXL sampler."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "CHARACTER_INFO": ("CHARACTER_INFO",),
                "RENDER_INTENT": ("RENDER_INTENT",),
                "ART_STYLE": ("ART_STYLE",),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = (
        "POSITIVE_STAGE1",
        "NEGATIVE_STAGE1",
        "POSITIVE_STAGE2",
        "NEGATIVE_STAGE2",
    )
    FUNCTION = "build"
    CATEGORY = "RPG/Gen 3/Prompt"
    DESCRIPTION = (
        "Build SDXL two-stage prompts from model-independent Gen 3 DNA. "
        "Stage 1 establishes the character; Stage 2 adds style and scene."
    )

    def build(self, CHARACTER_INFO, RENDER_INTENT, ART_STYLE):
        character_positive, character_negative = (
            RPGCharacterDNAPromptBuilder().build(CHARACTER_INFO)
        )

        portrait_with_scene = (
            RPGCharacterModelPromptAdapter._is_head_and_shoulders(RENDER_INTENT)
            and RPGCharacterModelPromptAdapter._has_explicit_scene(CHARACTER_INFO)
        )
        if portrait_with_scene:
            character_positive = (
                RPGCharacterModelPromptAdapter._qualify_scene_prompt(
                    character_positive,
                    CHARACTER_INFO,
                )
            )

        render_positive, render_negative = (
            RPGCharacterDNAPromptBuilder._render_intent(
                RENDER_INTENT,
                suppress_neutral_background=portrait_with_scene,
            )
        )

        style_positive = ""
        style_negative = ""
        if isinstance(ART_STYLE, dict):
            style_positive = str(
                ART_STYLE.get("positive_prompt", "") or ""
            ).strip()
            style_negative = str(
                ART_STYLE.get("negative_prompt", "") or ""
            ).strip()

        race_positive, race_negative = (
            RPGCharacterModelPromptAdapter._sdxl_race_anchors(
                character_positive
            )
        )
        skin_positive, skin_negative = (
            RPGCharacterModelPromptAdapter._sdxl_skin_anchor(
                character_positive
            )
        )
        scene_positive = RPGCharacterModelPromptAdapter._sdxl_scene_anchor(
            character_positive
        )
        style_positive, style_negative = (
            RPGCharacterModelPromptAdapter._sdxl_style_anchor(
                style_positive,
                style_negative,
            )
        )

        # Character DNA is rendered once into a compact, model-specific form.
        # The scene is removed here so Stage 1 cannot accidentally establish
        # the environment as a competing subject.
        compact_character = (
            RPGCharacterModelPromptAdapter._sdxl_compact_character(
                character_positive,
                remove_infernal_skin=bool(skin_positive),
            )
        )

        stage1_positive = RPGCharacterModelPromptAdapter._join(
            compact_character,
            race_positive,
            skin_positive,
            render_positive,
        )
        stage1_negative = RPGCharacterModelPromptAdapter._join(
            character_negative,
            render_negative,
            race_negative,
            skin_negative,
        )
        stage1_negative = (
            RPGCharacterModelPromptAdapter._emphasize_sdxl_negative(
                stage1_negative,
                (
                    ("beard", 1.35),
                    ("moustache", 1.30),
                    ("mustache", 1.30),
                    ("goatee", 1.25),
                    ("stubble", 1.25),
                    ("facial hair", 1.30),
                ),
            )
        )

        # Stage 2 deliberately does not re-send the entire Render Intent or
        # Scene-free character prose as its primary instruction. It gets a
        # compact identity reminder, then the presentation information that
        # should reinterpret the already-established character.
        stage2_identity = compact_character
        stage2_positive = RPGCharacterModelPromptAdapter._join(
            style_positive,
            "the same character remains the primary subject",
            stage2_identity,
            race_positive,
            skin_positive,
            render_positive,
            scene_positive,
        )
        stage2_negative = RPGCharacterModelPromptAdapter._join(
            style_negative,
            race_negative,
            skin_negative,
            render_negative,
            character_negative,
        )
        stage2_negative = (
            RPGCharacterModelPromptAdapter._emphasize_sdxl_negative(
                stage2_negative,
                (
                    ("beard", 1.35),
                    ("moustache", 1.30),
                    ("mustache", 1.30),
                    ("goatee", 1.25),
                    ("stubble", 1.25),
                    ("facial hair", 1.30),
                ),
            )
        )

        return (
            stage1_positive,
            stage1_negative,
            stage2_positive,
            stage2_negative,
        )


NODE_CLASS_MAPPINGS = {
    "RPGCharacterSDXLTwoStagePromptAdapter":
        RPGCharacterSDXLTwoStagePromptAdapter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGCharacterSDXLTwoStagePromptAdapter":
        "SDXL Two-Stage Prompt Adapter (Gen 3)",
}
