"""Tests for the Gen 3 SDXL two-stage sampler scheduling."""

import unittest

from gen3.nodes.sdxl_two_stage_sampler import RPGGen3SDXLTwoStageSampler


class TestGen3SDXLTwoStageSampler(unittest.TestCase):
    def _conditioning(self, label, metadata=None):
        return [[label, dict(metadata or {})]]

    def test_resolve_stage_bounds_preserves_nominal_end_and_calculates_overlap_start(self):
        stage1_end, stage2_start = RPGGen3SDXLTwoStageSampler.resolve_stage_bounds(
            20, 15, 3
        )
        self.assertEqual(stage1_end, 15)
        self.assertEqual(stage2_start, 12)

    def test_resolve_stage_bounds_clamps_overlap_to_stage1_end(self):
        stage1_end, stage2_start = RPGGen3SDXLTwoStageSampler.resolve_stage_bounds(
            20, 15, 99
        )
        self.assertEqual(stage1_end, 15)
        self.assertEqual(stage2_start, 0)

    def test_build_conditioning_schedule_creates_real_overlap(self):
        positive_stage1 = self._conditioning("character")
        negative_stage1 = self._conditioning("character-negative")
        positive_stage2 = self._conditioning("scene")
        negative_stage2 = self._conditioning("scene-negative")

        positive, negative, stage1_end, stage2_start = (
            RPGGen3SDXLTwoStageSampler.build_conditioning_schedule(
                positive_stage1,
                negative_stage1,
                positive_stage2,
                negative_stage2,
                20,
                15,
                3,
            )
        )

        self.assertEqual((stage1_end, stage2_start), (15, 12))
        self.assertEqual(
            [(item[0], item[1]["start_percent"], item[1]["end_percent"]) for item in positive],
            [("character", 0.0, 0.75), ("scene", 0.6, 1.0)],
        )
        self.assertEqual(
            [(item[0], item[1]["start_percent"], item[1]["end_percent"]) for item in negative],
            [("character-negative", 0.0, 0.75), ("scene-negative", 0.6, 1.0)],
        )

    def test_zero_overlap_has_adjacent_ranges(self):
        positive, negative, _, _ = RPGGen3SDXLTwoStageSampler.build_conditioning_schedule(
            self._conditioning("character"),
            self._conditioning("character-negative"),
            self._conditioning("scene"),
            self._conditioning("scene-negative"),
            20,
            15,
            0,
        )

        self.assertEqual(positive[0][1]["end_percent"], 0.75)
        self.assertEqual(positive[1][1]["start_percent"], 0.75)
        self.assertEqual(negative[0][1]["end_percent"], 0.75)
        self.assertEqual(negative[1][1]["start_percent"], 0.75)

    def test_existing_conditioning_range_is_intersected(self):
        positive, _, _, _ = RPGGen3SDXLTwoStageSampler.build_conditioning_schedule(
            self._conditioning("character", {"start_percent": 0.2, "end_percent": 0.9}),
            self._conditioning("negative"),
            self._conditioning("scene", {"start_percent": 0.1, "end_percent": 0.8}),
            self._conditioning("negative-scene"),
            20,
            15,
            3,
        )

        self.assertEqual(
            [(item[0], item[1]["start_percent"], item[1]["end_percent"]) for item in positive],
            [("character", 0.2, 0.75), ("scene", 0.6, 0.8)],
        )


if __name__ == "__main__":
    unittest.main()
