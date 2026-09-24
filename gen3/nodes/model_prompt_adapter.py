"""Gen 3 model-specific prompt adapter.

Character DNA, Render Intent and Art Style remain model-independent inputs.
This node translates those semantic inputs into prompt text appropriate for
the selected image model family.

The adapter deliberately does not modify Character DNA.
"""

from .dna_prompt_builder import RPGCharacterDNAPromptBuilder


MODEL_ADAPTERS = (
    "Generic",
    "FLUX",
    "SDXL",
    "Z-Image Turbo",
    "Krea 2",
)


class RPGCharacterModelPromptAdapter:
    """Translate Gen 3 semantic character presentation into model prompts."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "CHARACTER_INFO": ("CHARACTER_INFO",),
                "RENDER_INTENT": ("RENDER_INTENT",),
                "ART_STYLE": ("ART_STYLE",),
                "model": (list(MODEL_ADAPTERS),),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("POSITIVE_PROMPT", "NEGATIVE_PROMPT")
    FUNCTION = "build"
    CATEGORY = "RPG/Gen 3/Prompt"
    DESCRIPTION = (
        "Translate Character DNA, Render Intent and Art Style into a "
        "model-specific prompt without modifying Character DNA."
    )

    def build(self, CHARACTER_INFO, RENDER_INTENT, ART_STYLE, model):
        character_positive, character_negative = (
            RPGCharacterDNAPromptBuilder().build(CHARACTER_INFO)
        )
        render_positive, render_negative = (
            RPGCharacterDNAPromptBuilder._render_intent(RENDER_INTENT)
        )

        style_positive = ""
        style_negative = ""
        if isinstance(ART_STYLE, dict):
            style_positive = str(ART_STYLE.get("positive_prompt", "") or "").strip()
            style_negative = str(ART_STYLE.get("negative_prompt", "") or "").strip()

        positive, negative = self._adapt(
            model,
            character_positive,
            character_negative,
            render_positive,
            render_negative,
            style_positive,
            style_negative,
        )
        return positive, negative

    @classmethod
    def _adapt(
        cls,
        model,
        character_positive,
        character_negative,
        render_positive,
        render_negative,
        style_positive,
        style_negative,
    ):
        if model == "FLUX":
            return cls._flux(
                character_positive,
                character_negative,
                render_positive,
                render_negative,
                style_positive,
                style_negative,
            )

        if model == "SDXL":
            return cls._sdxl(
                character_positive,
                character_negative,
                render_positive,
                render_negative,
                style_positive,
                style_negative,
            )

        if model == "Z-Image Turbo":
            return cls._z_image(
                character_positive,
                character_negative,
                render_positive,
                render_negative,
                style_positive,
                style_negative,
            )

        if model == "Krea 2":
            return cls._krea2(
                character_positive,
                character_negative,
                render_positive,
                render_negative,
                style_positive,
                style_negative,
            )

        return cls._generic(
            character_positive,
            character_negative,
            render_positive,
            render_negative,
            style_positive,
            style_negative,
        )

    @staticmethod
    def _generic(character, character_negative, render, render_negative, style, style_negative):
        return (
            RPGCharacterModelPromptAdapter._join(character, render, style),
            RPGCharacterModelPromptAdapter._join(character_negative, render_negative, style_negative),
        )

    @staticmethod
    def _flux(character, character_negative, render, render_negative, style, style_negative):
        # FLUX is natural-language-first and does not use a traditional
        # negative-prompt channel.  Do not fold negative vocabulary into the
        # positive prompt: words such as "beard" or "boots" can become visual
        # concepts instead of exclusions.  The positive DNA/Render Intent
        # already contains the desired anatomical and presentation states.
        return (
            RPGCharacterModelPromptAdapter._join(
                character,
                render,
                style,
                "The character's defining facial and anatomical features remain clear and unobstructed.",
            ),
            "",
        )

    @staticmethod
    def _sdxl(character, character_negative, render, render_negative, style, style_negative):
        # SDXL workflows commonly use explicit positive/negative prompt
        # channels, so preserve that separation.  Apply restrained emphasis
        # only to hard presentation constraints rather than every token.
        render = RPGCharacterModelPromptAdapter._emphasize_sdxl(
            render,
            (
                ("close-up head-and-shoulders", 1.25),
                ("face is the primary subject", 1.20),
                ("completely clean-shaven face", 1.30),
            ),
        )
        return (
            RPGCharacterModelPromptAdapter._join(style, character, render),
            RPGCharacterModelPromptAdapter._join(
                character_negative,
                render_negative,
                style_negative,
            ),
        )

    @staticmethod
    def _z_image(character, character_negative, render, render_negative, style, style_negative):
        # Z-Image Turbo benefits from explicit positive constraints.  Fold the
        # negative channels into a final "without" clause instead of depending
        # on a separate negative input.
        exclusions = RPGCharacterModelPromptAdapter._join(
            character_negative,
            render_negative,
            style_negative,
        )
        constraint = (
            f"The image contains none of the following: {exclusions}."
            if exclusions
            else ""
        )
        return (
            RPGCharacterModelPromptAdapter._join(
                character,
                render,
                style,
                constraint,
            ),
            "",
        )

    @staticmethod
    def _krea2(character, character_negative, render, render_negative, style, style_negative):
        # Krea 2 here targets the everyday Turbo workflow.  Treat it as
        # positive-prompt-only rather than preserving a negative channel.
        # As with FLUX, do not inject negative vocabulary into the positive
        # prompt; the semantic positive character/render descriptions already
        # express the intended result.
        return (
            RPGCharacterModelPromptAdapter._join(
                character,
                render,
                style,
            ),
            "",
        )

    @staticmethod
    def _emphasize_sdxl(text, replacements):
        value = text
        for phrase, weight in replacements:
            if phrase in value:
                value = value.replace(
                    phrase,
                    f"({phrase}:{weight:.2f})",
                    1,
                )
        return value

    @staticmethod
    def _join(*parts):
        cleaned = []
        seen = set()
        for part in parts:
            value = " ".join(str(part or "").split()).strip()
            if not value or value in seen:
                continue
            seen.add(value)
            cleaned.append(value)
        return ", ".join(cleaned)


NODE_CLASS_MAPPINGS = {
    "RPGCharacterModelPromptAdapter": RPGCharacterModelPromptAdapter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGCharacterModelPromptAdapter": "Model Prompt Adapter (Gen 3)",
}
