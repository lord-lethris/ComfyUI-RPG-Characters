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
from _rpg_characters_test.gen3.dna.heritage_data import get_heritage
from _rpg_characters_test.gen3.dna.genome import make_genome
from _rpg_characters_test.gen3.nodes.render_intent import RPGCharacterRenderIntent
from _rpg_characters_test.gen3.nodes.art_style import RPGCharacterArtStyle
from _rpg_characters_test.gen3.nodes.model_prompt_adapter import RPGCharacterModelPromptAdapter
from _rpg_characters_test.gen3.render.render_intent import make_render_intent
from _rpg_characters_test.gen3.style.art_style import make_art_style


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
        self.assertIsInstance(dna["genome"], dict)
        self.assertEqual(dna["genome"]["identity"]["lineage"], values["race"])
        expected_heritage = (
            None if str(values["ethnicity"]).strip().lower() == "none"
            else values["ethnicity"]
        )
        self.assertEqual(dna["genome"]["identity"]["heritage"], expected_heritage)

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
        self.assertEqual(genome_a["phenotype"]["body_plan"]["posture"], "bipedal")
        self.assertEqual(genome_a["phenotype"]["body_plan"]["body"], "fully draconic humanoid")
        self.assertEqual(genome_a["phenotype"]["body_plan"]["head"], "fully draconic head")
        self.assertFalse(genome_a["phenotype"]["hair_allowed"])
        self.assertFalse(genome_a["phenotype"]["facial_hair_allowed"])

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

        self.assertIn("anthropomorphic dragon character", positive)
        self.assertIn("bipedal", positive)
        self.assertIn("fully draconic humanoid", positive)
        self.assertIn("fully draconic head", positive)
        self.assertIn("clawed draconic hands", positive)
        self.assertIn("digitigrade clawed feet", positive)
        self.assertIn("long muscular tail", positive)
        self.assertIn("ridged horns", positive)
        self.assertIn("fine scales", positive)
        self.assertNotIn("light to medium skin tone", positive)
        self.assertNotIn("varied features", positive)
        self.assertNotIn("heart-shaped face", positive)
        self.assertNotIn("Pure Human/Fantasy Form", positive)
        self.assertNotIn("bald head", positive)
        self.assertNotIn("No hair", positive)
        self.assertNotIn("No Beard", positive)
        self.assertNotIn("neutral mouth", positive)
        self.assertNotIn("mouth closed", positive)
        self.assertNotIn("has no defined class", positive)
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

    def test_gen3_tiefling_skin_is_first_class_dna(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]
        values = {
            name: options[0][0]
            for name, options in inputs.items()
            if isinstance(options, tuple) and isinstance(options[0], list)
        }
        values["race"] = "Tiefling"
        values["ethnicity"] = "None"
        values["dna_seed"] = 24680

        dna = RPGCharacterGen3().create_character(**values)[0]
        skin_section = dna["sections"]["skin"]
        skin_locus = next(item for item in skin_section["loci"] if item["id"] == "skin:colour")

        self.assertEqual(skin_locus["selected"], "Brick Red")
        self.assertEqual(
            skin_locus["option_prompts"]["Brick Red"],
            "brick-red infernal skin pigmentation",
        )
        self.assertIn("Dark Blue (Variant)", skin_locus["options"])
        self.assertEqual(skin_section["values"]["colour"], "Brick Red")

        positive, negative = RPGCharacterDNAPromptBuilder().build(dna)
        self.assertIn("brick-red infernal skin pigmentation", positive)
        self.assertNotIn("brick-red infernal skin pigmentation", negative)

    def test_gen3_no_beard_ignores_beard_colour_and_blocks_facial_hair(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]
        values = {
            name: options[0][0]
            for name, options in inputs.items()
            if isinstance(options, tuple) and isinstance(options[0], list)
        }
        values["race"] = "Tiefling"
        values["gender"] = "Male"
        values["age"] = "Mid Adult"
        values["beard_style"] = "No Beard"
        values["beard_colour"] = "Ash Blonde"
        values["dna_seed"] = 2468

        dna = RPGCharacterGen3().create_character(**values)[0]
        positive, negative = RPGCharacterDNAPromptBuilder().build(dna)

        beard_colour_locus = next(
            item for item in dna["sections"]["facial_hair"]["loci"]
            if item["id"] == "facial_hair:colour"
        )
        self.assertEqual(beard_colour_locus["selected"], "No Beard")
        self.assertIn("clean-shaven face", positive)
        self.assertIn("no facial hair", positive)
        self.assertNotIn("Ash Blonde Colored", positive)
        self.assertIn("beard", negative.lower())
        self.assertIn("moustache", negative.lower())
        self.assertNotIn("beard", positive.lower())

    def test_gen3_tiefling_uses_human_proportions(self):
        lineage = get_lineage("Tiefling")
        self.assertEqual(
            lineage["body_plan"]["body"],
            "human-proportioned infernal humanoid",
        )
        self.assertEqual(
            lineage["body_plan"]["build"],
            "human-proportioned medium build",
        )
        self.assertEqual(lineage["body_plan"]["tail"], "thick infernal tail")
        self.assertNotIn("dwarf", lineage["negative_prompt"])

    def test_gen3_tiefling_heritage_cannot_override_infernal_eyes(self):
        lineage = get_lineage("Tiefling")
        heritage = get_heritage("British")
        genome = make_genome(
            seed=1357,
            lineage="Tiefling",
            heritage="British",
            gender="Male",
            age="Mid Adult",
            lineage_data=lineage,
            heritage_data=heritage,
        )

        components = genome["phenotype"]["heritage_components"]
        self.assertIn("light to medium skin tone", components["skin"])
        self.assertIn("varied humanoid features", components["facial_features"])
        self.assertEqual(
            components["eyes"],
            "solid infernal eyes with no visible sclera or pupil",
        )
        self.assertNotIn("blue", genome["phenotype"]["heritage"])
        self.assertNotIn("green", genome["phenotype"]["heritage"])
        self.assertNotIn("brown eyes", genome["phenotype"]["heritage"])

    def test_gen3_researched_lineage_aliases_do_not_fall_back_to_human(self):
        for race, expected in (
            ("High Elf", "Elf"),
            ("Wood Elf", "Elf"),
            ("Dark Elf (Drow)", "Elf"),
            ("Hill Dwarf", "Dwarf"),
            ("Mountain Dwarf", "Dwarf"),
            ("Stout Halfling", "Halfling"),
            ("Rock Gnome", "Gnome"),
        ):
            self.assertEqual(
                get_lineage(race)["body_type"],
                get_lineage(expected)["body_type"],
            )

    def test_gen3_elf_disallows_facial_hair(self):
        self.assertFalse(get_lineage("Elf")["body_plan"]["facial_hair_allowed"])
        self.assertFalse(get_lineage("High Elf")["body_plan"]["facial_hair_allowed"])

    def test_gen3_empty_heritage_does_not_render_as_none(self):
        heritage = get_heritage(None)
        self.assertEqual(heritage["label"], "")
        self.assertEqual(heritage["prompt"], "")
        self.assertEqual(heritage["components"], {})

        lineage = get_lineage("Tiefling")
        genome = make_genome(
            seed=4321,
            lineage="Tiefling",
            heritage=None,
            gender="Male",
            age="Elder",
            lineage_data=lineage,
            heritage_data=heritage,
        )

        positive, negative = RPGCharacterDNAPromptBuilder()._render_genome(genome)
        self.assertNotIn("None heritage", positive)
        self.assertNotIn("None heritage", negative)


    def test_gen3_string_none_heritage_is_canonical_empty(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]
        values = {
            name: options[0][0]
            for name, options in inputs.items()
            if isinstance(options, tuple) and isinstance(options[0], list)
        }
        values["race"] = "Tiefling"
        values["ethnicity"] = "None"
        values["age"] = "Mid Adult"
        values["dna_seed"] = 4321

        dna = RPGCharacterGen3().create_character(**values)[0]
        self.assertIsNone(dna["genome"]["identity"]["heritage"])

        positive, negative = RPGCharacterDNAPromptBuilder().build(dna)
        self.assertNotIn("None heritage", positive)
        self.assertNotIn("None heritage", negative)
        self.assertEqual(get_heritage("None")["label"], "")


    def test_gen3_elder_and_ancient_use_non_contradictory_age_semantics(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]

        for age, expected_positive in (
            ("Elder", "as an elderly adult"),
            ("Ancient", "as an ancient adult"),
        ):
            values = {
                name: options[0][0]
                for name, options in inputs.items()
                if isinstance(options, tuple) and isinstance(options[0], list)
            }
            values["race"] = "Tiefling"
            values["ethnicity"] = "None"
            values["gender"] = "Male"
            values["age"] = age
            values["beard_style"] = "No Beard"
            values["dna_seed"] = 24680

            dna = RPGCharacterGen3().create_character(**values)[0]
            positive, negative = RPGCharacterDNAPromptBuilder().build(dna)

            self.assertIn(expected_positive, positive)
            self.assertIn("age lines", positive)
            self.assertNotIn("as an Elder", positive)
            self.assertNotIn("as an Ancient being", positive)
            self.assertNotIn("adult", negative.lower())
            self.assertIn("youthful appearance", negative.lower())


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


    def test_gen3_art_style_preset_is_separate_from_dna(self):
        dna = make_character_dna(seed=1234)
        style = make_art_style("Fantasy Illustration")

        self.assertEqual(style["type"], "RPG_ART_STYLE")
        self.assertEqual(style["source"], "preset")
        self.assertEqual(style["label"], "Fantasy Illustration")
        self.assertIn("fantasy art", style["positive_prompt"])
        self.assertNotIn("art_style", dna)

    def test_gen3_art_style_supports_custom_prompt(self):
        style = make_art_style(
            "Custom",
            custom_positive="watercolour fantasy concept art, ink outlines",
            custom_negative="photorealistic, 3D render",
        )

        self.assertEqual(style["type"], "RPG_ART_STYLE")
        self.assertEqual(style["source"], "custom")
        self.assertEqual(style["id"], "custom")
        self.assertEqual(
            style["positive_prompt"],
            "watercolour fantasy concept art, ink outlines",
        )
        self.assertEqual(
            style["negative_prompt"],
            "photorealistic, 3D render",
        )

    def test_gen3_art_style_node_supports_custom(self):
        options = RPGCharacterArtStyle.INPUT_TYPES()["required"]["art_style"][0]
        self.assertIn("Fantasy Illustration", options)
        self.assertIn("Custom", options)

        style = RPGCharacterArtStyle().create(
            "Custom",
            "storybook gouache fantasy illustration",
            "photorealistic",
        )[0]

        self.assertEqual(style["source"], "custom")
        self.assertIn("storybook gouache", style["positive_prompt"])

    def test_gen3_model_prompt_adapter_translates_for_each_model(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]
        values = {
            name: options[0][0]
            for name, options in inputs.items()
            if isinstance(options, tuple) and isinstance(options[0], list)
        }
        values["race"] = "Tiefling"
        values["gender"] = "Male"
        values["age"] = "Elder"
        values["beard_style"] = "No Beard"
        values["dna_seed"] = 24680

        dna = RPGCharacterGen3().create_character(**values)[0]
        render_intent = make_render_intent("character_portrait")
        style = make_art_style("Fantasy Illustration")
        adapter = RPGCharacterModelPromptAdapter()

        flux_positive, flux_negative = adapter.build(
            dna, render_intent, style, "FLUX"
        )
        sdxl_positive, sdxl_negative = adapter.build(
            dna, render_intent, style, "SDXL"
        )
        z_positive, z_negative = adapter.build(
            dna, render_intent, style, "Z-Image Turbo"
        )
        krea_positive, krea_negative = adapter.build(
            dna, render_intent, style, "Krea 2"
        )

        self.assertEqual(flux_negative, "")
        self.assertIn("clean-shaven face", flux_positive)
        self.assertIn("head-and-shoulders", flux_positive)
        self.assertIn("fantasy art", flux_positive)
        self.assertNotIn("beard", flux_positive.lower())
        self.assertNotIn("moustache", flux_positive.lower())

        self.assertIn("(close-up head-and-shoulders:1.25)", sdxl_positive)
        self.assertIn("(completely clean-shaven face:1.30)", sdxl_positive)
        self.assertTrue(sdxl_negative)
        self.assertIn("beard", sdxl_negative.lower())

        self.assertEqual(z_negative, "")
        self.assertIn("clean-shaven face", z_positive)
        self.assertIn("must not contain", z_positive.lower())

        self.assertEqual(krea_negative, "")
        self.assertIn("clean-shaven face", krea_positive)
        self.assertNotIn("beard", krea_positive.lower())
        self.assertNotIn("moustache", krea_positive.lower())

    def test_gen3_sdxl_tiefling_keeps_race_defining_features(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]
        values = {
            name: options[0][0]
            for name, options in inputs.items()
            if isinstance(options, tuple) and isinstance(options[0], list)
        }
        values["race"] = "Tiefling"
        values["gender"] = "Male"
        values["age"] = "Elder"
        values["beard_style"] = "No Beard"
        values["dna_seed"] = 24680

        dna = RPGCharacterGen3().create_character(**values)[0]
        render_intent = make_render_intent("character_portrait")
        style = make_art_style("Fantasy Illustration")

        positive, negative = RPGCharacterModelPromptAdapter().build(
            dna, render_intent, style, "SDXL"
        )

        self.assertIn("(large curved infernal horns clearly visible:1.35)", positive)
        self.assertIn("brick-red infernal skin pigmentation", positive)
        self.assertIn("(clearly infernal facial features:1.20)", positive)
        self.assertIn(
            "(solid-color infernal eyes with no visible sclera or pupil:1.20)",
            positive,
        )
        self.assertIn("(missing horns:1.35)", negative)
        self.assertIn("(ordinary human appearance:1.20)", negative)
        self.assertIn("(elven appearance:1.20)", negative)
        self.assertIn("(beard:1.35)", negative)
        self.assertIn("(facial hair:1.30)", negative)

    def test_gen3_character_portrait_render_intent_is_separate_from_dna(self):
        dna = make_character_dna(seed=1234)
        intent = make_render_intent("character_portrait")

        self.assertEqual(intent["type"], "RPG_CHARACTER_RENDER_INTENT")
        self.assertEqual(intent["render_intent_version"], 2)
        self.assertEqual(intent["id"], "character_portrait")
        self.assertEqual(intent["composition"]["framing"], "head_and_shoulders")
        self.assertEqual(intent["composition"]["crop"], "upper_chest")
        self.assertEqual(intent["composition"]["subject_count"], 1)
        self.assertEqual(intent["visibility"]["face"], "clear")
        self.assertIn("lower_body", intent["visibility"]["excluded_regions"])
        self.assertEqual(intent["character_constraints"]["facial_hair"], "none")
        self.assertNotIn("render_intent", dna)
        self.assertNotIn("positive_prompt", dna)
        self.assertNotIn("negative_prompt", dna)

    def test_gen3_render_intent_node_returns_character_portrait(self):
        inputs = RPGCharacterRenderIntent.INPUT_TYPES()["required"]["intent"][0]
        self.assertIn("Character Portrait", inputs)

        result = RPGCharacterRenderIntent().create("Character Portrait")[0]

        self.assertEqual(result["type"], "RPG_CHARACTER_RENDER_INTENT")
        self.assertEqual(result["render_intent_version"], 2)
        self.assertEqual(result["id"], "character_portrait")
        self.assertEqual(result["composition"]["framing"], "head_and_shoulders")
        self.assertEqual(result["character_constraints"]["facial_hair"], "none")
        self.assertNotIn("positive_prompt", result)
        self.assertNotIn("negative_prompt", result)

    def test_gen3_prompt_builder_applies_render_intent_without_mutating_dna(self):
        inputs = RPGCharacterGen3.INPUT_TYPES()["required"]
        values = {
            name: options[0][0]
            for name, options in inputs.items()
            if isinstance(options, tuple) and isinstance(options[0], list)
        }
        values["race"] = "Tiefling"
        values["gender"] = "Male"
        values["age"] = "Mid Adult"
        values["beard_style"] = "No Beard"
        values["dna_seed"] = 31415

        dna = RPGCharacterGen3().create_character(**values)[0]
        original_dna = __import__("copy").deepcopy(dna)
        intent = make_render_intent("character_portrait")

        positive_without, negative_without = RPGCharacterDNAPromptBuilder().build(dna)
        positive_with, negative_with = RPGCharacterDNAPromptBuilder().build(
            dna,
            intent,
        )

        self.assertEqual(dna, original_dna)
        self.assertNotIn("head-and-shoulders", positive_without)
        self.assertIn("close-up head-and-shoulders", positive_with)
        self.assertIn("upper chest upward", positive_with)
        self.assertIn("only the head, neck, shoulders and upper chest visible", positive_with)
        self.assertIn("face and head large in frame", positive_with)
        self.assertIn("face is the primary subject", positive_with)
        self.assertIn("full body", negative_with)
        self.assertIn("lower body", negative_with)
        self.assertIn("legs", negative_with)
        self.assertIn("feet", negative_with)
        self.assertIn("beard", negative_with.lower())
        self.assertIn("moustache", negative_with.lower())
        self.assertIn("clean-shaven face", positive_with)
        self.assertEqual(positive_with.count("head-and-shoulders"), 1)

if __name__ == "__main__":
    unittest.main()
