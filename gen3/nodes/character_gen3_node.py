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
        sections = {
            "identity": {
                "values": {
                    "race": race,
                    "ethnicity": ethnicity,
                    "class": character_class,
                },
                "traits": [race, ethnicity, character_class],
                "source": "rpg_character_data",
            },
            "anatomy": {
                "values": {"gender": gender, "age": age},
                "traits": [gender, age],
                "source": "rpg_character_data",
            },
            "hair": {
                "values": {"style": hair_style, "colour": hair_colour},
                "traits": [hair_style, hair_colour],
                "source": "rpg_character_data",
            },
            "facial_hair": {
                "values": {"style": beard_style, "colour": beard_colour},
                "traits": [beard_style, beard_colour],
                "source": "rpg_character_data",
            },
            "clothing": {
                "values": {"style": clothes_style},
                "traits": [clothes_style],
                "source": "rpg_character_data",
            },
            "equipment": {
                "values": {"augmentations": augmentations},
                "traits": [augmentations],
                "source": "rpg_character_data",
            },
            "expression": {
                "values": {"emotion": emotion},
                "traits": [emotion],
                "source": "rpg_character_data",
            },
            "scene": {
                "values": {"scene": scene},
                "traits": [scene],
                "source": "rpg_character_data",
            },
        }

        # Explicitly retain stable empty sections for downstream editors.
        for section_id in DNA_SECTIONS:
            sections.setdefault(section_id, {})

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
