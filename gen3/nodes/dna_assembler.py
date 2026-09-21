"""Character DNA assembly node.

Combines the stable, independently editable Gen 3 DNA sections back into one
complete Character DNA document.  The assembler does not reinterpret or
render the sections; it preserves them as the source of truth for downstream
nodes.
"""

from copy import deepcopy

from ..dna.character_dna import make_character_dna
from ..dna.dna_schema import DNA_SECTIONS


class RPGCharacterDNAAssembler:
    """Rebuild a complete Character DNA document from edited sections."""

    @classmethod
    def INPUT_TYPES(cls):
        required = {
            section_id: ("RPG_DNA_SECTION",)
            for section_id in DNA_SECTIONS
        }
        required.update({
            "seed": ("INT", {
                "default": -1,
                "min": -1,
                "max": 4294967295,
                "step": 1,
            }),
            "source": ("STRING", {
                "default": "DNA Assembler (Character)",
                "multiline": False,
            }),
        })
        return {"required": required}

    RETURN_TYPES = ("CHARACTER_INFO",)
    RETURN_NAMES = ("CHARACTER_INFO",)
    FUNCTION = "assemble"
    CATEGORY = "RPG/Gen 3"

    def assemble(self, seed, source, **sections):
        assembled_sections = {}

        for section_id in DNA_SECTIONS:
            section = sections.get(section_id)

            if isinstance(section, dict) and section.get("id") == section_id:
                assembled_sections[section_id] = deepcopy(section)
            else:
                # Keep the output contract stable even if a disconnected or
                # malformed input reaches the node.
                assembled_sections[section_id] = None

        resolved_seed = None if int(seed) < 0 else int(seed)

        return (make_character_dna(
            seed=resolved_seed,
            source=source,
            sections=assembled_sections,
        ),)


NODE_CLASS_MAPPINGS = {
    "RPGCharacterDNAAssembler": RPGCharacterDNAAssembler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGCharacterDNAAssembler": "DNA Assembler (Character)",
}
