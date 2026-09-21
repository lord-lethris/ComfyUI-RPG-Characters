"""Structured DNA editor node."""

import json
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
            },
            "optional": {
                # Hidden transport for frontend edits.  A socket cannot itself
                # be mutated by the browser and persisted in a workflow.
                "edited_section": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "hidden": True,
                }),
            },
        }

    RETURN_TYPES = ("RPG_DNA_SECTION",)
    RETURN_NAMES = ("DNA_SECTION",)
    FUNCTION = "edit"
    CATEGORY = "RPG/Gen 3/DNA"
    OUTPUT_NODE = True

    def edit(self, DNA_SECTION, section, operation, revision=0, edited_section=""):
        if operation == "Clear":
            result = make_empty_section(section)
        else:
            result = self._parse_edited_section(edited_section, section)
            if result is None:
                if not isinstance(DNA_SECTION, dict):
                    result = make_empty_section(section)
                else:
                    result = deepcopy(DNA_SECTION)
                    result["id"] = section
                    result.setdefault("values", {})
                    result.setdefault("traits", [])
                    result.setdefault("loci", [])

        # Always return the authoritative section to the frontend so the
        # graphical editor can stay in sync after execution.
        return {
            "ui": {"section": [result]},
            "result": (result,),
        }

    @staticmethod
    def _parse_edited_section(value, expected_section):
        if not value:
            return None
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
        if not isinstance(parsed, dict):
            return None
        if parsed.get("id") != expected_section:
            return None
        return parsed


NODE_CLASS_MAPPINGS = {"RPGCharacterDNAEditor": RPGCharacterDNAEditor}
NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGCharacterDNAEditor": "DNA Editor (Gen 3)"
}
