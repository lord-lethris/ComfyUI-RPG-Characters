"""Model-independent Gen 3 art-style definitions.

Art style is presentation data, not Character DNA.  A style can be a built-in
preset or user-authored custom text.  Model-specific prompt adapters decide
how these style descriptions should be expressed for a target generator.
"""

ART_STYLE_VERSION = 1

STYLE_PRESETS = {
    "Anime Style": {
        "id": "anime_style",
        "label": "Anime Style",
        "description": "Anime-inspired 2D character illustration.",
        "positive_prompt": (
            "anime style, 2D cel shading, vibrant colors, sharp lines, "
            "expressive eyes"
        ),
        "negative_prompt": "blurry, low detail, bad anatomy",
    },
    "Dark Fantasy": {
        "id": "dark_fantasy",
        "label": "Dark Fantasy",
        "description": "Dark, gothic fantasy illustration with dramatic lighting.",
        "positive_prompt": (
            "dark fantasy, moody lighting, gothic atmosphere, cinematic "
            "shadows, eerie atmosphere"
        ),
        "negative_prompt": "bright, cheerful, cartoonish",
    },
    "Realistic": {
        "id": "realistic",
        "label": "Realistic",
        "description": "Photographic, realistic character rendering.",
        "positive_prompt": (
            "photorealistic, natural lighting, high detail, sharp focus"
        ),
        "negative_prompt": "cartoon, painting, low detail",
    },
    "Fantasy Illustration": {
        "id": "fantasy_illustration",
        "label": "Fantasy Illustration",
        "description": "Painterly fantasy character illustration.",
        "positive_prompt": (
            "fantasy art, painterly strokes, epic atmosphere, vibrant colors"
        ),
        "negative_prompt": "dull, flat, low contrast",
    },
    "Pixel Art": {
        "id": "pixel_art",
        "label": "Pixel Art",
        "description": "Deliberate classic fantasy RPG pixel art.",
        "positive_prompt": (
            "pixel art, classic fantasy RPG pixel art, hand-crafted pixel "
            "illustration, crisp hard-edged pixels, deliberate pixel clusters, "
            "limited color palette, dithering, sprite-art aesthetics, "
            "stylized fantasy character portrait"
        ),
        "negative_prompt": (
            "photorealistic, photographic, hyperrealistic, 3D render, CGI, "
            "smooth gradients, airbrushed shading, anti-aliased edges, "
            "painterly brushstrokes, realistic skin pores, glossy realism, "
            "blurry, noisy"
        ),
    },
    "Sci-Fi / Cyberpunk": {
        "id": "sci_fi_cyberpunk",
        "label": "Sci-Fi / Cyberpunk",
        "description": "Futuristic science-fiction and cyberpunk presentation.",
        "positive_prompt": (
            "sci-fi, cyberpunk, neon lights, futuristic technology, "
            "vibrant neon colors"
        ),
        "negative_prompt": (
            "medieval, fantasy, dull colors, low-tech, blurry, "
            "unrealistic proportions"
        ),
    },
}

ART_STYLE_OPTIONS = tuple(STYLE_PRESETS.keys()) + ("Custom",)


def make_art_style(style_name="Fantasy Illustration", custom_positive="", custom_negative=""):
    """Create a JSON-safe RPG_ART_STYLE document."""
    if style_name == "Custom":
        positive = str(custom_positive or "").strip()
        negative = str(custom_negative or "").strip()
        if not positive:
            raise ValueError("Custom art style requires a positive style prompt.")

        return {
            "art_style_version": ART_STYLE_VERSION,
            "type": "RPG_ART_STYLE",
            "id": "custom",
            "label": "Custom",
            "source": "custom",
            "description": "User-authored art style.",
            "positive_prompt": positive,
            "negative_prompt": negative,
        }

    try:
        preset = STYLE_PRESETS[style_name]
    except KeyError as exc:
        raise ValueError(f"Unknown art style: {style_name}") from exc

    return {
        "art_style_version": ART_STYLE_VERSION,
        "type": "RPG_ART_STYLE",
        "source": "preset",
        **preset,
    }
