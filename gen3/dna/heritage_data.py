"""Gen 3 heritage definitions.

Heritage is cultural/phenotypic context, not species. Human heritage data may
influence humanoid phenotype, but incompatible lineages do not receive human
morphology merely because a legacy ethnicity value is selected.
"""

HERITAGE_DATA = {
    "British": {"label": "British", "prompt": "British heritage", "phenotype_prompt": "light to medium skin tone, varied humanoid features, blue, green or brown eyes", "humanoid_only": True},
    "Japanese": {"label": "Japanese", "prompt": "Japanese heritage", "phenotype_prompt": "light skin tone, dark brown eyes and delicate humanoid features", "humanoid_only": True},
    "Chinese": {"label": "Chinese", "prompt": "Chinese heritage", "phenotype_prompt": "light to medium skin tone, dark eyes and varied East Asian humanoid features", "humanoid_only": True},
    "Indian": {"label": "Indian", "prompt": "Indian heritage", "phenotype_prompt": "medium to deep brown skin tone and varied South Asian humanoid features", "humanoid_only": True},
    "African": {"label": "African heritage", "prompt": "African heritage", "phenotype_prompt": "dark skin tone and varied African humanoid features", "humanoid_only": True},
    "Irish": {"label": "Irish", "prompt": "Irish heritage", "phenotype_prompt": "fair to light skin tone and varied Celtic humanoid features", "humanoid_only": True},
    "Scottish": {"label": "Scottish", "prompt": "Scottish heritage", "phenotype_prompt": "fair to light skin tone and varied Celtic humanoid features", "humanoid_only": True},
    "Nordic": {"label": "Nordic heritage", "prompt": "Nordic heritage", "phenotype_prompt": "fair skin tone, varied northern European humanoid features and light or blue eyes", "humanoid_only": True},
    "Mediterranean": {"label": "Mediterranean heritage", "prompt": "Mediterranean heritage", "phenotype_prompt": "olive to medium skin tone and varied Mediterranean humanoid features", "humanoid_only": True},
    "Middle Eastern": {"label": "Middle Eastern heritage", "prompt": "Middle Eastern heritage", "phenotype_prompt": "medium skin tone and varied Middle Eastern humanoid features", "humanoid_only": True},
    "Slavic": {"label": "Slavic heritage", "prompt": "Slavic heritage", "phenotype_prompt": "fair to medium skin tone and varied Slavic humanoid features", "humanoid_only": True},
    "Latin American": {"label": "Latin American heritage", "prompt": "Latin American heritage", "phenotype_prompt": "varied skin tones and diverse Latin American humanoid features", "humanoid_only": True},
    "Fantasy": {"label": "Fantasy heritage", "prompt": "fantasy heritage", "phenotype_prompt": "varied fantasy humanoid features", "humanoid_only": True},
}

def get_heritage(name):
    return HERITAGE_DATA.get(name, {"label": name, "prompt": f"{name} heritage", "phenotype_prompt": "", "humanoid_only": True})
