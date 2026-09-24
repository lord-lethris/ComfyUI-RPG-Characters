"""Model-independent Character DNA prompt builder.

The builder consumes only Character DNA. It does not import the legacy RPG
character data tables and does not mutate the DNA document.

Source prompt mappings live on each locus so downstream prompt consumers can
operate independently of the source data implementation.

Prompt Builder v1.1 additionally renders:
- sculpted variant weights using standard ComfyUI prompt-weight syntax
- semantic expression-control descriptors from 2D controls
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
        "Builds prompts from Character DNA without modifying the DNA. "
        "Supports selected variants, sculpted weights and expression controls."
    )

    @classmethod
    def _render_genome(cls, genome):
        if not isinstance(genome, dict):
            return "", ""

        identity = genome.get("identity", {})
        species_traits = genome.get("species_traits", {})
        phenotype = genome.get("phenotype", {})
        lineage_data = cls._lineage_snapshot(genome)
        body_plan = phenotype.get("body_plan", {})

        positive = []
        negative = []

        if lineage_data.get("prompt"):
            positive.append(lineage_data["prompt"])

        anatomy = []
        for key in ("posture", "body", "head", "limbs", "hands", "feet", "wings", "tail"):
            value = body_plan.get(key)
            if value:
                anatomy.append(str(value))

        build = body_plan.get("build")
        if anatomy:
            phrase = ", ".join(anatomy)
            if build:
                phrase += f", {build}"
            positive.append(phrase)

        # Species-specific traits are rendered as modifiers of the body plan,
        # not as a disconnected list of boolean facts.
        horn_type = species_traits.get("horn_type")
        if horn_type:
            positive.append(f"{horn_type} horns")

        wing_type = species_traits.get("wing_type")
        if wing_type and not body_plan.get("wings"):
            positive.append(f"{wing_type} wings")

        scale_pattern = species_traits.get("scale_pattern")
        if scale_pattern:
            positive.append(f"{scale_pattern} scales")

        heritage = identity.get("heritage")
        if heritage and identity.get("heritage_compatible") and phenotype.get("heritage"):
            positive.append(f"{heritage} heritage")
            positive.append(phenotype["heritage"])

        if lineage_data.get("negative_prompt"):
            negative.append(lineage_data["negative_prompt"])

        return cls._join_parts(positive), cls._join_parts(negative)

    @staticmethod
    def _lineage_snapshot(genome):
        snapshot = genome.get("lineage", {})
        return snapshot if isinstance(snapshot, dict) else {}

    def build(self, CHARACTER_INFO):
        if not isinstance(CHARACTER_INFO, dict):
            return ("", "")

        sections = CHARACTER_INFO.get("sections", {})
        if not isinstance(sections, dict):
            return ("", "")

        positive_parts = []
        negative_parts = []

        # Gen 3 lineage/genome is authoritative for biological identity.
        # Legacy Race/Ethnicity prompt strings are retained for compatibility
        # but deliberately not rendered.
        genome = CHARACTER_INFO.get("genome")
        genome_positive, genome_negative = self._render_genome(genome)
        if genome_positive:
            positive_parts.append(genome_positive)
        if genome_negative:
            negative_parts.append(genome_negative)

        for section_id in DNA_SECTIONS:
            section = sections.get(section_id)
            if not isinstance(section, dict):
                continue

            for locus in section.get("loci", []):
                if not isinstance(locus, dict):
                    continue

                locus_id = locus.get("id")
                if locus_id in {"identity:race", "identity:ethnicity"}:
                    continue

                genome = CHARACTER_INFO.get("genome") or {}
                phenotype = genome.get("phenotype", {}) if isinstance(genome, dict) else {}
                if locus_id.startswith("hair:") and not phenotype.get("hair_allowed", True):
                    continue
                if locus_id.startswith("facial_hair:") and not phenotype.get("facial_hair_allowed", True):
                    continue

                selected = locus.get("selected")
                if not selected:
                    continue

                # Facial-hair colour has no meaning when the style is
                # explicitly "No Beard".  Do not let a stale/default colour
                # selection re-introduce facial hair through its colour prompt.
                if locus_id == "facial_hair:colour":
                    facial_hair_section = sections.get("facial_hair", {})
                    style_locus = next(
                        (
                            item for item in facial_hair_section.get("loci", [])
                            if isinstance(item, dict) and item.get("id") == "facial_hair:style"
                        ),
                        None,
                    )
                    if isinstance(style_locus, dict) and style_locus.get("selected") == "No Beard":
                        continue
                if locus_id == "identity:class" and str(selected).strip().lower() == "no class":
                    continue

                positive = self._resolve_locus_prompt(locus, selected)
                positive_controls = self._resolve_locus_controls(locus)
                negative = self._resolve_locus_negative_prompt(locus, selected)

                if positive:
                    positive_parts.append(positive)
                positive_parts.extend(positive_controls)
                if negative:
                    negative_parts.append(negative)

        return (
            self._join_parts(positive_parts),
            self._join_parts(negative_parts),
        )

    @classmethod
    def _resolve_locus_prompt(cls, locus, selected):
        option_prompts = locus.get("option_prompts", {})
        prompt = (
            option_prompts.get(selected, "")
            if isinstance(option_prompts, dict)
            else ""
        )

        # "No Beard" is a state, not a piece of positive visual prose.
        # Explicitly describe the absence so image models do not infer a beard
        # from age/gender while simultaneously receiving a colour selection.
        if locus.get("id") == "facial_hair:style" and selected == "No Beard":
            return "clean-shaven face, no facial hair"

        if not prompt:
            prompt = str(selected)

        prompt = prompt.replace("(Natural Body, No Implants, No Cybernetic Enhancements, No Magical Enhancements, Pure Human/Fantasy Form)", "")
        return cls._resolve_variants(prompt, locus.get("variant_sets", []))

    @classmethod
    def _resolve_locus_negative_prompt(cls, locus, selected):
        negative_prompts = locus.get("option_negative_prompts", {})
        if not isinstance(negative_prompts, dict):
            return ""

        if locus.get("id") == "facial_hair:style" and selected == "No Beard":
            return "beard, moustache, mustache, goatee, sideburns, stubble, facial hair"

        return str(negative_prompts.get(selected, "") or "").strip()

    @classmethod
    def _resolve_variants(cls, prompt, variant_sets):
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

            mode = str(variant.get("mode", "selected") or "selected").lower()
            if mode == "sculpted":
                weighted = cls._render_sculpted_variant(variant)
                if weighted:
                    return weighted

            selected = variant.get("selected")
            if selected:
                return str(selected)

            options = variant.get("options", [])
            if isinstance(options, list) and options:
                return str(options[0])

            return match.group(0)

        return VARIANT_PATTERN.sub(replace, str(prompt)).strip()

    @staticmethod
    def _render_sculpted_variant(variant):
        options = variant.get("options", [])
        weights = variant.get("weights", {})

        if not isinstance(options, list) or not isinstance(weights, dict):
            return ""

        rendered = []
        for index, option in enumerate(options):
            raw_weight = weights.get(str(index), weights.get(index))
            try:
                weight = float(raw_weight)
            except (TypeError, ValueError):
                continue

            if weight <= 0:
                continue

            rendered.append(f"({option}:{weight:.3f})")

        return " ".join(rendered)

    @classmethod
    def _resolve_locus_controls(cls, locus):
        controls = locus.get("controls", {})
        if not isinstance(controls, dict):
            return []

        rendered = []
        for control in controls.values():
            if not isinstance(control, dict):
                continue

            control_type = str(control.get("type", "") or "").lower()
            if control_type == "expression_2d":
                descriptor = cls._render_expression_2d(control)
                if descriptor:
                    rendered.append(descriptor)

        return rendered

    @classmethod
    def _render_expression_2d(cls, control):
        x_value = cls._numeric_control_value(control.get("x_value"))
        y_value = cls._numeric_control_value(control.get("y_value"))
        if x_value is None and y_value is None:
            return ""
        if x_value == 0.0 and y_value == 0.0:
            return ""

        descriptors = []

        x_axis = control.get("x", {})
        y_axis = control.get("y", {})
        x_label = str(x_axis.get("label", "") if isinstance(x_axis, dict) else "").lower()
        y_label = str(y_axis.get("label", "") if isinstance(y_axis, dict) else "").lower()

        if x_value is not None:
            descriptors.append(
                cls._describe_expression_axis(
                    x_value,
                    x_label,
                    negative_label="frown",
                    positive_label="smile",
                )
            )

        if y_value is not None:
            descriptors.append(
                cls._describe_expression_axis(
                    y_value,
                    y_label,
                    negative_label="closed",
                    positive_label="open",
                    minimum=0.0,
                    maximum=1.0,
                )
            )

        return ", ".join(value for value in descriptors if value)

    @staticmethod
    def _describe_expression_axis(
        value,
        label,
        negative_label,
        positive_label,
        minimum=-1.0,
        maximum=1.0,
    ):
        midpoint = (minimum + maximum) / 2.0
        span = maximum - minimum
        if span <= 0:
            return ""

        normalized = (value - minimum) / span
        normalized = max(0.0, min(1.0, normalized))

        if label == "smile":
            if normalized < 0.20:
                return "pronounced frown"
            if normalized < 0.40:
                return "frown"
            if normalized < 0.60:
                return "neutral mouth"
            if normalized < 0.80:
                return "smiling"
            return "broad smile"

        if label == "open":
            if normalized < 0.15:
                return "mouth closed"
            if normalized < 0.45:
                return "mouth slightly open"
            if normalized < 0.75:
                return "mouth open"
            return "mouth wide open"

        if normalized < 0.33:
            return f"{negative_label} {label}".strip()
        if normalized > 0.67:
            return f"{positive_label} {label}".strip()
        return f"neutral {label}".strip()

    @staticmethod
    def _numeric_control_value(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

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
