# ComfyUI-RPG-Characters - RPG Character Selector with DNA Locker
# Author: Lord Lethris

import hashlib
import json
import re
import secrets
import random

from .rpg_character_data.rpg_race_data import RACE_DATA
from .rpg_character_data.rpg_ethnicity_data import ETHNICITY_DATA
from .rpg_character_data.rpg_gender_data import GENDER_DATA
from .rpg_character_data.rpg_age_data import AGE_DATA
from .rpg_character_data.rpg_class_data import CLASS_DATA
from .rpg_character_data.rpg_hair_style_data import HAIR_STYLE_DATA
from .rpg_character_data.rpg_hair_colour_data import HAIR_COLOUR_DATA
from .rpg_character_data.rpg_beard_style_data import BEARD_STYLE_DATA
from .rpg_character_data.rpg_beard_colour_data import BEARD_COLOUR_DATA
from .rpg_character_data.rpg_clothes_style_data import CLOTHES_STYLE_DATA
from .rpg_character_data.rpg_augment_data import AUGMENT_DATA
from .rpg_character_data.rpg_emotion_data import EMOTION_DATA
from .rpg_character_data.rpg_scene_data import SCENE_DATA


VARIANT_PATTERN = re.compile(r"\{([^{}]+)\}")


def _race_overrides_ethnicity_visuals(race_entry):
    """Return visual trait categories explicitly controlled by the race."""
    prompt = str(race_entry.get("prompt", "")).lower()
    overrides = set()
    if "skin tone" in prompt or "skin tones" in prompt or "skin color" in prompt or "skin colour" in prompt:
        overrides.add("skin")
    if re.search(r"\beyes?\b", prompt):
        overrides.add("eyes")
    return overrides


def _remove_ethnicity_visual_conflicts(text, overrides):
    """Keep ethnicity identity/facial traits, but yield explicit race traits.

    Ethnicity data is deliberately lightweight prose rather than a structured
    schema, so conflict removal is clause-based. The explicit ethnicity label
    is always retained even when its first clause also contains skin/eye data.
    """
    if not text or not overrides:
        return text

    clauses = [clause.strip() for clause in str(text).split(",")]
    kept = []
    skip_continuation = False
    for index, clause in enumerate(clauses):
        lower = clause.lower()
        has_skin = bool(re.search(
            r"\bskin(?:\s+tone|\s+tones|\s+color|\s+colour)?\b", lower
        ))
        has_eyes = bool(re.search(
            r"\beye(?:s|\s+(?:color|colour))?\b", lower
        ))

        if skip_continuation:
            # Eye colours often continue across comma-separated fragments:
            # "... eye colors, typically brown, hazel, or green". Suppress
            # those continuation fragments while preserving later substantive
            # facial descriptors if a data entry happens to contain them.
            substantive = r"\b(face|features?|jaw|nose|cheek|hair|build|stature|complexion|skin)\b"
            if not re.search(substantive, lower):
                continue
            skip_continuation = False

        if ("skin" in overrides and has_skin) or ("eyes" in overrides and has_eyes):
            if index == 0:
                identity = re.match(r"(\(Ethnicity[^)]*\))", clause, flags=re.IGNORECASE)
                if identity:
                    kept.append(identity.group(1))
            if "eyes" in overrides and has_eyes:
                skip_continuation = True
            continue
        kept.append(clause)

    result = ", ".join(c for c in kept if c)
    result = re.sub(r"(^|,\s+)(?:and|with)\s+", r"\1", result, flags=re.IGNORECASE)
    result = re.sub(r"\s{2,}", " ", result).strip(" ,")
    return result


def _stable_seed(master_seed, locus_id, reroll_count=0):
    """Create a stable per-locus seed, including an optional reroll counter."""
    payload = f"RPGCharacterSelector|{master_seed}|{locus_id}|reroll:{int(reroll_count)}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _parse_state(value):
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def _normalise_weights(weights, count):
    values = []
    for index in range(count):
        try:
            value = float(weights.get(str(index), weights.get(index, 0)))
        except (TypeError, ValueError):
            value = 0.0
        values.append(max(0.0, value))

    # V2.4 DNA is intentionally limited to the nearest three variants.
    # This also sanitises older/stale workflow state that may contain more.
    if count > 3:
        keep = sorted(range(count), key=lambda i: values[i], reverse=True)[:3]
        keep = set(keep)
        values = [value if i in keep else 0.0 for i, value in enumerate(values)]

    total = sum(values)
    if total <= 0:
        return None
    return [value / total for value in values]


