"""Structured DNA editor node.

The node is intentionally model-independent.  It accepts one section from the
DNA Pipe, exposes its loci to the frontend, and returns the edited section.
The frontend can persist weights on the section without turning them into
prompt syntax.
"""

from copy import deepcopy

from ..dna.character_dna import make_empty_section
from ..dna.dna_schema import DNA_SECTIONS


class RPGCharacterDNAEditor:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "DNA_SECTION": ("RPG_DNA_SECTION",),
                "section": (list(DNA_SECTIONS),),
                "operation": (["Edit", "Pass Through", "Clear"],),
                "revision": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647,
                    "step": 1,
                }),
            }
        }

    RETURN_TYPES = ("RPG_DNA_SECTION",)
    RETURN_NAMES = ("DNA_SECTION",)
    FUNCTION = "edit"
    CATEGORY = "RPG/Gen 3/DNA"
    OUTPUT_NODE = True

    def edit(self, DNA_SECTION, section, operation, revision=0):
        if operation == "Clear":
            return (make_empty_section(section),)

        if not isinstance(DNA_SECTION, dict):
            return (make_empty_section(section),)

        edited = deepcopy(DNA_SECTION)
        edited["id"] = section
        edited.setdefault("values", {})
        edited.setdefault("traits", [])
        edited.setdefault("loci", [])

        # The frontend stores sculpted weights on individual loci.  We do not
        # render or collapse those weights here; keeping them structured means
        # future generators can interpret the same DNA for different models.
        return (edited,)


NODE_CLASS_MAPPINGS = {"RPGCharacterDNAEditor": RPGCharacterDNAEditor}
NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGCharacterDNAEditor": "DNA Editor (Gen 3)"
}
