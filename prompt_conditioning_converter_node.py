import nodes  # ComfyUI internal nodes module

class PromptConditioningConverter:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "positive": ("STRING", {"forceInput": True}),
                "negative": ("STRING", {"forceInput": True}),
                "clip": ("CLIP",),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING")
    RETURN_NAMES = ("positive_conditioning", "negative_conditioning")
    FUNCTION = "convert"
    CATEGORY = "Prompting"

    def convert(self, positive, negative, clip):
        # Use the built-in CLIPTextEncode node
        positive_cond, = nodes.CLIPTextEncode().encode(clip, positive)
        negative_cond, = nodes.CLIPTextEncode().encode(clip, negative)
        return (positive_cond, negative_cond)


NODE_CLASS_MAPPINGS = {
    "PromptConditioningConverter": PromptConditioningConverter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptConditioningConverter": "Prompt → Conditioning",
}