def _weighted_variant(options, weights):
    """Render an explicitly sculpted DNA locus.

    The output deliberately uses the user's proposed '&' syntax.
    The surrounding prompt parentheses (when present) are preserved, so:
    {emerald|gold} Skin tone:1.3
    can become:
    ((emerald:0.7) & (gold:0.3) Skin tone:1.3)
    """
    normalised = _normalise_weights(weights, len(options))
    if not normalised:
        return None

    active = [
        (option, weight)
        for option, weight in zip(options, normalised)
        if weight > 0.0005
    ]

    if not active:
        return None

    if len(active) == 1:
        return active[0][0]

    parts = [f"({option}:{weight:.3f}".rstrip("0").rstrip(".") + ")"
             for option, weight in active]
    return " & ".join(parts)


def resolve_prompt_variants_with_trace(text, master_seed, locus_prefix,
                                        locks=None, weights=None, rerolls=None):
    """Resolve every {A|B|C} group and return a DNA trace for the UI."""
    locks = locks or {}
    weights = weights or {}
    rerolls = rerolls or {}
    selections = []
    dna = []
    group_index = 0

    def replacer(match):
        nonlocal group_index
        raw = match.group(1)
        options = [item.strip() for item in raw.split("|")]
        locus_id = f"{locus_prefix}:{group_index}"
        group_index += 1

        if len(options) <= 1:
            # Existing behaviour for literal braces is preserved.
            choice = options[0] if options else ""
            selections.append(choice)
            return choice

        # V2.4 no longer exposes lock state in the UI. Keep the parameter for
        # backwards compatibility with older workflows, but never let stale
        # lock entries prevent the new Re-roll/Sculpt workflow from working.
        locked_value = None
        custom_weights = weights.get(locus_id)
        reroll_state = rerolls.get(locus_id, 0)
        avoid_value = None
        preview_value = None
        if isinstance(reroll_state, dict):
            try:
                reroll_count = max(0, int(reroll_state.get("count", 0)))
            except (TypeError, ValueError):
                reroll_count = 0
            avoid_value = reroll_state.get("avoid")
            preview_value = reroll_state.get("preview")
        else:
            try:
                reroll_count = max(0, int(reroll_state or 0))
            except (TypeError, ValueError):
                reroll_count = 0

        mode = "random"
        if locked_value in options:
            choice = locked_value
            mode = "locked"
            rendered = choice
            weight_map = None
        elif isinstance(custom_weights, dict):
            rendered = _weighted_variant(options, custom_weights)
            if rendered is not None:
                choice = " / ".join(
                    f"{option} {weight:.1%}"
                    for option, weight in zip(
                        options,
                        _normalise_weights(custom_weights, len(options))
                    )
                    if float(custom_weights.get(str(options.index(option)), 0) or 0) > 0
                )
                mode = "sculpted"
                weight_map = _normalise_weights(custom_weights, len(options))
            else:
                rendered = None
                weight_map = None
        else:
            # The Locker can choose a reroll immediately in the UI.  Persist
            # that preview in the reroll state so the next ComfyUI execution
            # uses exactly what the user saw, rather than changing it again
            # when Run is pressed.  Older states without a preview continue
            # to use the deterministic seed+reroll-counter path.
            if preview_value in options:
                choice = preview_value
            else:
                rng = random.Random(_stable_seed(master_seed, locus_id, reroll_count))
                if avoid_value in options and len(options) > 1:
                    # A deliberate locus reroll should actually move to another
                    # variant when alternatives exist, rather than occasionally
                    # landing on the same value by chance.
                    alternatives = [option for option in options if option != avoid_value]
                    choice = rng.choice(alternatives)
                else:
                    choice = rng.choice(options)
            rendered = choice
            weight_map = None

        if mode != "sculpted":
            weight_map = [1.0 if option == choice else 0.0 for option in options]

        dna.append({
            "id": locus_id,
            "label": f"Variant {group_index}",
            "options": options,
            "selected": choice,
            "weights": weight_map,
            "mode": mode,
        })
        selections.append(choice)
        return rendered

    resolved = VARIANT_PATTERN.sub(replacer, text)
    return resolved, selections, dna


