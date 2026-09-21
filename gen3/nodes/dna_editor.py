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

    def edit(self, DNA_SECTION, operation, revision=0, edited_section=""):
        section = DNA_SECTION.get("id") if isinstance(DNA_SECTION, dict) else None
        if section not in DNA_SECTIONS:
            raise ValueError("DNA Editor received an invalid or missing DNA section")

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
            elif isinstance(DNA_SECTION, dict):
                # The incoming Character Gen 3 section is the schema authority.
                # Merge its locus metadata into persisted edits so newly added
                # fields such as internal prompt variant sets survive older
                # edited_section payloads saved in workflows.
                result = self._merge_locus_metadata(DNA_SECTION, result)

        # Always return the authoritative section to the frontend so the
        # graphical editor can stay in sync after execution.
        return {
            "ui": {"section": [result]},
            "result": (result,),
        }

    @staticmethod
    def _merge_locus_metadata(source, persisted):
        result = deepcopy(persisted)
        source_loci = {
            locus.get("id"): locus
            for locus in source.get("loci", [])
            if isinstance(locus, dict) and locus.get("id")
        }
        merged_loci = []
        for persisted_locus in result.get("loci", []):
            if not isinstance(persisted_locus, dict):
                continue
            locus_id = persisted_locus.get("id")
            source_locus = source_loci.get(locus_id)
            merged = deepcopy(source_locus or {})
            merged.update(deepcopy(persisted_locus))
            for key in ("label", "options", "variant_sets"):
                if source_locus and key in source_locus:
                    merged[key] = deepcopy(source_locus[key])
            merged_loci.append(merged)
            source_loci.pop(locus_id, None)

        for source_locus in source_loci.values():
            merged_loci.append(deepcopy(source_locus))

        result["loci"] = merged_loci
        return result

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
