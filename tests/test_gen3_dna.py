"""Smoke tests for the Gen 3 structured DNA contract.

Run from the repository root with:
    python -m unittest discover -s tests -p "test_gen3*.py"
"""

import sys
import types
import unittest
from pathlib import Path

# Gen 3 uses package-relative imports because it normally lives inside the
# RPG-Characters custom-node package.  Give the test runner the same package
# context without changing the production import structure.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_PACKAGE_NAME = "_rpg_characters_test"
_test_package = types.ModuleType(_PACKAGE_NAME)
_test_package.__path__ = [str(_REPO_ROOT)]
sys.modules.setdefault(_PACKAGE_NAME, _test_package)

from _rpg_characters_test.gen3.dna.character_dna import (
    CHARACTER_DNA_VERSION,
    make_character_dna,
    make_source_signature,
)
from _rpg_characters_test.gen3.dna.dna_schema import DNA_SECTIONS
from _rpg_characters_test.gen3.nodes.dna_editor import RPGCharacterDNAEditor
from _rpg_characters_test.gen3.nodes.character_gen3_node import RPGCharacterGen3
from _rpg_characters_test.gen3.nodes.dna_pipe import RPGCharacterDNAPipe


class TestGen3DNA(unittest.TestCase):
    def test_character_dna_has_stable_sections(self):
        dna = make_character_dna(seed=1234)

        self.assertEqual(dna["type"], "RPG_CHARACTER_DNA")
        self.assertEqual(dna["dna_version"], CHARACTER_DNA_VERSION)
        self.assertEqual(tuple(dna["sections"].keys()), DNA_SECTIONS)

        for section_id in DNA_SECTIONS:
            section = dna["sections"][section_id]
            self.assertEqual(section["id"], section_id)
            self.assertIsInstance(section["values"], dict)
            self.assertIsInstance(section["traits"], list)

    def test_pipe_routes_each_section(self):
        dna = make_character_dna(
            seed=1234,
            sections={
                "identity": {
                    "values": {"race": "Human"},
                    "traits": ["Human"],
                    "source": "test",
                },
                "hair": {
                    "values": {"style": "Long"},
                    "traits": ["Long"],
                    "source": "test",
                },
            },
        )

        outputs = RPGCharacterDNAPipe().route(dna)

        self.assertEqual(len(outputs), len(DNA_SECTIONS))
        identity_index = DNA_SECTIONS.index("identity")
        hair_index = DNA_SECTIONS.index("hair")

        self.assertEqual(outputs[identity_index]["values"]["race"], "Human")
        self.assertEqual(outputs[hair_index]["values"]["style"], "Long")
        self.assertIn("loci", outputs[identity_index])
        self.assertIn("loci", outputs[hair_index])


    def test_character_gen3_populates_real_loci(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]
        values = {
            name: options[0][0]
            for name, options in inputs.items()
            if isinstance(options, tuple) and isinstance(options[0], list)
        }

        values["dna_seed"] = 1234
        # Pick a clothing entry with internal prompt variants so the test
        # exercises the structured variant-set extraction.
        values["clothes_style"] = "AD&D - Druidic Garments"
        dna = RPGCharacterGen3().create_character(**values)[0]

        self.assertEqual(dna["type"], "RPG_CHARACTER_DNA")
        self.assertEqual(dna["seed"], 1234)

        for section_id in ("identity", "anatomy", "hair", "facial_hair", "clothing", "equipment", "expression", "scene"):
            self.assertTrue(dna["sections"][section_id]["loci"], section_id)

        clothing = dna["sections"]["clothing"]["loci"][0]
        self.assertEqual(clothing["selected"], values["clothes_style"])
        self.assertGreaterEqual(len(clothing["variant_sets"]), 2)
        self.assertEqual(
            clothing["variant_sets"][0]["options"],
            ["forest green", "moss green", "olive", "brown", "tan", "dark grey"],
        )
        self.assertEqual(
            clothing["variant_sets"][1]["options"],
            ["brown leather", "woven hemp", "wooden", "bronze"],
        )

        expression = dna["sections"]["expression"]["loci"][0]
        self.assertIn("controls", expression)
        mouth = expression["controls"]["mouth"]
        self.assertEqual(mouth["type"], "expression_2d")
        self.assertEqual(mouth["x_value"], 0.0)
        self.assertEqual(mouth["y_value"], 0.0)

    def test_gen3_source_signatures_only_change_affected_sections(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]
        values = {
            name: options[0][0]
            for name, options in inputs.items()
            if isinstance(options, tuple) and isinstance(options[0], list)
        }
        values["dna_seed"] = 1234

        first = RPGCharacterGen3().create_character(**values)[0]
        values["hair_style"] = inputs["hair_style"][0][1]
        second = RPGCharacterGen3().create_character(**values)[0]

        self.assertNotEqual(
            first["sections"]["hair"]["source_signature"],
            second["sections"]["hair"]["source_signature"],
        )
        self.assertEqual(
            first["sections"]["expression"]["source_signature"],
            second["sections"]["expression"]["source_signature"],
        )

    def test_editor_preserves_edits_when_source_signature_is_unchanged(self):
        import json

        signature = make_source_signature("hair", {"hair_style": "Long", "hair_colour": "Black"})
        source = {
            "id": "hair",
            "values": {"style": "Long", "colour": "Black"},
            "traits": ["Long", "Black"],
            "loci": [{
                "id": "hair:style",
                "label": "Hair Style",
                "options": ["Long", "Short"],
                "selected": "Long",
                "weights": {"0": 1.0},
                "mode": "selected",
            }],
            "source_signature": signature,
            "source_inputs": {"hair_style": "Long", "hair_colour": "Black"},
        }
        edited = dict(source)
        edited["loci"] = [dict(source["loci"][0], selected="Short", weights={"1": 1.0}, mode="selected")]

        result = RPGCharacterDNAEditor().edit(
            source, "Edit", 1, json.dumps(edited)
        )["result"][0]

        self.assertEqual(result["loci"][0]["selected"], "Short")
        self.assertEqual(result["source_signature"], signature)

    def test_editor_resets_edits_when_source_signature_changes(self):
        import json

        old_signature = make_source_signature("hair", {"hair_style": "Long", "hair_colour": "Black"})
        new_signature = make_source_signature("hair", {"hair_style": "Short", "hair_colour": "Black"})
        source = {
            "id": "hair",
            "values": {"style": "Short", "colour": "Black"},
            "traits": ["Short", "Black"],
            "loci": [{
                "id": "hair:style",
                "label": "Hair Style",
                "options": ["Long", "Short"],
                "selected": "Short",
                "weights": {"1": 1.0},
                "mode": "selected",
            }],
            "source_signature": new_signature,
            "source_inputs": {"hair_style": "Short", "hair_colour": "Black"},
        }
        edited = dict(source)
        edited["source_signature"] = old_signature
        edited["loci"] = [dict(source["loci"][0], selected="Long", weights={"0": 1.0}, mode="selected")]

        result = RPGCharacterDNAEditor().edit(
            source, "Edit", 2, json.dumps(edited)
        )["result"][0]

        self.assertEqual(result["loci"][0]["selected"], "Short")
        self.assertEqual(result["source_signature"], new_signature)

    def test_editor_pass_through_preserves_data(self):
        section = {
            "id": "hair",
            "label": "Hair",
            "description": "test",
            "values": {"colour": "Black"},
            "traits": ["Black"],
            "source": "test",
        }

        result = RPGCharacterDNAEditor().edit(
            section,
            "Pass Through",
        )["result"][0]

        self.assertEqual(result["id"], "hair")
        self.assertEqual(result["values"]["colour"], "Black")

    def test_editor_clear_returns_empty_valid_section(self):
        section = {
            "id": "hair",
            "values": {"colour": "Black"},
        }

        result = RPGCharacterDNAEditor().edit(
            section,
            "Clear",
        )["result"][0]

        self.assertEqual(result["id"], "hair")
        self.assertEqual(result["values"], {})
        self.assertEqual(result["traits"], [])


    def test_editor_accepts_persisted_structured_section(self):
        section = {
            "id": "hair",
            "label": "Hair",
            "description": "test",
            "values": {"colour": "Black"},
            "traits": ["Black"],
            "loci": [{
                "id": "hair:colour",
                "label": "Hair Colour",
                "options": ["Black", "White"],
                "selected": "White",
                "weights": {"0": 0.25, "1": 0.75},
                "mode": "sculpted",
            }],
            "source": "test",
            "source_signature": make_source_signature("hair", {"hair_style": "Long", "hair_colour": "Black"}),
        }

        import json
        result = RPGCharacterDNAEditor().edit(
            section,
            "Edit",
            1,
            json.dumps(section),
        )["result"][0]

        self.assertEqual(result["id"], "hair")
        self.assertEqual(result["loci"][0]["selected"], "White")
        self.assertEqual(result["loci"][0]["weights"]["1"], 0.75)

if __name__ == "__main__":
    unittest.main()
