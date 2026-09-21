"""Stable schema definitions for RPG Character Gen 3 DNA.

The schema is deliberately model-independent.  Values describe the character;
downstream nodes decide how those values are rendered into prompts, control
images, H3 instructions, or other model-specific representations.
"""

DNA_SECTION_DEFINITIONS = {
    "identity": {
        "label": "Identity",
        "description": "Core identity and RPG character selection.",
    },
    "anatomy": {
        "label": "Anatomy",
        "description": "Body, age, gender and physical build information.",
    },
    "face": {
        "label": "Face",
        "description": "Facial structure and defining facial traits.",
    },
    "hair": {
        "label": "Hair",
        "description": "Head hair style, colour and related traits.",
    },
    "facial_hair": {
        "label": "Facial Hair",
        "description": "Beard and moustache information.",
    },
    "skin": {
        "label": "Skin",
        "description": "Skin tone and other skin-specific traits.",
    },
    "clothing": {
        "label": "Clothing",
        "description": "Clothing and outfit information.",
    },
    "armour": {
        "label": "Armour",
        "description": "Armour and protective equipment.",
    },
    "equipment": {
        "label": "Equipment",
        "description": "Weapons, accessories and carried equipment.",
    },
    "expression": {
        "label": "Expression",
        "description": "Emotion and facial expression.",
    },
    "pose": {
        "label": "Pose",
        "description": "Character pose and body positioning.",
    },
    "style": {
        "label": "Style",
        "description": "Visual style and rendering preferences.",
    },
    "scene": {
        "label": "Scene",
        "description": "Environment, background and scene information.",
    },
}

DNA_SECTIONS = tuple(DNA_SECTION_DEFINITIONS.keys())


def get_section_definition(section_id):
    """Return a schema definition or raise a useful error for bad IDs."""
    try:
        return DNA_SECTION_DEFINITIONS[section_id]
    except KeyError as exc:
        raise ValueError(f"Unknown DNA section: {section_id}") from exc
