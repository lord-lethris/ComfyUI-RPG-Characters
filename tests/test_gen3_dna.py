"""Smoke tests for the Gen 3 structured DNA contract.

Run from the repository root with:
    python -m unittest discover -s tests -p "test_gen3*.py"
"""

import unittest

from gen3.dna.character_dna import (
    CHARACTER_DNA_VERSION,
    make_character_dna,
)
from gen3.dna.dna_schema import DNA_SECTIONS
from gen3.nodes.dna_editor import RPGCharacterDNAEditor
from gen3.nodes.dna_pipe import RPGCharacterDNAPipe


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
        self.assertTrue(outputs[identity_index]["loci"])
        self.assertEqual(outputs[hair_index]["loci"][0]["id"], "hair:style")

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
            "hair",
            "Pass Through",
        )[0]

        self.assertEqual(result["id"], "hair")
        self.assertEqual(result["values"]["colour"], "Black")

    def test_editor_clear_returns_empty_valid_section(self):
        section = {
            "id": "hair",
            "values": {"colour": "Black"},
        }

        result = RPGCharacterDNAEditor().edit(
            section,
            "hair",
            "Clear",
        )[0]

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
        }

        import json
        result = RPGCharacterDNAEditor().edit(
            {},
            "hair",
            "Edit",
            1,
            json.dumps(section),
        )[0]

        self.assertEqual(result["id"], "hair")
        self.assertEqual(result["loci"][0]["selected"], "White")
        self.assertEqual(result["loci"][0]["weights"]["1"], 0.75)

if __name__ == "__main__":
    unittest.main()
