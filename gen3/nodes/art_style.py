"""ComfyUI node for selecting a Gen 3 art style."""

from ..style.art_style import ART_STYLE_OPTIONS, make_art_style


class RPGCharacterArtStyle:
    """Select a built-in or user-authored presentation style."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "art_style": (list(ART_STYLE_OPTIONS),),
            },
            "optional": {
                "custom_positive": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "dynamicPrompts": False,
                    },
                ),
                "custom_negative": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "dynamicPrompts": False,
                    },
                ),
            },
        }

    RETURN_TYPES = ("ART_STYLE",)
    RETURN_NAMES = ("ART_STYLE",)
    FUNCTION = "create"
    CATEGORY = "RPG/Gen 3/Style"
    DESCRIPTION = (
        "Select a Gen 3 art style preset or provide a custom style. "
        "Style is presentation data and is independent of Character DNA."
    )

    def create(self, art_style, custom_positive="", custom_negative=""):
        return (
            make_art_style(
                art_style,
                custom_positive=custom_positive,
                custom_negative=custom_negative,
            ),
        )


NODE_CLASS_MAPPINGS = {
    "RPGCharacterArtStyle": RPGCharacterArtStyle,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RPGCharacterArtStyle": "Character Art Style (Gen 3)",
}
