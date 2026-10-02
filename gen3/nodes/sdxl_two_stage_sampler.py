"""Gen 3 SDXL two-stage sampler.

Runs one SDXL sampling schedule with two conditioning phases:
1. Character establishment.
2. Style/scene reinterpretation.

The phases are scheduled on the same denoising trajectory. When overlap is
enabled, both conditioning phases are active during the overlap window, so
ComfyUI blends their predictions instead of attempting to resume a latent at
an earlier sigma than the latent actually represents.
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
        "The overlap window blends both conditioning phases on one denoising schedule."
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
    def schedule_conditioning(cls, conditioning, start_percent, end_percent):
        """Apply a sampler timestep range to every conditioning entry.

        Existing conditioning ranges are intersected rather than overwritten.
        This keeps the node composable with conditioning that is already
        scheduled by another node.
        """
        start_percent = max(0.0, min(float(start_percent), 1.0))
        end_percent = max(0.0, min(float(end_percent), 1.0))

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

            if intersection_start >= intersection_end:
                continue

            metadata["start_percent"] = intersection_start
            metadata["end_percent"] = intersection_end
            scheduled.append([cond, metadata])

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
        """Build positive/negative conditioning schedules for both phases."""
        stage1_end, stage2_start = cls.resolve_stage_bounds(
            steps,
            stage1_end_step,
            stage2_overlap,
        )

        stage1_end_percent = stage1_end / max(1, int(steps))
        stage2_start_percent = stage2_start / max(1, int(steps))

        positive = cls.schedule_conditioning(
            positive_stage1,
            0.0,
            stage1_end_percent,
        )
        positive.extend(
            cls.schedule_conditioning(
                positive_stage2,
                stage2_start_percent,
                1.0,
            )
        )

        negative = cls.schedule_conditioning(
            negative_stage1,
            0.0,
            stage1_end_percent,
        )
        negative.extend(
            cls.schedule_conditioning(
                negative_stage2,
                stage2_start_percent,
                1.0,
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
        # 0 -> stage1_end; Stage 2 is active from stage2_start -> 1. During
        # the overlap window both are evaluated by ComfyUI and their outputs
        # are combined. This avoids the invalid operation of asking a sampler
        # to start at an earlier sigma than the supplied latent represents.
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
