class ModelLikenessSwitch:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "use_likeness": ("BOOLEAN", {"default": False}),
                "model_if_true": ("MODEL",),
                "model_if_false": ("MODEL",),
            }
        }

    RETURN_TYPES = ("MODEL", "BOOLEAN",)
    RETURN_NAMES = ("selected_model", "use_likeness_value",)
    FUNCTION = "select_model"
    CATEGORY = "RPG"

    def select_model(self, use_likeness, model_if_true, model_if_false):
        return (model_if_true if use_likeness else model_if_false, use_likeness)


NODE_CLASS_MAPPINGS = {
    "ModelLikenessSwitch": ModelLikenessSwitch,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ModelLikenessSwitch": "Model Selector (Use Likeness)",
}
