"""Character DNA assembly node.

Combines the stable, independently editable Gen 3 DNA sections back into one
complete Character DNA document.  The assembler starts from the original
Character DNA and overlays any connected section changes.  Unconnected change
inputs are intentionally ignored.
"""

from copy import deepcopy

from ..dna.dna_schema import DNA_SECTIONS


class RPGCharacterDNAAssembler:
    """Apply zero or more edited DNA sections to a Character DNA document."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character_info": ("CHARACTER_INFO",),
            },
            "optional": {
                "change_1": ("RPG_DNA_SECTION",),
            },
        }

    RETURN_TYPES = ("CHARACTER_INFO",)
    RETURN_NAMES = ("CHARACTER_INFO",)
    FUNCTION = "assemble"
    CATEGORY = "RPG/Gen 3"

    def assemble(self, character_info, **changes):
        result = deepcopy(character_info)

        sections = result.get("sections")
        if not isinstance(sections, dict):
            sections = {}
            result["sections"] = sections

        for input_name in sorted(changes):
            if not input_name.startswith("change_"):
                continue

            change = changes[input_name]
            if not isinstance(change, dict):
                continue

            section_id = change.get("id")
            if section_id not in DNA_SECTIONS:
                continue

            sections[section_id] = deepcopy(change)

        return (result,)


NODE_CLASS_MAPPINGS = {
    "RPGCharacterDNAAssembler": RPGCharacterDNAAssembler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGCharacterDNAAssembler": "DNA Assembler (Character)",
}
