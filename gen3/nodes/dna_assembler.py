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
                "change_2": ("RPG_DNA_SECTION",),
                "change_3": ("RPG_DNA_SECTION",),
                "change_4": ("RPG_DNA_SECTION",),
                "change_5": ("RPG_DNA_SECTION",),
                "change_6": ("RPG_DNA_SECTION",),
                "change_7": ("RPG_DNA_SECTION",),
                "change_8": ("RPG_DNA_SECTION",),
                "change_9": ("RPG_DNA_SECTION",),
                "change_10": ("RPG_DNA_SECTION",),
                "change_11": ("RPG_DNA_SECTION",),
                "change_12": ("RPG_DNA_SECTION",),
                "change_13": ("RPG_DNA_SECTION",),
                "change_14": ("RPG_DNA_SECTION",),
                "change_15": ("RPG_DNA_SECTION",),
                "change_16": ("RPG_DNA_SECTION",),
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

        # Temporary execution diagnostics: prove which fixed change inputs
        # actually reached the Python node before changing the frontend again.
        print(
            "[RPG Gen3 DNA ASSEMBLER DEBUG]"
            f" change_keys={sorted(changes.keys())}"
            f" change_ids={[(name, value.get("id") if isinstance(value, dict) else None) for name, value in sorted(changes.items())]}"
        )

        for input_name in sorted(changes):
            if not input_name.startswith("change_"):
                continue

            change = changes[input_name]
            if not isinstance(change, dict):
                continue

            section_id = change.get("id")
            if section_id not in DNA_SECTIONS:
                continue

            print(
                "[RPG Gen3 DNA ASSEMBLER DEBUG]"
                f" applying={input_name} section={section_id}"
            )
            sections[section_id] = deepcopy(change)

        return (result,)


NODE_CLASS_MAPPINGS = {
    "RPGCharacterDNAAssembler": RPGCharacterDNAAssembler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGCharacterDNAAssembler": "DNA Assembler (Character)",
}
