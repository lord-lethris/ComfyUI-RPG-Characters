"""Gen 3 semantic age prompt overrides.

Gen 3 keeps the legacy age dropdown/data for compatibility, but some legacy
prompt wording is contradictory for modern model prompting. These overrides
provide clearer positive/negative semantics without changing V2 behaviour.
"""

GEN3_AGE_OVERRIDES = {
    "Elder": {
        "prompt": (
            "as an elderly adult, visibly aged, mature facial features, "
            "age lines and wrinkles"
        ),
        "negative_prompt": (
            "childlike, kid, teenager, youthful appearance, young adult"
        ),
    },
    "Ancient": {
        "prompt": (
            "as an ancient adult, extremely aged, deeply mature facial "
            "features, pronounced age lines and wrinkles"
        ),
        "negative_prompt": (
            "childlike, kid, teenager, youthful appearance, young adult"
        ),
    },
}


def get_age_override(name):
    """Return a Gen 3 semantic override, or an empty mapping."""
    return dict(GEN3_AGE_OVERRIDES.get(name, {}))