class RPGCharacterSelector:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "race": (list(RACE_DATA.keys()),),
                "ethnicity": (list(ETHNICITY_DATA.keys()),),
                "gender": (list(GENDER_DATA.keys()),),
                "age": (list(AGE_DATA.keys()),),
                "character_class": (list(CLASS_DATA.keys()),),
                "hair_style": (list(HAIR_STYLE_DATA.keys()),),
                "hair_colour": (list(HAIR_COLOUR_DATA.keys()),),
                "beard_style": (list(BEARD_STYLE_DATA.keys()),),
                "beard_colour": (list(BEARD_COLOUR_DATA.keys()),),
                "clothes_style": (list(CLOTHES_STYLE_DATA.keys()),),
                "Augmentations": (list(AUGMENT_DATA.keys()),),
                "emotion": (list(EMOTION_DATA.keys()),),
                "scene": (list(SCENE_DATA.keys()),),
                "dna_seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 4294967295,
                    "step": 1,
                }),
                # Hidden execution revision.  DNA Locker UI edits must invalidate
                # ComfyUI's execution cache without changing the master DNA seed.
                "dna_revision": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647,
                    "step": 1,
                }),
            },
            "optional": {
                "dna_locks": ("STRING", {"default": "{}", "multiline": False}),
                "dna_weights": ("STRING", {"default": "{}", "multiline": False}),
                "dna_rerolls": ("STRING", {"default": "{}", "multiline": False}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = (
        "positive_prompt",
        "negative_prompt",
        "Ollama_Generate_V2_Textbox_2",
        "selection_summary",
    )
    FUNCTION = "generate_prompt"
    CATEGORY = "RPG"
    OUTPUT_NODE = True

    def generate_prompt(
        self,
        race,
        ethnicity,
        gender,
        age,
        character_class,
        hair_style,
        hair_colour,
        beard_style,
        beard_colour,
        clothes_style,
        Augmentations,
        emotion,
        scene,
        dna_seed=-1,
        dna_revision=0,
        dna_locks="{}",
        dna_weights="{}",
        dna_rerolls="{}",
    ):
        if dna_seed is None or int(dna_seed) < 0:
            dna_seed = secrets.randbits(32)
        else:
            dna_seed = int(dna_seed)

        locks = _parse_state(dna_locks)
        weights = _parse_state(dna_weights)
        rerolls = _parse_state(dna_rerolls)

        # Some ComfyUI frontend builds can treat auxiliary hidden widgets
        # differently when building the execution payload.  The DNA Locker
        # therefore mirrors reroll/unlock state inside dna_locks as a fallback.
        embedded_rerolls = locks.pop("__dna_rerolls", None)
        if not rerolls and isinstance(embedded_rerolls, dict):
            rerolls = embedded_rerolls

        race_entry = RACE_DATA[race]
        ethnicity_entry = ETHNICITY_DATA[ethnicity]
        ethnicity_entry_for_prompt = dict(ethnicity_entry)
        race_overrides = _race_overrides_ethnicity_visuals(race_entry)
        if race_overrides and ethnicity_entry_for_prompt.get("prompt"):
            ethnicity_entry_for_prompt["prompt"] = _remove_ethnicity_visual_conflicts(
                ethnicity_entry_for_prompt["prompt"], race_overrides
            )

        selected_data = [
            ("Race", race, race_entry),
            ("Ethnicity", ethnicity, ethnicity_entry_for_prompt),
            ("Gender", gender, GENDER_DATA[gender]),
            ("Age", age, AGE_DATA[age]),
            ("Class", character_class, CLASS_DATA[character_class]),
            ("Hair Style", hair_style, HAIR_STYLE_DATA[hair_style]),
            ("Hair Colour", hair_colour, HAIR_COLOUR_DATA[hair_colour]),
            ("Beard Style", beard_style, BEARD_STYLE_DATA[beard_style]),
            ("Beard Colour", beard_colour, BEARD_COLOUR_DATA[beard_colour]),
            ("Clothes Style", clothes_style, CLOTHES_STYLE_DATA[clothes_style]),
            ("Augmentations", Augmentations, AUGMENT_DATA[Augmentations]),
            ("Emotion", emotion, EMOTION_DATA[emotion]),
            ("Scene", scene, SCENE_DATA[scene]),
        ]

        resolved_prompts = []
        resolved_negatives = []
        all_selections = []
        dna_groups = []

        for field_name, selected_name, entry in selected_data:
            if entry["prompt"]:
                resolved, selections, dna = resolve_prompt_variants_with_trace(
                    entry["prompt"],
                    dna_seed,
                    f"{field_name}:positive",
                    locks,
                    weights,
                    rerolls,
                )
                resolved_prompts.append(resolved)
                all_selections.extend(selections)
                for group in dna:
                    group["field"] = field_name
                    group["source"] = "positive"
                    group["label"] = self._infer_variant_label(
                        entry["prompt"], group["options"], group["label"]
                    )
                dna_groups.extend(dna)

            if entry["negative_prompt"]:
                resolved, selections, dna = resolve_prompt_variants_with_trace(
                    entry["negative_prompt"],
                    dna_seed,
                    f"{field_name}:negative",
                    locks,
                    weights,
                    rerolls,
                )
                resolved_negatives.append(resolved)
                all_selections.extend(selections)
                for group in dna:
                    group["field"] = field_name
                    group["source"] = "negative"
                    group["label"] = self._infer_variant_label(
                        entry["negative_prompt"], group["options"], group["label"]
                    )
                dna_groups.extend(dna)

        combined_prompt = "Create an extreme close-up portrait of " + ", ".join(resolved_prompts)
        combined_negative_prompt = ", ".join(resolved_negatives)

        if scene.lower().startswith("plain") or "chroma key" in scene.lower() or "solid" in scene.lower():
            scene_description = (
                f"Scene: Solid {scene.replace('Plain ', '').replace('Chroma key ', '')} "
                "Background Only. No objects or distractions."
            )
        else:
            scene_description = f"Scene: {scene}"

        selection_summary = "\n".join([
            f"Race: {race}",
            f"Ethnicity: {ethnicity}",
            f"Gender: {gender}",
            f"Age: {age}",
            f"Class: {character_class}",
            f"Hair Style: {hair_style}",
            f"Hair Colour: {hair_colour}",
            f"Beard Style: {beard_style}",
            f"Beard Colour: {beard_colour}",
            f"Clothes Style: {clothes_style}",
            f"Augmentations: {Augmentations}",
            f"Emotion: {emotion}",
            scene_description,
            f"DNA Seed: {dna_seed}",
        ])

        if race_overrides:
            selection_summary += (
                "\nRace Priority: " + ", ".join(sorted(race_overrides)) +
                " override(s) applied to conflicting ethnicity traits."
            )

        ollama_description = (
            "Create an extreme close-up portrait of " +
            ", ".join(resolved_prompts) +
            ", Include Art Style."
        )

        if all_selections:
            selection_summary += "\nRandomized Choices Used: " + ", ".join(all_selections)

        # Human-readable DNA record. This is also useful when the node is
        # connected to logging/debugging tools.
        if dna_groups:
            selection_summary += "\nDNA Loci:"
            for group in dna_groups:
                if group["mode"] == "sculpted" and group["weights"]:
                    parts = [
                        f"{option}={weight:.3f}".rstrip("0").rstrip(".")
                        for option, weight in zip(group["options"], group["weights"])
                        if weight > 0.0005
                    ]
                    resolved = " / ".join(parts)
                else:
                    resolved = group["selected"]
                selection_summary += (
                    f"\n- {group['field']} [{group['source']}] "
                    f"{group['label']}: {resolved} ({group['mode']})"
                )

        # ComfyUI flattens UI values by iterating each UI field.  Therefore
        # custom structured UI payloads must themselves be list-valued, or a
        # dict here would arrive in JavaScript as ["seed", "groups"].
        # Keep the DNA record as a single list item.
        ui_payload = {
            "dna": [{
                "seed": dna_seed,
                "groups": dna_groups,
            }]
        }

        return {
            "ui": ui_payload,
            "result": (
                combined_prompt,
                combined_negative_prompt,
                ollama_description,
                selection_summary,
            ),
        }

    @staticmethod
    def _infer_variant_label(source_text, options, fallback):
        """Best-effort label for common '... Skin tone' / '... eyes' groups."""
        marker = "}"
        matches = list(VARIANT_PATTERN.finditer(source_text))
        for match in matches:
            if [item.strip() for item in match.group(1).split("|")] == options:
                suffix = source_text[match.end():]
                suffix = suffix.lstrip(" ,)")
                label_match = re.match(r"([A-Za-z][A-Za-z _-]{1,40})", suffix)
                if label_match:
                    label = label_match.group(1).strip()
                    if label.lower().startswith(("skin tone", "eyes", "eye colour")):
                        return label
                break
        return fallback


NODE_CLASS_MAPPINGS = {
    "RPGCharacterSelector": RPGCharacterSelector
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGCharacterSelector": "RPG Character Selector"
}
