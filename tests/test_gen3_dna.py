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
from _rpg_characters_test.gen3.dna.dna_schema import (
    DNA_SECTIONS,
    DNA_SECTION_KEYS,
    DNA_LOCUS_KEYS,
    DNA_VARIANT_SET_KEYS,
)
from _rpg_characters_test.gen3.nodes.dna_editor import RPGCharacterDNAEditor
from _rpg_characters_test.gen3.nodes.character_gen3_node import RPGCharacterGen3
from _rpg_characters_test.gen3.nodes.dna_pipe import RPGCharacterDNAPipe
from _rpg_characters_test.gen3.nodes.dna_assembler import RPGCharacterDNAAssembler


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

        for section_id in DNA_SECTIONS:
            section = dna["sections"][section_id]
            self.assertTrue(all(key in section for key in DNA_SECTION_KEYS))
            self.assertEqual(section["source_inputs"], {})
            self.assertIsNone(section["source_signature"])


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


    def test_assembler_exposes_base_and_first_change_input(self):
        inputs = RPGCharacterDNAAssembler.INPUT_TYPES()

        self.assertEqual(
            inputs["required"]["character_info"],
            ("CHARACTER_INFO",),
        )
        self.assertEqual(
            inputs["optional"]["change_1"],
            ("RPG_DNA_SECTION",),
        )
        for index in range(1, 17):
            self.assertEqual(
                inputs["optional"][f"change_{index}"],
                ("RPG_DNA_SECTION",),
            )
        self.assertNotIn("change_17", inputs.get("optional", {}))


    def test_assembler_accepts_character_info_without_changes(self):
        character = make_character_dna(
            seed=4321,
            source="Gen 3",
            sections={
                "hair": {
                    "values": {"style": "Long"},
                    "traits": ["Long"],
                    "loci": [],
                },
            },
        )

        result = RPGCharacterDNAAssembler().assemble(
            character_info=character,
        )[0]

        self.assertEqual(result, character)
        self.assertIsNot(result, character)
        self.assertIsNot(result["sections"], character["sections"])

    def test_assembler_applies_connected_section_changes(self):
        character = make_character_dna(
            seed=4321,
            source="Gen 3",
            sections={
                "hair": {
                    "values": {"style": "Long"},
                    "traits": ["Long"],
                    "loci": [],
                },
                "expression": {
                    "values": {"emotion": "Neutral"},
                    "traits": ["Neutral"],
                    "loci": [],
                },
            },
        )

        edited_hair = {
            "id": "hair",
            "values": {"style": "Short"},
            "traits": ["Short"],
            "loci": [],
            "source_signature": "edited-hair",
        }
        edited_expression = {
            "id": "expression",
            "values": {"emotion": "Angry"},
            "traits": ["Angry"],
            "loci": [],
            "source_signature": "edited-expression",
        }

        result = RPGCharacterDNAAssembler().assemble(
            character_info=character,
            change_2=edited_expression,
            change_1=edited_hair,
        )[0]

        self.assertEqual(result["seed"], character["seed"])
        self.assertEqual(result["source"], character["source"])
        self.assertEqual(result["sections"]["hair"], edited_hair)
        self.assertEqual(result["sections"]["expression"], edited_expression)

        # Unchanged sections remain untouched.
        for section_id in DNA_SECTIONS:
            if section_id not in ("hair", "expression"):
                self.assertEqual(
                    result["sections"][section_id],
                    character["sections"][section_id],
                )

        # The assembler must not mutate its source character or change inputs.
        self.assertEqual(character["sections"]["hair"]["values"]["style"], "Long")
        self.assertEqual(edited_hair["values"]["style"], "Short")

    def test_assembler_accepts_multiple_dynamic_change_inputs(self):
        character = make_character_dna(seed=7)
        edited_hair = {
            "id": "hair",
            "values": {"style": "Short"},
            "traits": ["Short"],
            "loci": [],
        }
        edited_expression = {
            "id": "expression",
            "values": {"emotion": "Joy"},
            "traits": ["Joy"],
            "loci": [],
        }

        result = RPGCharacterDNAAssembler().assemble(
            character_info=character,
            change_1=edited_hair,
            change_2=edited_expression,
            change_3=None,
        )[0]

        self.assertEqual(result["sections"]["hair"], edited_hair)
        self.assertEqual(result["sections"]["expression"], edited_expression)

    def test_assembler_ignores_missing_and_invalid_changes(self):
        character = make_character_dna(seed=99)

        result = RPGCharacterDNAAssembler().assemble(
            character_info=character,
            change_1=None,
            change_2={"not_a_section": True},
            change_3={"id": "not-a-real-section", "values": {"x": 1}},
        )[0]

        self.assertEqual(result, character)


    def test_editor_persistence_transport_is_required_and_serializable(self):
        inputs = RPGCharacterDNAEditor.INPUT_TYPES()
        self.assertIn("edited_section", inputs["required"])

        edited = inputs["required"]["edited_section"]
        self.assertEqual(edited[0], "STRING")
        self.assertNotIn("hidden", edited[1])
        self.assertNotIn("edited_section", inputs.get("optional", {}))


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

    def test_editor_preserves_variant_set_state(self):
        import json

        signature = make_source_signature("clothing", {"clothes_style": "Druidic"})
        source = {
            "id": "clothing",
            "values": {"style": "Druidic"},
            "traits": ["Druidic"],
            "loci": [{
                "id": "clothing:style",
                "label": "Clothing Style",
                "options": ["Druidic"],
                "selected": "Druidic",
                "variant_sets": [{
                    "id": "clothing:style:variant:0",
                    "label": "Variant 1",
                    "options": ["forest green", "moss green", "olive"],
                    "selected": "forest green",
                    "weights": {"0": 1.0},
                    "mode": "random",
                }],
            }],
            "source_signature": signature,
            "source_inputs": {"clothes_style": "Druidic"},
        }
        edited = json.loads(json.dumps(source))
        variant = edited["loci"][0]["variant_sets"][0]
        variant["selected"] = "moss green"
        variant["weights"] = {"0": 0.0008, "1": 0.9983, "2": 0.0009}
        variant["mode"] = "sculpted"

        result = RPGCharacterDNAEditor().edit(
            source, "Edit", 1, json.dumps(edited)
        )["result"][0]

        persisted = result["loci"][0]["variant_sets"][0]
        self.assertEqual(persisted["selected"], "moss green")
        self.assertEqual(persisted["weights"]["1"], 0.9983)
        self.assertEqual(persisted["mode"], "sculpted")
        self.assertEqual(
            persisted["options"],
            ["forest green", "moss green", "olive"],
        )


    def test_editor_preserves_expression_control_values(self):
        import json

        signature = make_source_signature("expression", {"emotion": "Hope"})
        source = {
            "id": "expression",
            "values": {"emotion": "Hope"},
            "traits": ["Hope"],
            "loci": [{
                "id": "expression:emotion",
                "label": "Emotion",
                "options": ["Hope", "Joy"],
                "selected": "Hope",
                "variant_sets": [],
                "controls": {
                    "mouth": {
                        "label": "Mouth",
                        "type": "expression_2d",
                        "x": {"label": "Smile", "min": -1.0, "max": 1.0},
                        "y": {"label": "Open", "min": 0.0, "max": 1.0},
                        "x_value": 0.0,
                        "y_value": 0.0,
                    }
                },
            }],
            "source_signature": signature,
            "source_inputs": {"emotion": "Hope"},
        }
        edited = json.loads(json.dumps(source))
        edited["loci"][0]["controls"]["mouth"]["x_value"] = 0.75
        edited["loci"][0]["controls"]["mouth"]["y_value"] = 0.8

        result = RPGCharacterDNAEditor().edit(
            source, "Edit", 1, json.dumps(edited)
        )["result"][0]

        mouth = result["loci"][0]["controls"]["mouth"]
        self.assertEqual(mouth["x_value"], 0.75)
        self.assertEqual(mouth["y_value"], 0.8)
        self.assertEqual(mouth["x"]["min"], -1.0)
        self.assertEqual(mouth["x"]["max"], 1.0)
        self.assertEqual(mouth["y"]["min"], 0.0)
        self.assertEqual(mouth["y"]["max"], 1.0)
        self.assertEqual(mouth["type"], "expression_2d")


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
