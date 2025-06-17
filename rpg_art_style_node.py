# rpg_art_style_node.py

class RPGArtStyleSelector:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "art_style": ([
                    "Anime Style",
                    "Dark Fantasy",
                    "Realistic",
                    "Fantasy Illustration",
                    "Digital Painting",
                    "Pixar Animation",
                ],)
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = (
        "Ollama_Posative_Textbox_1",
        "positive_prompt",
        "negative_prompt",
        "Ollama_Negative_Textbox_1",
    )

    FUNCTION = "generate_prompt"
    CATEGORY = "RPG"

    STYLE_PROMPTS = {
        "Anime Style": {
            "positive": "anime style, 2D cel shading, vibrant colors, sharp lines, expressive eyes",
            "negative": "blurry, low detail, bad anatomy"
        },
        "Dark Fantasy": {
            "positive": "dark fantasy, moody lighting, gothic, cinematic shadows, eerie atmosphere",
            "negative": "bright, cheerful, cartoonish"
        },
        "Realistic": {
            "positive": "photorealistic, natural lighting, high detail, sharp focus",
            "negative": "cartoon, painting, low detail"
        },
        "Fantasy Illustration": {
            "positive": "fantasy art, painterly strokes, epic atmosphere, vibrant colors",
            "negative": "dull, flat, low contrast"
        },
        "Digital Painting": {
            "positive": "digital painting, smooth brushwork, rich textures, detailed lighting",
            "negative": "pixelated, noisy, flat lighting"
        },
    }

    def generate_prompt(self, art_style):
        style_prompts_text = {
            "Anime Style": (
                "Use anime style: cel shading, vibrant color, expressive eyes and sharp lines.\n\n"
                "**1024x1024 Extreme Close-Up Portrait**\n\n"
                "The face of the character is central, rendered in vivid anime detail with expressive eyes and colorful features. Hair flows in stylized strands, and outlines are clean and dynamic.\n\n"
                "**Eyes**: Large, sparkling, and brimming with emotion.\n\n"
                "**Hair**: Colorful and animated, capturing motion and shine.\n\n"
                "**Upper Chest/Clothing**: Stylized clothing with bold patterns or accessories.\n\n"
                "**Soft Background**: Gentle gradients or painterly background relevant to the scene.\n\n"
                "All visual emphasis is on the facial features, hair, and upper chest."
            ),
            "Dark Fantasy": (
                "Use dark fantasy style: moody lighting, gothic atmosphere, dramatic shading.\n\n"
                "**1024x1024 Extreme Close-Up Portrait**\n\n"
                "The character's face emerges from shadow, lit by eerie glow. Their expression carries weight and mystery.\n\n"
                "**Eyes**: Piercing or haunted, with high shadow contrast.\n\n"
                "**Hair**: Windswept or unkempt, in deep tones.\n\n"
                "**Upper Chest/Clothing**: Gothic armor, leather, or mystical robes with sigils.\n\n"
                "**Soft Background**: Blurred cathedrals, foggy crypts, or dying embers."
            ),
            "Realistic": (
                "Use realistic style: photographic precision, natural lighting, high realism.\n\n"
                "**1024x1024 Extreme Close-Up Portrait**\n\n"
                "Highly detailed character face in true-to-life proportions. Skin texture, pores, and light interaction are all depicted authentically.\n\n"
                "**Eyes**: Realistic reflections, depth, and moisture.\n\n"
                "**Hair**: Individually rendered strands, natural movement.\n\n"
                "**Upper Chest/Clothing**: Textiles with natural folds and stitch detail.\n\n"
                "**Soft Background**: Subtle bokeh, faded landscape elements."
            ),
            "Fantasy Illustration": (
                "Use fantasy illustration style: vibrant colors, painterly texture, epic composition.\n\n"
                "**1024x1024 Extreme Close-Up Portrait**\n\n"
                "Character glows with heroic light. Soft edges blend into a fantasy environment.\n\n"
                "**Eyes**: Mythic gleam, vibrant irises, imbued with magic.\n\n"
                "**Hair**: Flowing, dramatic, full of color and motion.\n\n"
                "**Upper Chest/Clothing**: Armor or robes, enchanted detail, magical symbols.\n\n"
                "**Soft Background**: Clouds, magical auras, glowing cliffs or ruins."
            ),
            "Digital Painting": (
                "Use digital painting style: rich texture, brushstrokes, dynamic lighting.\n\n"
                "**1024x1024 Extreme Close-Up Portrait**\n\n"
                "Painted detail with soft blend transitions and visible brush techniques.\n\n"
                "**Eyes**: Reflective, highlighted with strokes.\n\n"
                "**Hair**: Painterly motion with rich shading.\n\n"
                "**Upper Chest/Clothing**: Stylized materials with visual brushwork.\n\n"
                "**Soft Background**: Smudged gradients and digital bloom."
            ),
        }

        Ollama_Posative_Textbox_1 = style_prompts_text.get(art_style, "**1024x1024 Extreme Close-Up Portrait**\n\nCharacter with vivid detail and atmospheric background.")
        positive_prompt = self.STYLE_PROMPTS.get(art_style, {}).get("positive", "")
        negative_prompt = self.STYLE_PROMPTS.get(art_style, {}).get("negative", "")

        ollama_negative_prompt_instruction = (
            "You are an AI art Generator. You are a visual design assistant generating a **negative prompt** for a SDXL prompt.\n\n"
            "Use the following positive prompt as reference. Your task is to identify unwanted visual artifacts, styles, or elements that should be **excluded** to preserve the artistic and thematic integrity of the original.\n\n"
            "Format the output as a clean, comma-separated list of negative prompt tags and descriptors.\n\n"
            "Avoid redundancy. Do **not** repeat anything that's already desirable in the positive prompt.\n\n"
            "Keep it realistic, but include common issues in AI generation such as:\n"
            "- anatomy errors\n"
            "- texture distortions\n"
            "- uncanny facial features\n"
            "- unwanted artifacts or styles\n"
            "- bad lighting or awkward angles\n"
            "- overexaggeration or surreal effects\n\n"
            "Only return the negative prompt list in clean Markdown format with no extra commentary, no extra text or formatting. Do not include any introductions or explanations. Begin immediately."
        )

        return (
            Ollama_Posative_Textbox_1,
            positive_prompt,
            negative_prompt,
            ollama_negative_prompt_instruction
        )


NODE_CLASS_MAPPINGS = {
    "RPGArtStyleSelector": RPGArtStyleSelector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGArtStyleSelector": "RPG Art Style Selector",
}
