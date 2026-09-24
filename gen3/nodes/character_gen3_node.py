"""RPG Character Gen 3 source-of-truth node."""

import re

from ..dna.character_dna import make_character_dna, make_source_signature
from ..dna.dna_schema import DNA_SECTIONS
from ..dna.face_data import FACE_LOCUS_DATA

from ...rpg_character_data.rpg_race_data import RACE_DATA
from ...rpg_character_data.rpg_ethnicity_data import ETHNICITY_DATA
from ...rpg_character_data.rpg_gender_data import GENDER_DATA
from ...rpg_character_data.rpg_age_data import AGE_DATA
from ...rpg_character_data.rpg_class_data import CLASS_DATA
from ...rpg_character_data.rpg_hair_style_data import HAIR_STYLE_DATA
from ...rpg_character_data.rpg_hair_colour_data import HAIR_COLOUR_DATA
from ...rpg_character_data.rpg_beard_style_data import BEARD_STYLE_DATA
from ...rpg_character_data.rpg_beard_colour_data import BEARD_COLOUR_DATA
from ...rpg_character_data.rpg_clothes_style_data import CLOTHES_STYLE_DATA
from ...rpg_character_data.rpg_augment_data import AUGMENT_DATA
from ...rpg_character_data.rpg_emotion_data import EMOTION_DATA
from ...rpg_character_data.rpg_scene_data import SCENE_DATA


VARIANT_PATTERN = re.compile(r"\{([^{}]+)\}")


def _variant_label(prompt, match, index):
    """Give prompt variants a human-readable label from nearby context."""
    context = prompt[match.end():match.end() + 80].lower()

    # The source prompts commonly place the thing being varied immediately
    # after the {A|B|C} expression. Keep this deliberately conservative so
    # labels remain descriptive without pretending to understand arbitrary
    # prompt prose.
    labels = (
        ("eye", "Eye Colour"),
        ("eyes", "Eye Colour"),
        ("skin", "Skin Tone"),
        ("hair", "Hair"),
        ("face shape", "Face Shape"),
        ("facial", "Facial Features"),
        ("lips", "Lip Shape"),
        ("nose", "Nose Shape"),
    )
    for token, label in labels:
        if token in context:
            return label

    return f"Variant {index + 1}"


def _select_face_options(seed, context):
    """Choose a stable default face from the character seed/context."""
    selected = {}
    for locus_id, definition in FACE_LOCUS_DATA.items():
        options = list(definition["options"].keys())
        if not options:
            continue
        signature = make_source_signature(
            f"face:{locus_id}",
            {
                "seed": seed,
                **context,
            },
        )
        index = int(signature[:8], 16) % len(options)
        selected[locus_id] = options[index]
    return selected


def _extract_variant_sets(entry, prefix):
    """Expose the internal prompt variants as structured DNA variant sets."""
    prompt = str(entry.get("prompt", "")) if isinstance(entry, dict) else ""
    variant_sets = []
    for index, match in enumerate(VARIANT_PATTERN.finditer(prompt)):
        options = [item.strip() for item in match.group(1).split("|") if item.strip()]
        if len(options) <= 1:
            continue
        variant_sets.append({
            "id": f"{prefix}:variant:{index}",
            "label": _variant_label(prompt, match, len(variant_sets)),
            "options": options,
            "selected": options[0],
            "weights": {"0": 1.0},
            "mode": "random",
        })
    return variant_sets


