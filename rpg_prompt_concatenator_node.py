from nodes import CLIPTextEncode

class PromptConcatenatorNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP",),  # Needed for conditioning output
                "art_positive": ("STRING", {"forceInput": True}),
                "char_positive": ("STRING", {"forceInput": True}),
                "art_negative": ("STRING", {"forceInput": True}),
                "char_negative": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "CONDITIONING", "CONDITIONING")
    RETURN_NAMES = (
        "concatenate_positive_string",
        "concatenate_negative_string",
        "positive",
        "negative"
    )
    FUNCTION = "concatenate_prompts"
    CATEGORY = "RPG"

    def concatenate_prompts(self, clip, art_positive, char_positive, art_negative, char_negative):
        positive = f"{art_positive.strip()}, {char_positive.strip()}"
        negative = f"{art_negative.strip()}, {char_negative.strip()}"

        # Encode prompts
        encoded_positive = CLIPTextEncode().encode(clip, positive)[0]
        encoded_negative = CLIPTextEncode().encode(clip, negative)[0]

        return (positive, negative, encoded_positive, encoded_negative)

NODE_CLASS_MAPPINGS = {
    "PromptConcatenatorNode": PromptConcatenatorNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptConcatenatorNode": "RPG Prompt Concatenator",
}
