"""Gen 3 SDXL two-stage sampler.

Runs one ComfyUI sampling schedule in two conditioning phases:
1. Character establishment.
2. Style/scene reinterpretation.

The implementation mirrors KSampler Advanced semantics: Stage 1 keeps
leftover noise, Stage 2 continues from that latent without adding fresh noise.
"""

class RPGGen3SDXLTwoStageSampler:
    """Run the experimentally validated Gen 3 SDXL two-stage render strategy."""

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
        "reinterpret it through a separate style/scene conditioning pass."
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
        import comfy.model_management
        import comfy.sample

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
        disable_pbar = not comfy.utils.PROGRESS_BAR_ENABLED if hasattr(comfy, "utils") else False

        # Stage 1: establish character identity and composition, then hand the
        # partially denoised latent to Stage 2 with its remaining noise intact.
        stage1_samples = comfy.sample.sample(
            model,
            noise,
            steps,
            cfg,
            sampler_name,
            scheduler,
            positive_stage1,
            negative_stage1,
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

        # Stage 2: continue from exactly the Stage 1 latent. No fresh noise is
        # added; only the conditioning changes to style/scene refinement.
        stage2_samples = comfy.sample.sample(
            model,
            noise,
            steps,
            cfg,
            sampler_name,
            scheduler,
            positive_stage2,
            negative_stage2,
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
    "RPGGen3SDXLTwoStageSampler": "SDXL Two-Stage Sampler (Gen 3)",
}