class RPGCharacterGen3:
    """Create structured Character DNA from the existing V2 character data."""

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
                "augmentations": (list(AUGMENT_DATA.keys()),),
                "emotion": (list(EMOTION_DATA.keys()),),
                "scene": (list(SCENE_DATA.keys()),),
                "dna_seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 4294967295,
                    "step": 1,
                }),
            }
        }

    RETURN_TYPES = ("CHARACTER_INFO",)
    RETURN_NAMES = ("CHARACTER_INFO",)
    FUNCTION = "create_character"
    CATEGORY = "RPG/Gen 3"

    def create_character(
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
        augmentations,
        emotion,
        scene,
        dna_seed=-1,
    ):
        face_context = {
            "race": race,
            "ethnicity": ethnicity,
            "gender": gender,
            "age": age,
        }
        face_selections = _select_face_options(
            None if int(dna_seed) < 0 else int(dna_seed),
            face_context,
        )

        selections = {
            "race": race,
            "ethnicity": ethnicity,
            "gender": gender,
            "age": age,
            "class": character_class,
            "hair_style": hair_style,
            "hair_colour": hair_colour,
            "beard_style": beard_style,
            "beard_colour": beard_colour,
            "clothing": clothes_style,
            "augmentations": augmentations,
            "emotion": emotion,
            "scene": scene,
            "face": dict(face_selections),
        }

        # Keep the first Gen 3 implementation intentionally conservative:
        # existing V2 data remains the source for the selected values, while
        # the new DNA document provides the stable contract for future nodes.
        # Each populated section also exposes its selectable loci.  The
        # options come from the existing RPG data tables, while the DNA Editor
        # stores the user's blend independently of prompt rendering.
        selected_entries = {
            "identity:race": ("Race", race, RACE_DATA[race]),
            "identity:ethnicity": ("Ethnicity", ethnicity, ETHNICITY_DATA[ethnicity]),
            "identity:class": ("Class", character_class, CLASS_DATA[character_class]),
            "anatomy:gender": ("Gender", gender, GENDER_DATA[gender]),
            "anatomy:age": ("Age", age, AGE_DATA[age]),
            "hair:style": ("Hair Style", hair_style, HAIR_STYLE_DATA[hair_style]),
            "hair:colour": ("Hair Colour", hair_colour, HAIR_COLOUR_DATA[hair_colour]),
            "facial_hair:style": ("Beard Style", beard_style, BEARD_STYLE_DATA[beard_style]),
            "facial_hair:colour": ("Beard Colour", beard_colour, BEARD_COLOUR_DATA[beard_colour]),
            "clothing:style": ("Clothing Style", clothes_style, CLOTHES_STYLE_DATA[clothes_style]),
            "equipment:augmentations": ("Augmentations", augmentations, AUGMENT_DATA[augmentations]),
            "expression:emotion": ("Emotion", emotion, EMOTION_DATA[emotion]),
            "scene:scene": ("Scene", scene, SCENE_DATA[scene]),
        }

        loci = {}
        for locus_id, (label, selected, entry) in selected_entries.items():
            field = locus_id.split(":", 1)[0]
            option_data = {
                "identity:race": RACE_DATA,
                "identity:ethnicity": ETHNICITY_DATA,
                "identity:class": CLASS_DATA,
                "anatomy:gender": GENDER_DATA,
                "anatomy:age": AGE_DATA,
                "hair:style": HAIR_STYLE_DATA,
                "hair:colour": HAIR_COLOUR_DATA,
                "facial_hair:style": BEARD_STYLE_DATA,
                "facial_hair:colour": BEARD_COLOUR_DATA,
                "clothing:style": CLOTHES_STYLE_DATA,
                "equipment:augmentations": AUGMENT_DATA,
                "expression:emotion": EMOTION_DATA,
                "scene:scene": SCENE_DATA,
            }[locus_id]
            locus = {
                "id": locus_id,
                "label": label,
                "options": list(option_data.keys()),
                "selected": selected,
                "variant_sets": _extract_variant_sets(entry, locus_id),
                "option_prompts": {
                    key: str(value.get("prompt", ""))
                    for key, value in option_data.items()
                    if isinstance(value, dict)
                },
                "option_negative_prompts": {
                    key: str(value.get("negative_prompt", ""))
                    for key, value in option_data.items()
                    if isinstance(value, dict) and value.get("negative_prompt")
                },
            }
            if locus_id == "expression:emotion":
                locus["controls"] = {
                    "mouth": {
                        "label": "Mouth",
                        "type": "expression_2d",
                        "x": {"label": "Smile", "min": -1.0, "max": 1.0},
                        "y": {"label": "Open", "min": 0.0, "max": 1.0},
                        "x_value": 0.0,
                        "y_value": 0.0,
                    }
                }
            loci.setdefault(field, []).append(locus)

        face_loci = []
        for locus_id, definition in FACE_LOCUS_DATA.items():
            options = list(definition["options"].keys())
            selected = face_selections.get(locus_id)
            option_data = definition["options"]
            face_loci.append({
                "id": f"face:{locus_id}",
                "label": definition["label"],
                "options": options,
                "selected": selected,
                "variant_sets": [],
                "option_prompts": {
                    key: str(value.get("prompt", ""))
                    for key, value in option_data.items()
                    if isinstance(value, dict)
                },
                "option_negative_prompts": {
                    key: str(value.get("negative_prompt", ""))
                    for key, value in option_data.items()
                    if isinstance(value, dict) and value.get("negative_prompt")
                },
            })

        sections = {
            "identity": {
                "values": {
                    "race": race,
                    "ethnicity": ethnicity,
                    "class": character_class,
                },
                "traits": [race, ethnicity, character_class],
                "source": "rpg_character_data",
                "loci": loci["identity"],
            },
            "anatomy": {
                "values": {"gender": gender, "age": age},
                "traits": [gender, age],
                "source": "rpg_character_data",
                "loci": loci["anatomy"],
            },
            "hair": {
                "values": {"style": hair_style, "colour": hair_colour},
                "traits": [hair_style, hair_colour],
                "source": "rpg_character_data",
                "loci": loci["hair"],
            },
            "facial_hair": {
                "values": {"style": beard_style, "colour": beard_colour},
                "traits": [beard_style, beard_colour],
                "source": "rpg_character_data",
                "loci": loci["facial_hair"],
            },
            "clothing": {
                "values": {"style": clothes_style},
                "traits": [clothes_style],
                "source": "rpg_character_data",
                "loci": loci["clothing"],
            },
            "equipment": {
                "values": {"augmentations": augmentations},
                "traits": [augmentations],
                "source": "rpg_character_data",
                "loci": loci["equipment"],
            },
            "expression": {
                "values": {"emotion": emotion},
                "traits": [emotion],
                "source": "rpg_character_data",
                "loci": loci["expression"],
            },
            "scene": {
                "values": {"scene": scene},
                "traits": [scene],
                "source": "rpg_character_data",
                "loci": loci["scene"],
            },
        }

        sections["face"] = {
            "values": dict(face_selections),
            "traits": list(face_selections.values()),
            "source": "gen3_face_data",
            "loci": face_loci,
        }

        # Explicitly retain stable empty sections for downstream editors.
        for section_id in DNA_SECTIONS:
            sections.setdefault(section_id, {})
            sections[section_id].setdefault("loci", [])

        # Each section gets a deterministic signature for the upstream values
        # that actually define it. DNA Editors use this to distinguish a
        # genuine source change from an ordinary graph execution.
        source_inputs = {
            "identity": {"race": race, "ethnicity": ethnicity, "class": character_class},
            "anatomy": {"gender": gender, "age": age},
            "hair": {"hair_style": hair_style, "hair_colour": hair_colour},
            "facial_hair": {"beard_style": beard_style, "beard_colour": beard_colour},
            "clothing": {"clothes_style": clothes_style},
            "equipment": {"augmentations": augmentations},
            "expression": {"emotion": emotion},
            "scene": {"scene": scene},
            "face": {
                "seed": None if int(dna_seed) < 0 else int(dna_seed),
                **face_context,
            },
            "skin": {},
            "armour": {},
            "pose": {},
            "style": {},
        }

        for section_id in DNA_SECTIONS:
            inputs = source_inputs.get(section_id, {})
            sections[section_id]["source_inputs"] = dict(inputs)
            sections[section_id]["source_signature"] = make_source_signature(section_id, inputs)

        seed = None if int(dna_seed) < 0 else int(dna_seed)
        return (make_character_dna(
            selections=selections,
            seed=seed,
            source="RPG Character Gen 3",
            sections=sections,
        ),)


NODE_CLASS_MAPPINGS = {"RPGCharacterGen3": RPGCharacterGen3}
NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGCharacterGen3": "RPG Character Gen 3"
}
