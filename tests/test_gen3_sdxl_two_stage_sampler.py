"""Tests for the Gen 3 SDXL two-stage sampler scheduling."""

import unittest

from gen3.nodes.sdxl_two_stage_sampler import RPGGen3SDXLTwoStageSampler


class TestGen3SDXLTwoStageSampler(unittest.TestCase):
    def _conditioning(self, label, metadata=None):
        return [[label, dict(metadata or {})]]

    def _schedule(self, conditioning, steps=20, stage1_end=15, overlap=3):
        return RPGGen3SDXLTwoStageSampler.build_conditioning_schedule(
            conditioning,
            self._conditioning("character-negative"),
            self._conditioning("scene"),
            self._conditioning("scene-negative"),
            steps,
            stage1_end,
            overlap,
        )[0]

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

    def test_build_conditioning_schedule_creates_weighted_overlap(self):
        positive, negative, stage1_end, stage2_start = (
            RPGGen3SDXLTwoStageSampler.build_conditioning_schedule(
                self._conditioning("character"),
                self._conditioning("character-negative"),
                self._conditioning("scene"),
                self._conditioning("scene-negative"),
                20,
                15,
                3,
            )
        )

        self.assertEqual((stage1_end, stage2_start), (15, 12))

        positive_ranges = [
            (item[0], item[1]["start_percent"], item[1]["end_percent"], item[1]["strength"])
            for item in positive
        ]
        self.assertEqual(
            positive_ranges,
            [
                ("character", 0.0, 0.6, 1.0),
                ("character", 0.6, 0.65, 1.0),
                ("character", 0.65, 0.7, 2 / 3),
                ("character", 0.7, 0.75, 1 / 3),
                ("scene", 0.6, 0.65, 1 / 3),
                ("scene", 0.65, 0.7, 2 / 3),
                ("scene", 0.7, 0.75, 1.0),
                ("scene", 0.75, 1.0, 1.0),
            ],
        )

        negative_ranges = [
            (item[0], item[1]["start_percent"], item[1]["end_percent"], item[1]["strength"])
            for item in negative
        ]
        self.assertEqual(
            negative_ranges,
            [
                ("character-negative", 0.0, 0.6, 1.0),
                ("character-negative", 0.6, 0.65, 1.0),
                ("character-negative", 0.65, 0.7, 2 / 3),
                ("character-negative", 0.7, 0.75, 1 / 3),
                ("scene-negative", 0.6, 0.65, 1 / 3),
                ("scene-negative", 0.65, 0.7, 2 / 3),
                ("scene-negative", 0.7, 0.75, 1.0),
                ("scene-negative", 0.75, 1.0, 1.0),
            ],
        )

    def test_weighted_overlap_uses_complementary_strengths(self):
        positive, _, _, _ = RPGGen3SDXLTwoStageSampler.build_conditioning_schedule(
            self._conditioning("character"),
            self._conditioning("negative"),
            self._conditioning("scene"),
            self._conditioning("negative-scene"),
            20,
            15,
            3,
        )

        overlap = positive[1:7]
        pairs = list(zip(overlap[1:4], overlap[4:7]))

        for character_entry, scene_entry in pairs:
            self.assertAlmostEqual(
                character_entry[1]["strength"] + scene_entry[1]["strength"],
                1.0,
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

        self.assertEqual(
            [(item[0], item[1]["start_percent"], item[1]["end_percent"]) for item in positive],
            [("character", 0.0, 0.75), ("scene", 0.75, 1.0)],
        )
        self.assertEqual(
            [(item[0], item[1]["start_percent"], item[1]["end_percent"]) for item in negative],
            [("character-negative", 0.0, 0.75), ("scene-negative", 0.75, 1.0)],
        )

    def test_existing_conditioning_range_and_strength_are_composed(self):
        positive, _, _, _ = RPGGen3SDXLTwoStageSampler.build_conditioning_schedule(
            self._conditioning(
                "character",
                {"start_percent": 0.2, "end_percent": 0.9, "strength": 0.5},
            ),
            self._conditioning("negative"),
            self._conditioning(
                "scene",
                {"start_percent": 0.1, "end_percent": 0.8, "strength": 0.5},
            ),
            self._conditioning("negative-scene"),
            20,
            15,
            3,
        )

        self.assertEqual(
            [
                (item[0], item[1]["start_percent"], item[1]["end_percent"], item[1]["strength"])
                for item in positive
            ],
            [
                ("character", 0.2, 0.6, 0.5),
                ("character", 0.6, 0.65, 0.5),
                ("character", 0.65, 0.7, 1 / 3),
                ("character", 0.7, 0.75, 1 / 6),
                ("scene", 0.6, 0.65, 1 / 6),
                ("scene", 0.65, 0.7, 1 / 3),
                ("scene", 0.7, 0.75, 0.5),
                ("scene", 0.75, 0.8, 0.5),
            ],
        )


if __name__ == "__main__":
    unittest.main()
