"""Gen 3 heritage definitions.

Heritage is cultural/phenotypic context, not species. Components are separated
so lineage rules can veto incompatible biological features.
"""

HERITAGE_DATA = {
    "British": {"label": "British", "prompt": "British heritage", "phenotype_prompt": "light to medium skin tone, varied humanoid features, blue, green or brown eyes", "components": {"skin": "light to medium skin tone", "facial_features": "varied humanoid features", "eyes": "blue, green or brown eyes"}, "humanoid_only": True},
    "Japanese": {"label": "Japanese", "prompt": "Japanese heritage", "phenotype_prompt": "light skin tone, dark brown eyes and delicate humanoid features", "components": {"skin": "light skin tone", "facial_features": "delicate humanoid features", "eyes": "dark brown eyes"}, "humanoid_only": True},
    "Chinese": {"label": "Chinese", "prompt": "Chinese heritage", "phenotype_prompt": "light to medium skin tone, dark eyes and varied East Asian humanoid features", "components": {"skin": "light to medium skin tone", "facial_features": "varied East Asian humanoid features", "eyes": "dark eyes"}, "humanoid_only": True},
    "Indian": {"label": "Indian", "prompt": "Indian heritage", "phenotype_prompt": "medium to deep brown skin tone and varied South Asian humanoid features", "components": {"skin": "medium to deep brown skin tone", "facial_features": "varied South Asian humanoid features"}, "humanoid_only": True},
    "African": {"label": "African", "prompt": "African heritage", "phenotype_prompt": "dark skin tone and varied African humanoid features", "components": {"skin": "dark skin tone", "facial_features": "varied African humanoid features"}, "humanoid_only": True},
    "Irish": {"label": "Irish", "prompt": "Irish heritage", "phenotype_prompt": "fair to light skin tone and varied Celtic humanoid features", "components": {"skin": "fair to light skin tone", "facial_features": "varied Celtic humanoid features"}, "humanoid_only": True},
    "Scottish": {"label": "Scottish", "prompt": "Scottish heritage", "phenotype_prompt": "fair to light skin tone and varied Celtic humanoid features", "components": {"skin": "fair to light skin tone", "facial_features": "varied Celtic humanoid features"}, "humanoid_only": True},
    "Nordic": {"label": "Nordic", "prompt": "Nordic heritage", "phenotype_prompt": "fair skin tone, varied northern European humanoid features and light or blue eyes", "components": {"skin": "fair skin tone", "facial_features": "varied northern European humanoid features", "eyes": "light or blue eyes"}, "humanoid_only": True},
    "Mediterranean": {"label": "Mediterranean", "prompt": "Mediterranean heritage", "phenotype_prompt": "olive to medium skin tone and varied Mediterranean humanoid features", "components": {"skin": "olive to medium skin tone", "facial_features": "varied Mediterranean humanoid features"}, "humanoid_only": True},
    "Middle Eastern": {"label": "Middle Eastern", "prompt": "Middle Eastern heritage", "phenotype_prompt": "medium skin tone and varied Middle Eastern humanoid features", "components": {"skin": "medium skin tone", "facial_features": "varied Middle Eastern humanoid features"}, "humanoid_only": True},
    "Slavic": {"label": "Slavic", "prompt": "Slavic heritage", "phenotype_prompt": "fair to medium skin tone and varied Slavic humanoid features", "components": {"skin": "fair to medium skin tone", "facial_features": "varied Slavic humanoid features", "eyes": "blue, green or brown eyes"}, "humanoid_only": True},
    "Latin American": {"label": "Latin American", "prompt": "Latin American heritage", "phenotype_prompt": "varied skin tones and diverse Latin American humanoid features", "components": {"skin": "varied skin tones", "facial_features": "diverse Latin American humanoid features"}, "humanoid_only": True},
    "Fantasy": {"label": "Fantasy", "prompt": "Fantasy heritage", "phenotype_prompt": "varied fantasy humanoid features", "components": {"facial_features": "varied fantasy humanoid features"}, "humanoid_only": True},
}

def get_heritage(name):
    """Return heritage data without turning an empty selection into prose."""
    if (
        name is None
        or not str(name).strip()
        or str(name).strip().lower() == "none"
    ):
        return {
            "label": "",
            "prompt": "",
            "phenotype_prompt": "",
            "components": {},
            "humanoid_only": True,
        }

    name = str(name).strip()
    return HERITAGE_DATA.get(
        name,
        {
            "label": name,
            "prompt": f"{name} heritage",
            "phenotype_prompt": "",
            "components": {},
            "humanoid_only": True,
        },
    )
