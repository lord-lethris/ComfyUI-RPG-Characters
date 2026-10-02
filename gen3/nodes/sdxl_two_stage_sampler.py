"""Gen 3 SDXL two-stage sampler.

Runs one SDXL sampling schedule with two conditioning phases:
1. Character establishment.
2. Style/scene reinterpretation.

The phases are scheduled on the same denoising trajectory. When overlap is
enabled, both conditioning phases are active during the overlap window with
a linearly changing strength, so the scene conditioning takes over gradually
instead of attempting to resume a latent at an earlier sigma.
"""


class RPGGen3SDXLTwoStageSampler:
    """Run the Gen 3 SDXL two-stage render strategy."""

    DEFAULT_STEPS = 20
    DEFAULT_STAGE1_END = 15
    DEFAULT_OVERLAP = 3
    DEFAULT_CFG = 5.5
    DEFAULT_SAMPLER = "dpmpp_2m_sde"
    DEFAULT_SCHEDULER = "beta"

    @classmethod
    def INPUT_TYPES(cls):
        import comfy.samplers

        return {
            "required": {
                "model": ("MODEL",),
                "positive_stage1": ("CONDITIONING",),
                "negative_stage1": ("CONDITIONING",),
                "positive_stage2": ("CONDITIONING",),
                "negative_stage2": ("CONDITIONING",),
                "latent_image": ("LATENT",),
                "noise_seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xffffffffffffffff,
                        "control_after_generate": True,
                    },
                ),
                "steps": (
                    "INT",
                    {"default": cls.DEFAULT_STEPS, "min": 1, "max": 10000},
                ),
                "cfg": (
                    "FLOAT",
                    {
                        "default": cls.DEFAULT_CFG,
                        "min": 0.0,
                        "max": 100.0,
                        "step": 0.1,
                        "round": 0.01,
                    },
                ),
                "sampler_name": (
                    list(comfy.samplers.KSampler.SAMPLERS),
                    {"default": cls.DEFAULT_SAMPLER},
                ),
                "scheduler": (
                    list(comfy.samplers.KSampler.SCHEDULERS),
                    {"default": cls.DEFAULT_SCHEDULER},
                ),
                "stage1_end_step": (
                    "INT",
                    {
                        "default": cls.DEFAULT_STAGE1_END,
                        "min": 1,
                        "max": 10000,
                        "advanced": True,
                    },
                ),
                "stage2_overlap": (
                    "INT",
                    {
                        "default": cls.DEFAULT_OVERLAP,
                        "min": 0,
                        "max": 10000,
                        "advanced": True,
                    },
                ),
            },
        }

    RETURN_TYPES = ("LATENT",)
    RETURN_NAMES = ("latent",)
    FUNCTION = "sample"
    CATEGORY = "RPG/Gen 3/Sampling"
    DESCRIPTION = (
        "SDXL two-stage Gen 3 sampler: establish the character first, then "
        "reinterpret it through a separate style/scene conditioning pass. "
        "The overlap window transitions conditioning strength on one denoising schedule."
    )

    @classmethod
    def resolve_stage_bounds(cls, steps, stage1_end_step, stage2_overlap):
        """Return validated (stage1_end, stage2_start) schedule bounds.

        These are expressed as sampler-step positions. The actual implementation
        uses the corresponding percentages as conditioning ranges on one sampler
        trajectory, allowing a real overlap without rewinding a latent.
        """
        steps = max(1, int(steps))
        stage1_end = max(1, min(int(stage1_end_step), steps))
        overlap = max(0, min(int(stage2_overlap), stage1_end))
        stage2_start = max(0, stage1_end - overlap)
        return stage1_end, stage2_start

    @classmethod
    def schedule_conditioning(cls, conditioning, start_percent, end_percent, strength=1.0):
        """Apply a sampler timestep range and strength to conditioning entries.

        Existing conditioning ranges are intersected rather than overwritten.
        Existing strength is multiplied by the requested phase strength so this
        remains composable with conditioning that already has a strength.
        """
        start_percent = max(0.0, min(float(start_percent), 1.0))
        end_percent = max(0.0, min(float(end_percent), 1.0))
        strength = max(0.0, float(strength))

        if start_percent > end_percent:
            raise ValueError("conditioning start_percent must not exceed end_percent")

        scheduled = []
        for entry in conditioning:
            cond, metadata = entry
            metadata = metadata.copy()

            existing_start = float(metadata.get("start_percent", 0.0))
            existing_end = float(metadata.get("end_percent", 1.0))

            intersection_start = max(start_percent, existing_start)
            intersection_end = min(end_percent, existing_end)

            if intersection_start >= intersection_end or strength == 0.0:
                continue

            metadata["start_percent"] = intersection_start
            metadata["end_percent"] = intersection_end
            metadata["strength"] = float(metadata.get("strength", 1.0)) * strength
            scheduled.append([cond, metadata])

        return scheduled

    @classmethod
    def build_phase_schedule(
        cls,
        conditioning,
        steps,
        stage1_end,
        stage2_start,
        phase,
    ):
        """Build a phase schedule with a linear strength hand-off.

        Stage 1 has full strength before the overlap and fades out linearly.
        Stage 2 has full strength after the overlap and fades in linearly.
        During the overlap, the two phases therefore trade influence rather
        than being averaged at a fixed 50/50 ratio.
        """
        steps = max(1, int(steps))
        stage1_end = int(stage1_end)
        stage2_start = int(stage2_start)
        overlap = max(0, stage1_end - stage2_start)

        scheduled = []

        if phase == 1:
            if stage2_start > 0:
                scheduled.extend(
                    cls.schedule_conditioning(
                        conditioning,
                        0.0,
                        stage2_start / steps,
                        strength=1.0,
                    )
                )

            for offset in range(overlap):
                start_step = stage2_start + offset
                end_step = start_step + 1
                strength = (overlap - offset) / overlap
                scheduled.extend(
                    cls.schedule_conditioning(
                        conditioning,
                        start_step / steps,
                        end_step / steps,
                        strength=strength,
                    )
                )

            if stage2_start == stage1_end:
                # Zero-overlap case: Stage 1 still owns the complete first phase.
                scheduled.extend(
                    cls.schedule_conditioning(
                        conditioning,
                        0.0,
                        stage1_end / steps,
                        strength=1.0,
                    )
                )
        elif phase == 2:
            for offset in range(overlap):
                start_step = stage2_start + offset
                end_step = start_step + 1
                strength = (offset + 1) / overlap
                scheduled.extend(
                    cls.schedule_conditioning(
                        conditioning,
                        start_step / steps,
                        end_step / steps,
                        strength=strength,
                    )
                )

            if stage1_end < steps:
                scheduled.extend(
                    cls.schedule_conditioning(
                        conditioning,
                        stage1_end / steps,
                        1.0,
                        strength=1.0,
                    )
                )

            if overlap == 0:
                scheduled.extend(
                    cls.schedule_conditioning(
                        conditioning,
                        stage1_end / steps,
                        1.0,
                        strength=1.0,
                    )
                )
        else:
            raise ValueError("phase must be 1 or 2")

        return scheduled

    @classmethod
    def build_conditioning_schedule(
        cls,
        positive_stage1,
        negative_stage1,
        positive_stage2,
        negative_stage2,
        steps,
        stage1_end_step,
        stage2_overlap,
    ):
        """Build weighted positive/negative conditioning schedules."""
        stage1_end, stage2_start = cls.resolve_stage_bounds(
            steps,
            stage1_end_step,
            stage2_overlap,
        )

        positive = cls.build_phase_schedule(
            positive_stage1,
            steps,
            stage1_end,
            stage2_start,
            phase=1,
        )
        positive.extend(
            cls.build_phase_schedule(
                positive_stage2,
                steps,
                stage1_end,
                stage2_start,
                phase=2,
            )
        )

        negative = cls.build_phase_schedule(
            negative_stage1,
            steps,
            stage1_end,
            stage2_start,
            phase=1,
        )
        negative.extend(
            cls.build_phase_schedule(
                negative_stage2,
                steps,
                stage1_end,
                stage2_start,
                phase=2,
            )
        )

        return positive, negative, stage1_end, stage2_start

    def sample(
        self,
        model,
        positive_stage1,
        negative_stage1,
        positive_stage2,
        negative_stage2,
        latent_image,
        noise_seed,
        steps,
        cfg,
        sampler_name,
        scheduler,
        stage1_end_step,
        stage2_overlap,
    ):
        import comfy.sample
        import comfy.utils

        positive, negative, stage1_end, stage2_start = (
            self.build_conditioning_schedule(
                positive_stage1,
                negative_stage1,
                positive_stage2,
                negative_stage2,
                steps,
                stage1_end_step,
                stage2_overlap,
            )
        )

        latent = dict(latent_image)
        latent_samples = comfy.sample.fix_empty_latent_channels(
            model,
            latent["samples"],
        )

        batch_inds = latent.get("batch_index")
        noise = comfy.sample.prepare_noise(
            latent_samples,
            noise_seed,
            batch_inds,
        )

        noise_mask = latent.get("noise_mask")
        disable_pbar = not comfy.utils.PROGRESS_BAR_ENABLED

        # Both phases run on one sampler trajectory. Stage 1 is active from
        # 0 -> stage1_end; Stage 2 is active from stage2_start -> 1.
        # During the overlap their strength changes linearly from:
        #
        #   Stage 1 100% / Stage 2   0%
        #   Stage 1  75% / Stage 2  25%
        #   Stage 1  50% / Stage 2  50%
        #   Stage 1  25% / Stage 2  75%
        #   Stage 1   0% / Stage 2 100%
        #
        # for a 3-step overlap. ComfyUI's conditioning aggregator applies the
        # strength values while normalising the combined prediction.
        samples = comfy.sample.sample(
            model,
            noise,
            steps,
            cfg,
            sampler_name,
            scheduler,
            positive,
            negative,
            latent_samples,
            denoise=1.0,
            disable_noise=False,
            start_step=0,
            last_step=steps,
            force_full_denoise=True,
            noise_mask=noise_mask,
            callback=None,
            disable_pbar=disable_pbar,
            seed=noise_seed,
        )

        result = {"samples": samples}
        if "batch_index" in latent:
            result["batch_index"] = latent["batch_index"]
        return (result,)


NODE_CLASS_MAPPINGS = {
    "RPGGen3SDXLTwoStageSampler": RPGGen3SDXLTwoStageSampler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGGen3SDXLTwoStageSampler": "SDXL Two-Stage Sampler (Gen 3)",
}
