"""Tests for the Gen 3 SDXL one-prompt/two-step workflow."""

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
from _rpg_characters_test.gen3.nodes.sdxl_two_stage_sampler import (
    RPGGen3SDXLTwoStageSampler,
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

    def test_sdxl_adapter_builds_one_complete_prompt(self):
        dna = RPGCharacterGen3().create_character(**self._make_inputs())[0]
        render_intent = RPGCharacterRenderIntent().create("Character Portrait")[0]
        style = RPGCharacterArtStyle().create("Fantasy Illustration")[0]

        positive, negative = RPGCharacterSDXLTwoStagePromptAdapter().build(
            dna,
            render_intent,
            style,
        )

        self.assertIsInstance(positive, str)
        self.assertIsInstance(negative, str)
        self.assertTrue(positive)
        self.assertTrue(negative)

        prompt = positive.lower()

        # Character identity remains in the SAME prompt as the scene.
        self.assertIn("tiefling", prompt)
        self.assertIn("horn", prompt)
        self.assertIn("fantasy art", prompt)
        self.assertIn("medieval fantasy marketplace", prompt)

        # Scene is explicitly environmental context rather than a second subject.
        self.assertIn("secondary background environment", prompt)
        self.assertIn("background environment", prompt)

        # The SDXL race anchors remain part of the single prompt.
        self.assertIn("distinctive tiefling appearance", prompt)
        self.assertIn("large curved infernal horns clearly visible", prompt)

        # The hard anti-collapse constraints remain in the negative prompt.
        self.assertIn("missing horns", negative.lower())
        self.assertIn("beard", negative.lower())

    def test_sdxl_two_step_uses_one_conditioning_pair(self):
        inputs = RPGGen3SDXLTwoStageSampler.INPUT_TYPES

        # INPUT_TYPES imports ComfyUI's sampler lists, so skip this structural
        # assertion when ComfyUI is not available in the test environment.
        try:
            required = inputs()["required"]
        except ModuleNotFoundError:
            self.skipTest("ComfyUI is not installed in the unit-test environment.")

        self.assertIn("positive", required)
        self.assertIn("negative", required)
        self.assertNotIn("positive_stage1", required)
        self.assertNotIn("negative_stage1", required)
        self.assertNotIn("positive_stage2", required)
        self.assertNotIn("negative_stage2", required)

    def test_stage_bounds_preserve_v2_style_overlap(self):
        self.assertEqual(
            RPGGen3SDXLTwoStageSampler.resolve_stage_bounds(20, 15, 3),
            (15, 12),
        )
        self.assertEqual(
            RPGGen3SDXLTwoStageSampler.resolve_stage_bounds(8, 4, 2),
            (4, 2),
        )


if __name__ == "__main__":
    unittest.main()
