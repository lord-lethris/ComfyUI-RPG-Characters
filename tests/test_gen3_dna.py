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
from _rpg_characters_test.gen3.nodes.dna_prompt_builder import RPGCharacterDNAPromptBuilder
from _rpg_characters_test.gen3.dna.face_data import FACE_LOCUS_DATA
from _rpg_characters_test.gen3.dna.lineage_data import get_lineage
from _rpg_characters_test.gen3.dna.genome import make_genome


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
        self.assertTrue(all(key in clothing for key in DNA_LOCUS_KEYS))
        self.assertGreaterEqual(len(clothing["variant_sets"]), 2)
        self.assertEqual(
            clothing["variant_sets"][0]["options"],
            ["forest green", "moss green", "olive", "brown", "tan", "dark grey"],
        )
        self.assertEqual(
            clothing["variant_sets"][1]["options"],
            ["brown leather", "woven hemp", "wooden", "bronze"],
        )

        for variant in clothing["variant_sets"]:
            self.assertTrue(all(key in variant for key in DNA_VARIANT_SET_KEYS))

        expression = dna["sections"]["expression"]["loci"][0]
        self.assertIn("controls", expression)
        mouth = expression["controls"]["mouth"]
        self.assertEqual(mouth["type"], "expression_2d")
        self.assertEqual(mouth["x_value"], 0.0)
        self.assertEqual(mouth["y_value"], 0.0)

    def test_gen3_face_section_is_structured_and_deterministic(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]
        values = {
            name: options[0][0]
            for name, options in inputs.items()
            if isinstance(options, tuple) and isinstance(options[0], list)
        }
        values["dna_seed"] = 1234

        first = RPGCharacterGen3().create_character(**values)[0]
        second = RPGCharacterGen3().create_character(**values)[0]

        face = first["sections"]["face"]
        self.assertEqual(face, second["sections"]["face"])
        self.assertEqual(len(face["loci"]), len(FACE_LOCUS_DATA))
        self.assertEqual(set(face["values"]), set(FACE_LOCUS_DATA))

        for locus in face["loci"]:
            locus_id = locus["id"].split(":", 1)[1]
            self.assertIn(locus_id, FACE_LOCUS_DATA)
            self.assertIn(locus["selected"], locus["options"])
            self.assertTrue(locus["option_prompts"][locus["selected"]])
            self.assertEqual(locus["variant_sets"], [])
            self.assertTrue(all(key in locus for key in DNA_LOCUS_KEYS))

    def test_gen3_face_source_changes_with_identity_context(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]
        values = {
            name: options[0][0]
            for name, options in inputs.items()
            if isinstance(options, tuple) and isinstance(options[0], list)
        }
        values["dna_seed"] = 1234

        first = RPGCharacterGen3().create_character(**values)[0]
        values["gender"] = inputs["gender"][0][1]
        second = RPGCharacterGen3().create_character(**values)[0]

        self.assertEqual(
            first["sections"]["hair"]["source_signature"],
            second["sections"]["hair"]["source_signature"],
        )
        self.assertNotEqual(
            first["sections"]["face"]["source_signature"],
            second["sections"]["face"]["source_signature"],
        )

    def test_gen3_variant_labels_describe_prompt_context(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]
        values = {
            name: options[0][0]
            for name, options in inputs.items()
            if isinstance(options, tuple) and isinstance(options[0], list)
        }
        values["dna_seed"] = 1234
        values["ethnicity"] = "British"

        dna = RPGCharacterGen3().create_character(**values)[0]
        ethnicity = dna["sections"]["identity"]["loci"][1]
        variant = ethnicity["variant_sets"][0]

        self.assertEqual(variant["label"], "Eye Colour")
        self.assertEqual(variant["options"], ["blue", "green", "brown"])

    def test_gen3_loci_include_source_prompt_mappings(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]
        values = {
            name: options[0][0]
            for name, options in inputs.items()
            if isinstance(options, tuple) and isinstance(options[0], list)
        }
        values["dna_seed"] = 1234

        dna = RPGCharacterGen3().create_character(**values)[0]
        hair = dna["sections"]["hair"]["loci"][0]

        self.assertIn("option_prompts", hair)
        self.assertIn(values["hair_style"], hair["option_prompts"])
        self.assertTrue(hair["option_prompts"][values["hair_style"]])

    def test_prompt_builder_resolves_selected_values_and_variants(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]
        values = {
            name: options[0][0]
            for name, options in inputs.items()
            if isinstance(options, tuple) and isinstance(options[0], list)
        }
        values["dna_seed"] = 1234
        values["hair_style"] = "Afro"

        dna = RPGCharacterGen3().create_character(**values)[0]
        hair = dna["sections"]["hair"]["loci"][0]
        hair["variant_sets"][0]["selected"] = "large"
        hair["variant_sets"][1]["selected"] = "softly textured"

        original = __import__("copy").deepcopy(dna)
        positive, negative = RPGCharacterDNAPromptBuilder().build(dna)

        self.assertIn("large Afro hair", positive)
        self.assertIn("softly textured", positive)
        self.assertEqual(dna, original)
        self.assertIsInstance(negative, str)

    def test_prompt_builder_renders_sculpted_variant_weights(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]
        values = {
            name: options[0][0]
            for name, options in inputs.items()
            if isinstance(options, tuple) and isinstance(options[0], list)
        }
        values["dna_seed"] = 1234
        values["clothes_style"] = "AD&D - Mage Robes"

        dna = RPGCharacterGen3().create_character(**values)[0]
        clothing = dna["sections"]["clothing"]["loci"][0]

        first_variant = clothing["variant_sets"][0]
        first_variant["selected"] = "green"
        first_variant["weights"] = {
            "1": 0.22433293215117625,
            "5": 0.23202471900969102,
            "6": 0.5436423488391326,
        }
        first_variant["mode"] = "sculpted"

        second_variant = clothing["variant_sets"][1]
        second_variant["selected"] = "gold"
        second_variant["weights"] = {"0": 1.0}
        second_variant["mode"] = "random"

        original = __import__("copy").deepcopy(dna)
        positive, negative = RPGCharacterDNAPromptBuilder().build(dna)

        self.assertIn("(silver:0.224)", positive)
        self.assertIn("(blue:0.232)", positive)
        self.assertIn("(green:0.544)", positive)
        self.assertIn("gold embroidered fabric and sash", positive)
        self.assertNotIn("wearing green flowing fantasy mage robes", positive)
        self.assertEqual(dna, original)
        self.assertIsInstance(negative, str)

    def test_prompt_builder_renders_expression_control_descriptors(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]
        values = {
            name: options[0][0]
            for name, options in inputs.items()
            if isinstance(options, tuple) and isinstance(options[0], list)
        }
        values["dna_seed"] = 1234
        values["emotion"] = "Hope"

        dna = RPGCharacterGen3().create_character(**values)[0]
        expression = dna["sections"]["expression"]["loci"][0]
        mouth = expression["controls"]["mouth"]
        mouth["x_value"] = 0.973
        mouth["y_value"] = 0.809

        original = __import__("copy").deepcopy(dna)
        positive, negative = RPGCharacterDNAPromptBuilder().build(dna)

        self.assertIn("showing the expression of Hope", positive)
        self.assertIn("broad smile", positive)
        self.assertIn("mouth wide open", positive)
        self.assertEqual(dna, original)
        self.assertIsInstance(negative, str)

    def test_prompt_builder_falls_back_to_selected_value(self):
        dna = make_character_dna(
            sections={
                "pose": {
                    "values": {},
                    "traits": [],
                    "loci": [{
                        "id": "pose:test",
                        "label": "Pose",
                        "options": ["heroic stance"],
                        "selected": "heroic stance",
                        "variant_sets": [],
                        "controls": {},
                    }],
                },
            },
        )

        positive, negative = RPGCharacterDNAPromptBuilder().build(dna)

        self.assertEqual(positive, "heroic stance")
        self.assertEqual(negative, "")


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

    def test_gen3_genome_is_deterministic_and_persistent(self):
        lineage = get_lineage("Dragon")
        genome_a = make_genome(
            seed=1234,
            lineage="Dragon",
            heritage="British",
            gender="Male",
            age="Elder",
            lineage_data=lineage,
            heritage_data={"phenotype_prompt": "human features"},
        )
        genome_b = make_genome(
            seed=1234,
            lineage="Dragon",
            heritage="British",
            gender="Male",
            age="Elder",
            lineage_data=lineage,
            heritage_data={"phenotype_prompt": "human features"},
        )

        self.assertEqual(genome_a, genome_b)
        self.assertEqual(genome_a["identity"]["lineage"], "Dragon")
        self.assertFalse(genome_a["identity"]["heritage_compatible"])
        self.assertTrue(genome_a["species_traits"]["horns"]["present"])
        self.assertTrue(genome_a["species_traits"]["tail"]["present"])
        self.assertTrue(genome_a["species_traits"]["wings"]["present"])
        self.assertTrue(genome_a["species_traits"]["scales"]["present"])

    def test_gen3_dragon_prompt_does_not_inherit_human_heritage_morphology(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]
        values = {
            name: options[0][0]
            for name, options in inputs.items()
            if isinstance(options, tuple) and isinstance(options[0], list)
        }
        values["race"] = "Dragon"
        values["ethnicity"] = "British"
        values["gender"] = "Male"
        values["age"] = "Elder"
        values["dna_seed"] = 1234

        dna = RPGCharacterGen3().create_character(**values)[0]
        positive, negative = RPGCharacterDNAPromptBuilder().build(dna)

        self.assertIn("sapient dragon", positive)
        self.assertIn("with horns", positive)
        self.assertIn("with tail", positive)
        self.assertIn("with wings", positive)
        self.assertIn("with scales", positive)
        self.assertNotIn("light to medium skin tone", positive)
        self.assertNotIn("varied features", positive)
        self.assertNotIn("heart-shaped face", positive)
        self.assertNotIn("Pure Human/Fantasy Form", positive)
        self.assertIn("human face", negative)

    def test_gen3_tiefling_genome_requires_horns_and_tail(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]
        values = {
            name: options[0][0]
            for name, options in inputs.items()
            if isinstance(options, tuple) and isinstance(options[0], list)
        }
        values["race"] = "Tiefling"
        values["dna_seed"] = 9876

        dna = RPGCharacterGen3().create_character(**values)[0]
        genome = dna["genome"]

        self.assertEqual(genome["identity"]["lineage"], "Tiefling")
        self.assertTrue(genome["species_traits"]["horns"]["present"])
        self.assertTrue(genome["species_traits"]["tail"]["present"])
        self.assertTrue(genome["species_traits"]["horn_type"])
        self.assertTrue(genome["species_traits"]["tail_type"])

    def test_gen3_incompatible_heritage_is_cultural_only(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]
        values = {
            name: options[0][0]
            for name, options in inputs.items()
            if isinstance(options, tuple) and isinstance(options[0], list)
        }
        values["race"] = "Dragon"
        values["ethnicity"] = "Japanese"
        values["dna_seed"] = 2222

        dna = RPGCharacterGen3().create_character(**values)[0]
        genome = dna["genome"]

        self.assertFalse(genome["identity"]["heritage_compatible"])
        self.assertEqual(genome["phenotype"]["heritage"], "")

if __name__ == "__main__":
    unittest.main()
