"""First-pass DNA Editor node.

The graphical sculptor will replace/extend this editor once the data contract
is proven.  This version deliberately behaves as a safe pass-through editor
so workflows can already be wired and tested.
"""

import json

from ..dna.character_dna import make_empty_section
from ..dna.dna_schema import DNA_SECTIONS, DNA_SECTION_DEFINITIONS


class RPGCharacterDNAEditor:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "DNA_SECTION": ("RPG_DNA_SECTION",),
                "section": (list(DNA_SECTIONS),),
                "operation": (["Pass Through", "Clear"],),
            }
        }

    RETURN_TYPES = ("RPG_DNA_SECTION",)
    RETURN_NAMES = ("DNA_SECTION",)
    FUNCTION = "edit"
    CATEGORY = "RPG/Gen 3/DNA"

    def edit(self, DNA_SECTION, section, operation):
        if operation == "Clear":
            return (make_empty_section(section),)

        if not isinstance(DNA_SECTION, dict):
            return (make_empty_section(section),)

        # Keep the editor honest while the visual UI is being built: never
        # silently change a section into a different section.
        edited = dict(DNA_SECTION)
        edited["id"] = section
        return (edited,)


NODE_CLASS_MAPPINGS = {"RPGCharacterDNAEditor": RPGCharacterDNAEditor}
NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGCharacterDNAEditor": "DNA Editor (Gen 3)"
}
