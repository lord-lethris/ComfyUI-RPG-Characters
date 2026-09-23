"""Stable schema definitions for RPG Character Gen 3 DNA.

The DNA contract is deliberately model-independent and JSON-safe.  DNA describes
the character; downstream nodes decide how those values are rendered.

Ownership
---------
Character Gen 3 owns source/default metadata and definitions:
    id, label, description, values, traits, options, variant definitions,
    control definitions, source, source_inputs, source_signature.

DNA Editor owns user-authored locus state:
    selected, variant weights/mode, and live control values.

DNA Assembler owns section replacement.  It does not reinterpret or mutate
the contents of a section.

Prompt Builder and other downstream consumers are read-only with respect to
DNA.  They may derive representations from it, but must not modify the DNA
document.

Document contract
-----------------
A Character DNA document contains:
    dna_version, type, seed, source, selections, sections

Every section contains:
    id, label, description, values, traits, loci, source, source_inputs,
    source_signature

Every locus contains:
    id, label, options, selected, variant_sets, controls

A variant set contains:
    id, label, options, selected, weights, mode

A control contains a definition (for example x/y ranges) plus editor-owned
live values such as x_value/y_value or value/values.

Empty sections are valid and retain the same structural keys.  A source
signature may be None for an unpopulated standalone section; populated Gen 3
sections receive a deterministic signature.
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

DNA_SECTION_KEYS = (
    "id",
    "label",
    "description",
    "values",
    "traits",
    "loci",
    "source",
    "source_inputs",
    "source_signature",
)

DNA_LOCUS_KEYS = (
    "id",
    "label",
    "options",
    "selected",
    "variant_sets",
    "controls",
    "option_prompts",
    "option_negative_prompts",
)

DNA_VARIANT_SET_KEYS = (
    "id",
    "label",
    "options",
    "selected",
    "weights",
    "mode",
)


def get_section_definition(section_id):
    """Return a schema definition or raise a useful error for bad IDs."""
    try:
        return DNA_SECTION_DEFINITIONS[section_id]
    except KeyError as exc:
        raise ValueError(f"Unknown DNA section: {section_id}") from exc
