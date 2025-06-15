# ComfyUI-RPG-Characters - Extended Node for Character Race, Gender, and more
# Author: Lord Lethris

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
from .rpg_character_data.rpg_emotion_data import EMOTION_DATA
from .rpg_character_data.rpg_scene_data import SCENE_DATA

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
                "emotion": (list(EMOTION_DATA.keys()),),
                "scene": (list(SCENE_DATA.keys()),),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("prompt", "negative_prompt", "Ollama_Generate_V2_Textbox_2", "selection_summary")
    FUNCTION = "generate_prompt"
    CATEGORY = "RPG"

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
        emotion,
        scene,
    ):
        selected_data = [
            RACE_DATA[race],
            ETHNICITY_DATA[ethnicity],
            GENDER_DATA[gender],
            AGE_DATA[age],
            CLASS_DATA[character_class],
            HAIR_STYLE_DATA[hair_style],
            HAIR_COLOUR_DATA[hair_colour],
            BEARD_STYLE_DATA[beard_style],
            BEARD_COLOUR_DATA[beard_colour],
            CLOTHES_STYLE_DATA[clothes_style],
            EMOTION_DATA[emotion],
            SCENE_DATA[scene],
        ]

        combined_prompt = ", ".join([entry["prompt"] for entry in selected_data if entry["prompt"]])
        combined_negative_prompt = ", ".join([entry["negative_prompt"] for entry in selected_data if entry["negative_prompt"]])

        # Enhanced plain scene handling
        if scene.lower().startswith("plain") or "chroma key" in scene.lower() or "solid" in scene.lower():
            scene_description = f"Scene: Solid {scene.replace('Plain ', '').replace('Chroma key ', '')} Background Only. No objects or distractions."
        else:
            scene_description = f"Scene: {scene}"

        # Ollama Textbox 2 format
        ollama_description = "\n".join([
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
            f"Emotion: {emotion}",
            scene_description
        ])

        selection_summary = ollama_description

        return (combined_prompt, combined_negative_prompt, ollama_description, selection_summary)


NODE_CLASS_MAPPINGS = {
    "RPGCharacterSelector": RPGCharacterSelector
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGCharacterSelector": "RPG Character Selector"
}
