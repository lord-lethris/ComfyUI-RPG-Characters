"""Model-independent Character DNA prompt builder.

The builder consumes only Character DNA. It does not import the legacy RPG
character data tables and does not mutate the DNA document.

Source prompt mappings live on each locus so downstream prompt consumers can
operate independently of the source data implementation.
"""

import re

from ..dna.dna_schema import DNA_SECTIONS


VARIANT_PATTERN = re.compile(r"\{([^{}]+)\}")


class RPGCharacterDNAPromptBuilder:
    """Render Character DNA into generic positive and negative prompts."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "CHARACTER_INFO": ("CHARACTER_INFO",),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("POSITIVE_PROMPT", "NEGATIVE_PROMPT")
    FUNCTION = "build"
    CATEGORY = "RPG/Gen 3/Prompt"
    DESCRIPTION = (
        "Builds model-independent positive and negative prompts from "
        "Character DNA without modifying the DNA."
    )

    def build(self, CHARACTER_INFO):
        if not isinstance(CHARACTER_INFO, dict):
            return ("", "")

        sections = CHARACTER_INFO.get("sections", {})
        if not isinstance(sections, dict):
            return ("", "")

        positive_parts = []
        negative_parts = []

        for section_id in DNA_SECTIONS:
            section = sections.get(section_id)
            if not isinstance(section, dict):
                continue

            for locus in section.get("loci", []):
                if not isinstance(locus, dict):
                    continue

                selected = locus.get("selected")
                if not selected:
                    continue

                positive = self._resolve_locus_prompt(locus, selected)
                negative = self._resolve_locus_negative_prompt(locus, selected)

                if positive:
                    positive_parts.append(positive)
                if negative:
                    negative_parts.append(negative)

        return (
            self._join_parts(positive_parts),
            self._join_parts(negative_parts),
        )

    @classmethod
    def _resolve_locus_prompt(cls, locus, selected):
        option_prompts = locus.get("option_prompts", {})
        prompt = option_prompts.get(selected, "") if isinstance(option_prompts, dict) else ""

        if not prompt:
            prompt = str(selected)

        return cls._resolve_variants(prompt, locus.get("variant_sets", []))

    @classmethod
    def _resolve_locus_negative_prompt(cls, locus, selected):
        negative_prompts = locus.get("option_negative_prompts", {})
        if not isinstance(negative_prompts, dict):
            return ""
        return str(negative_prompts.get(selected, "") or "").strip()

    @staticmethod
    def _resolve_variants(prompt, variant_sets):
        if not prompt:
            return ""

        if not isinstance(variant_sets, list):
            variant_sets = []

        index = 0

        def replace(match):
            nonlocal index

            if index >= len(variant_sets):
                index += 1
                return match.group(0)

            variant = variant_sets[index]
            index += 1

            if not isinstance(variant, dict):
                return match.group(0)

            selected = variant.get("selected")
            if selected:
                return str(selected)

            options = variant.get("options", [])
            if isinstance(options, list) and options:
                return str(options[0])

            return match.group(0)

        return VARIANT_PATTERN.sub(replace, str(prompt)).strip()

    @staticmethod
    def _join_parts(parts):
        cleaned = []
        seen = set()

        for part in parts:
            value = " ".join(str(part).split()).strip()
            if not value:
                continue

            if value in seen:
                continue

            seen.add(value)
            cleaned.append(value)

        return ", ".join(cleaned)


NODE_CLASS_MAPPINGS = {
    "RPGCharacterDNAPromptBuilder": RPGCharacterDNAPromptBuilder,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGCharacterDNAPromptBuilder": "DNA Prompt Builder (Gen 3)",
}
