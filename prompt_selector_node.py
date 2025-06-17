from nodes import CLIPTextEncode

class PromptSelectorNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "standard_positive": ("STRING", {"forceInput": True}),
                "standard_negative": ("STRING", {"forceInput": True}),
                "ollama_positive": ("STRING", {"forceInput": True}),
                "ollama_negative": ("STRING", {"forceInput": True}),
				"clip": ("CLIP",),  # Needed for conditioning output
                "prompt_source": (["Standard", "Ollama"],),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "STRING", "STRING")
    RETURN_NAMES = ("positive", "negative", "positive_string", "negative_string")
    FUNCTION = "select_prompt_pair"
    CATEGORY = "RPG"

    def select_prompt_pair(
        self,
        standard_positive,
        standard_negative,
        ollama_positive,
        ollama_negative,
		clip,  # <- This was missing
        prompt_source
    ):
        if prompt_source == "Standard":
            # Encode prompts
            encoded_positive = CLIPTextEncode().encode(clip, standard_positive)[0]
            encoded_negative = CLIPTextEncode().encode(clip, standard_negative)[0]
            return (encoded_positive, encoded_negative, standard_positive, standard_negative)
        else:
            encoded_positive = CLIPTextEncode().encode(clip, ollama_positive)[0]
            encoded_negative = CLIPTextEncode().encode(clip, ollama_negative)[0]
            return (encoded_positive, encoded_negative, ollama_positive, ollama_negative)


NODE_CLASS_MAPPINGS = {
    "PromptSelectorNode": PromptSelectorNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptSelectorNode": "Prompt Selector",
}
