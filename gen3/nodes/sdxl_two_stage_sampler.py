"""Gen 3 SDXL two-step sampler.

Runs one ComfyUI sampling schedule in two refinement passes using the SAME
positive and negative conditioning for both passes.

The first pass establishes the character and broad composition. The second
pass continues from the partially denoised latent with the same prompt,
allowing the model to refine and integrate the established character and
scene rather than asking it to reinterpret the character through a second,
different prompt.

This deliberately returns to the V2 architecture: one prompt, two sampling
passes. The prompt itself contains the character plus any requested scene
context. Model-specific prompt adaptation remains outside the sampler.
"""


class RPGGen3SDXLTwoStageSampler:
    """Run the Gen 3 two-step render strategy with one prompt."""

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
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
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
        "SDXL two-step Gen 3 sampler: use one positive/negative prompt for "
        "both refinement passes. The prompt contains the character and scene."
    )

    @classmethod
    def resolve_stage_bounds(cls, steps, stage1_end_step, stage2_overlap):
        """Return validated (stage1_end, stage2_start) schedule bounds."""
        steps = max(1, int(steps))
        stage1_end = max(1, min(int(stage1_end_step), steps))
        overlap = max(0, int(stage2_overlap))
        stage2_start = max(0, stage1_end - overlap)
        return stage1_end, stage2_start

    def sample(
        self,
        model,
        positive,
        negative,
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

        stage1_end, stage2_start = self.resolve_stage_bounds(
            steps,
            stage1_end_step,
            stage2_overlap,
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

        # Pass 1: establish the character and broad composition.
        stage1_samples = comfy.sample.sample(
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
            last_step=stage1_end,
            force_full_denoise=False,
            noise_mask=noise_mask,
            callback=None,
            disable_pbar=disable_pbar,
            seed=noise_seed,
        )

        # Pass 2: continue the same latent with the EXACT SAME conditioning.
        # No fresh noise is introduced and no second prompt reinterpretation
        # occurs. The overlap preserves the V2-style refinement hand-off.
        stage2_samples = comfy.sample.sample(
            model,
            noise,
            steps,
            cfg,
            sampler_name,
            scheduler,
            positive,
            negative,
            stage1_samples,
            denoise=1.0,
            disable_noise=True,
            start_step=stage2_start,
            last_step=steps,
            force_full_denoise=True,
            noise_mask=noise_mask,
            callback=None,
            disable_pbar=disable_pbar,
            seed=noise_seed,
        )

        result = {"samples": stage2_samples}
        if "batch_index" in latent:
            result["batch_index"] = latent["batch_index"]
        return (result,)


NODE_CLASS_MAPPINGS = {
    "RPGGen3SDXLTwoStageSampler": RPGGen3SDXLTwoStageSampler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGGen3SDXLTwoStageSampler": "SDXL Two-Step Sampler (Gen 3)",
}
