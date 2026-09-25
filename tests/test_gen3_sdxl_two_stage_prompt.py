"""Tests for the Gen 3 SDXL two-stage prompt adapter."""

import sys
import types
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PACKAGE_NAME = "_rpg_characters_test"
_test_package = types.ModuleType(_PACKAGE_NAME)
_test_package.__path__ = [str(_REPO_ROOT)]
sys.modules.setdefault(_PACKAGE_NAME, _test_package)

from _rpg_characters_test.gen3.nodes.art_style import RPGCharacterArtStyle
from _rpg_characters_test.gen3.nodes.character_gen3_node import RPGCharacterGen3
from _rpg_characters_test.gen3.nodes.render_intent import RPGCharacterRenderIntent
from _rpg_characters_test.gen3.nodes.sdxl_two_stage_prompt_adapter import (
    RPGCharacterSDXLTwoStagePromptAdapter,
)


class TestGen3SDXLTwoStagePromptAdapter(unittest.TestCase):
    def _make_inputs(self):
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
        values["scene"] = "Medieval Market"
        values["dna_seed"] = 24680
        return values

    def test_sdxl_two_stage_prompt_separates_scene_from_character_establishment(self):
        dna = RPGCharacterGen3().create_character(**self._make_inputs())[0]
        render_intent = RPGCharacterRenderIntent().create("Character Portrait")[0]
        style = RPGCharacterArtStyle().create("Fantasy Illustration")[0]

        result = RPGCharacterSDXLTwoStagePromptAdapter().build(
            dna,
            render_intent,
            style,
        )

        self.assertEqual(len(result), 4)
        stage1_positive, stage1_negative, stage2_positive, stage2_negative = result

        # Stage 1 establishes the character and must not receive Scene DNA.
        self.assertNotIn("medieval fantasy marketplace", stage1_positive.lower())
        self.assertNotIn("secondary background environment", stage1_positive.lower())
        self.assertIn("tiefling", stage1_positive.lower())
        self.assertIn("clean-shaven", stage1_positive.lower())
        self.assertIn("horn", stage1_positive.lower())

        # Stage 2 reinterprets the established character through style + scene.
        self.assertIn("fantasy art", stage2_positive.lower())
        self.assertIn("medieval fantasy marketplace", stage2_positive.lower())
        self.assertIn("secondary background environment", stage2_positive.lower())
        self.assertIn("same character remains the primary subject", stage2_positive.lower())

        # Both stages retain the important anti-collapse constraints.
        self.assertIn("beard", stage1_negative.lower())
        self.assertIn("beard", stage2_negative.lower())
        self.assertIn("missing horns", stage1_negative.lower())
        self.assertIn("missing horns", stage2_negative.lower())

    def test_sdxl_two_stage_prompt_keeps_art_style_out_of_stage1(self):
        dna = RPGCharacterGen3().create_character(**self._make_inputs())[0]
        render_intent = RPGCharacterRenderIntent().create("Character Portrait")[0]
        style = RPGCharacterArtStyle().create("K-Pop Demon Hunters")[0]

        stage1_positive, _, stage2_positive, _ = (
            RPGCharacterSDXLTwoStagePromptAdapter().build(
                dna,
                render_intent,
                style,
            )
        )

        self.assertNotIn("k-pop-inspired fantasy design", stage1_positive.lower())
        self.assertIn("k-pop-inspired fantasy design", stage2_positive.lower())


if __name__ == "__main__":
    unittest.main()
