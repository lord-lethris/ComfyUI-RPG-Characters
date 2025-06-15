class PromptSelectorNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "standard_positive": ("STRING", {"forceInput": True}),
                "standard_negative": ("STRING", {"forceInput": True}),
                "ollama_positive": ("STRING", {"forceInput": True}),
                "ollama_negative": ("STRING", {"forceInput": True}),
                "prompt_source": (["Standard", "Ollama"],),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt")
    FUNCTION = "select_prompt_pair"
    CATEGORY = "RPG"

    def select_prompt_pair(self, standard_positive, standard_negative, ollama_positive, ollama_negative, prompt_source):
        if prompt_source == "Standard":
            return standard_positive, standard_negative
        else:  # Ollama
            return ollama_positive, ollama_negative


NODE_CLASS_MAPPINGS = {
    "PromptSelectorNode": PromptSelectorNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptSelectorNode": "Prompt Selector",
}
