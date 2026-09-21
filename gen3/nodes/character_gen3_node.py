"""RPG Character Gen 3 source-of-truth node."""

from ..dna.character_dna import make_character_dna
from ..dna.dna_schema import DNA_SECTIONS

from rpg_character_data.rpg_race_data import RACE_DATA
from rpg_character_data.rpg_ethnicity_data import ETHNICITY_DATA
from rpg_character_data.rpg_gender_data import GENDER_DATA
from rpg_character_data.rpg_age_data import AGE_DATA
from rpg_character_data.rpg_class_data import CLASS_DATA
from rpg_character_data.rpg_hair_style_data import HAIR_STYLE_DATA
from rpg_character_data.rpg_hair_colour_data import HAIR_COLOUR_DATA
from rpg_character_data.rpg_beard_style_data import BEARD_STYLE_DATA
from rpg_character_data.rpg_beard_colour_data import BEARD_COLOUR_DATA
from rpg_character_data.rpg_clothes_style_data import CLOTHES_STYLE_DATA
from rpg_character_data.rpg_augment_data import AUGMENT_DATA
from rpg_character_data.rpg_emotion_data import EMOTION_DATA
from rpg_character_data.rpg_scene_data import SCENE_DATA


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
        }

        # Keep the first Gen 3 implementation intentionally conservative:
        # existing V2 data remains the source for the selected values, while
        # the new DNA document provides the stable contract for future nodes.
        # Each populated section also exposes its selectable loci.  The
        # options come from the existing RPG data tables, while the DNA Editor
        # stores the user's blend independently of prompt rendering.
        loci = {
            "identity": [
                {"id": "identity:race", "label": "Race", "options": list(RACE_DATA.keys()), "selected": race},
                {"id": "identity:ethnicity", "label": "Ethnicity", "options": list(ETHNICITY_DATA.keys()), "selected": ethnicity},
                {"id": "identity:class", "label": "Class", "options": list(CLASS_DATA.keys()), "selected": character_class},
            ],
            "anatomy": [
                {"id": "anatomy:gender", "label": "Gender", "options": list(GENDER_DATA.keys()), "selected": gender},
                {"id": "anatomy:age", "label": "Age", "options": list(AGE_DATA.keys()), "selected": age},
            ],
            "hair": [
                {"id": "hair:style", "label": "Hair Style", "options": list(HAIR_STYLE_DATA.keys()), "selected": hair_style},
                {"id": "hair:colour", "label": "Hair Colour", "options": list(HAIR_COLOUR_DATA.keys()), "selected": hair_colour},
            ],
            "facial_hair": [
                {"id": "facial_hair:style", "label": "Beard Style", "options": list(BEARD_STYLE_DATA.keys()), "selected": beard_style},
                {"id": "facial_hair:colour", "label": "Beard Colour", "options": list(BEARD_COLOUR_DATA.keys()), "selected": beard_colour},
            ],
            "clothing": [
                {"id": "clothing:style", "label": "Clothing Style", "options": list(CLOTHES_STYLE_DATA.keys()), "selected": clothes_style},
            ],
            "equipment": [
                {"id": "equipment:augmentations", "label": "Augmentations", "options": list(AUGMENT_DATA.keys()), "selected": augmentations},
            ],
            "expression": [
                {"id": "expression:emotion", "label": "Emotion", "options": list(EMOTION_DATA.keys()), "selected": emotion},
            ],
            "scene": [
                {"id": "scene:scene", "label": "Scene", "options": list(SCENE_DATA.keys()), "selected": scene},
            ],
        }

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

        # Explicitly retain stable empty sections for downstream editors.
        for section_id in DNA_SECTIONS:
            sections.setdefault(section_id, {})
            sections[section_id].setdefault("loci", [])

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
