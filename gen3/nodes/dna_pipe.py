"""Stable Character DNA routing node."""

from ..dna.character_dna import make_empty_section
from ..dna.dna_schema import DNA_SECTIONS, DNA_SECTION_DEFINITIONS


class RPGCharacterDNAPipe:
    """Expose stable, independently editable DNA sections."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "CHARACTER_INFO": ("CHARACTER_INFO",),
            }
        }

    RETURN_TYPES = tuple("RPG_DNA_SECTION" for _ in DNA_SECTIONS)
    RETURN_NAMES = tuple(DNA_SECTION_DEFINITIONS[s]["label"] for s in DNA_SECTIONS)
    FUNCTION = "route"
    CATEGORY = "RPG/Gen 3"

    def route(self, CHARACTER_INFO):
        document = CHARACTER_INFO if isinstance(CHARACTER_INFO, dict) else {}
        sections = document.get("sections", {})

        outputs = []
        for section_id in DNA_SECTIONS:
            section = sections.get(section_id)
            if not isinstance(section, dict):
                section = make_empty_section(section_id)
            outputs.append(section)

        return tuple(outputs)


NODE_CLASS_MAPPINGS = {"RPGCharacterDNAPipe": RPGCharacterDNAPipe}
NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGCharacterDNAPipe": "DNA Pipe (Character)"
}
