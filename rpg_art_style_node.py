# rpg_art_style_node.py

ART_STYLE_DATA = {
    "Fantasy Illustration": {
        "prompt": "fantasy illustration, digital painting, epic composition",
        "negative_prompt": ""
    },
    "Realistic": {
        "prompt": "realistic, highly detailed, lifelike rendering, dramatic lighting",
        "negative_prompt": "cartoon, anime, sketch, low detail"
    },
    "Painterly": {
        "prompt": "oil painting, painterly brushwork, classical portrait",
        "negative_prompt": "digital look, photo"
    },
    "Concept Art": {
        "prompt": "concept art, character design sheet, artistic rendering",
        "negative_prompt": "comic, anime, unfinished"
    },
    "Dark Fantasy": {
        "prompt": "dark fantasy, moody atmosphere, gothic shadows, dramatic lighting",
        "negative_prompt": "bright, cheerful, cartoon"
    },
    "Anime Style": {
       "prompt": "anime style, 2D illustration, cel shading, vibrant colors, sharp lines, big eyes, expressive face, studio ghibli, makoto shinkai, anime screencap",
       "negative_prompt": "photorealistic, realistic, 3D, Pixar, Unreal Engine, CG, rendering, hyperrealistic, uncanny, doll-like, semi-realistic"
    },
    "Comic Book": {
        "prompt": "comic book, inked lines, bold shading, western comic style",
        "negative_prompt": "realistic, anime, painterly"
    },
    "Watercolor": {
        "prompt": "watercolor painting, soft gradients, light textures",
        "negative_prompt": "bold ink, high contrast"
    }
}

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
                    # add more styles as needed
                ],)
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("Ollama_Generate_V2_Textbox_1", "positive_prompt", "negative_prompt")
    FUNCTION = "generate_prompt"
    CATEGORY = "RPG"

    # Example prompts for styles - fill these with your actual prompts
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
        "Pixar Animation": {
            "positive": "Pixar style, stylized 3D, soft lighting, warm colors, expressive characters",
            "negative": "dark, realistic, harsh lighting"
        },
    }

    def generate_prompt(self, art_style):
        base_prompt = (
            "You are an RPG Solo Character extreme close-up portrait prompt generator. "
            "1024x1024. Do not explain your answers. Be sure to Include Race, Ethnicity, Gender, "
            "Age, Class, Hair Style, Hair Colour, Beard Style, Beard Colour, Clothes Style, Emotion, and Scene. "
            "Return a richly detailed SDXL prompt in natural descriptive language. No extra commentary."
        )

        style_prompts_text = {
            "Anime Style": (
                "You are an RPG Solo Character extreme close-up portrait prompt generator in anime style, "
                "featuring 2D illustration, cel shading, vibrant colors, sharp lines, and expressive eyes. "
                + base_prompt +
                " Emphasize anime aesthetics."
            ),
            "Dark Fantasy": (
                base_prompt + 
                " Emphasize dark fantasy aesthetics: moody lighting, gothic elements, cinematic shadows."
            ),
            "Realistic": (
                base_prompt + 
                " Emphasize realistic aesthetics: photographic detail, natural lighting, high realism."
            ),
            "Fantasy Illustration": (
                base_prompt +
                " Emphasize fantasy illustration style: painterly strokes, vibrant colors, epic atmosphere."
            ),
            "Digital Painting": (
                base_prompt +
                " Emphasize digital painting style: smooth brushwork, rich textures, detailed lighting."
            ),
            "Pixar Animation": (
                base_prompt +
                " Emphasize Pixar style: soft lighting, stylized characters, warm colors, and 3D rendering feel."
            ),
        }

        Ollama_Generate_V2_Textbox_1 = style_prompts_text.get(art_style, base_prompt + f" Emphasize {art_style} aesthetics.")
        
        positive_prompt = self.STYLE_PROMPTS.get(art_style, {}).get("positive", "")
        negative_prompt = self.STYLE_PROMPTS.get(art_style, {}).get("negative", "")

        return (Ollama_Generate_V2_Textbox_1, positive_prompt, negative_prompt)



NODE_CLASS_MAPPINGS = {
    "RPGArtStyleSelector": RPGArtStyleSelector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGArtStyleSelector": "RPG Art Style Selector",
}
