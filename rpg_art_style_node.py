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
                    "Pixel Art",
                    "Sci-Fi / Cyberpunk",  # NEW
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
        "Pixel Art": {
            "positive": "pixel art, classic fantasy RPG pixel art, hand-crafted pixel illustration, crisp hard-edged pixels, limited color palette, deliberate pixel clusters, dithering, sprite-art aesthetics, stylized fantasy character portrait",
            "negative": "photorealistic, photographic, hyperrealistic, 3D render, CGI, smooth gradients, airbrushed shading, anti-aliased edges, painterly brushstrokes, realistic skin pores, glossy realism, blurry, noisy"
        },
        "Sci-Fi / Cyberpunk": {  # NEW
            "positive": "sci-fi, cyberpunk, neon lights, futuristic tech, detailed cybernetic elements, vibrant neon colors",
            "negative": "medieval, fantasy, dull colors, low-tech, blurry, unrealistic proportions"
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
            "Pixel Art": (
                "Use classic fantasy RPG pixel art style: hand-crafted pixel illustration with crisp hard-edged pixels, deliberate pixel clusters, limited but expressive color palettes, strong silhouettes, dithering, selective highlights, and readable sprite-art forms. The result should look like a deliberately created piece of pixel art, not a normal illustration that has merely been pixelated.\n\n"
                "**1024x1024 Extreme Close-Up Portrait**\n\n"
                "Render the character as a polished fantasy RPG pixel-art portrait, inspired by classic 16-bit and 32-bit game artwork. Use visible pixel structure throughout the image, stepped edges, block-based shading, clustered pixels, controlled dithering, and deliberate colour grouping. Keep important facial and costume features readable while simplifying tiny details into intentional pixel shapes.\n\n"
                "**Eyes**: Bright, expressive pixel-art eyes with a few carefully placed highlight pixels and strong readable shapes.\n\n"
                "**Hair**: Build hair from grouped pixel clusters and sweeping stepped shapes, with a small number of highlight bands rather than individual realistic strands.\n\n"
                "**Upper Chest/Clothing**: Use strong silhouettes, blocky folds, clustered highlights and shadows, and simplified decorative details that remain clearly readable at pixel scale.\n\n"
                "**Soft Background**: Construct the environment from layered pixel-art shapes, atmospheric colour blocks, silhouettes, dithering and simplified environmental details rather than photographic depth of field.\n\n"
                "Avoid photorealistic rendering, smooth photographic gradients, anti-aliased edges, painterly brushwork, CGI/3D-render appearance, excessive micro-detail, and simply applying a pixelation filter to realistic artwork."
            ),
            "Sci-Fi / Cyberpunk": (  # NEW
                "Use sci-fi / cyberpunk style: neon lights, futuristic city, cybernetic implants, high-tech fashion.\n\n"
                "**1024x1024 Extreme Close-Up Portrait**\n\n"
                "The character's face shows technological augmentation, glowing interfaces, and neon reflections.\n\n"
                "**Eyes**: Enhanced with digital overlays or neon glows.\n\n"
                "**Hair**: Futuristic styles with vibrant neon highlights.\n\n"
                "**Upper Chest/Clothing**: Cyberpunk armor, holographic fabrics, tech accessories.\n\n"
                "**Soft Background**: Futuristic cityscape, neon signs, misty night lights."
            ),
        }

        Ollama_Posative_Textbox_1 = style_prompts_text.get(
            art_style,
            "**1024x1024 Extreme Close-Up Portrait**\n\nCharacter with vivid detail and atmospheric background."
        )
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
