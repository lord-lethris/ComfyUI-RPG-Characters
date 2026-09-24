"""Gen 3 lineage definitions.

Lineage is biological/species identity. It describes the creature's anatomical
baseline and which phenotype systems are valid. It deliberately does not use
the legacy prompt strings.
"""

LINEAGE_DATA = {
    "Human": {
        "category": "humanoid", "body_type": "human", "heritage_compatible": True,
        "prompt": "a human",
        "negative_prompt": "non-human anatomy, horns, tail, wings, scales, muzzle, reptilian face",
        "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
        "face_model": "humanoid",
        "face_allowed": True,
        "traits": {"ears": "human", "eyes": "human", "nose": "human", "mouth": "human", "skin": "skin"},
    },
    "Elf": {
        "category": "humanoid", "body_type": "elven humanoid", "heritage_compatible": True,
        "prompt": "an elven humanoid with subtly pointed ears and an elegant elven appearance",
        "negative_prompt": "human-only anatomy, animal muzzle, scales",
        "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
        "face_model": "humanoid", "face_allowed": True,
        "traits": {"ears": "pointed elven ears", "eyes": "humanoid", "nose": "humanoid", "mouth": "humanoid", "skin": "skin"},
    },
    "Tiefling": {
        "category": "humanoid", "body_type": "infernal humanoid", "heritage_compatible": True,
        "prompt": "a tiefling humanoid with infernal features",
        "negative_prompt": "ordinary human, missing horns, missing tail",
        "features": {"horns": True, "tail": True, "wings": False, "scales": False, "claws": False},
        "face_model": "humanoid", "face_allowed": True,
        "traits": {"ears": "humanoid ears", "eyes": "infernal eyes", "nose": "humanoid", "mouth": "humanoid", "skin": "infernal skin"},
        "feature_loci": {"horn_type": ["swept back", "curved", "ram", "crown"], "tail_type": ["whip", "forked", "spaded"]},
    },
    "Dragon": {
        "category": "draconic", "body_type": "dragon", "heritage_compatible": False,
        "prompt": "a sapient dragon with a fully draconic head, scaled body, reptilian eyes, horns, powerful wings, a long tail and clawed limbs",
        "negative_prompt": "human face, human skin, human ears, human nose, human lips, human body, humanoid head, human anatomy",
        "features": {"horns": True, "tail": True, "wings": True, "scales": True, "claws": True},
        "face_model": "draconic", "face_allowed": False,
        "traits": {"ears": "no external human ears", "eyes": "reptilian eyes", "nose": "dragon muzzle", "mouth": "dragon jaws", "skin": "scales"},
        "feature_loci": {"horn_type": ["swept", "backward curved", "crown", "ridged"], "wing_type": ["bat-like", "leathery", "broad"], "scale_pattern": ["fine", "large", "overlapping", "armoured"]},
    },
    "Dragonkin": {
        "category": "draconic", "body_type": "draconic humanoid", "heritage_compatible": False,
        "prompt": "a dragonkin humanoid with a distinctly draconic head, scales, reptilian eyes, horns, a tail and clawed hands",
        "negative_prompt": "human face, human skin, human ears, ordinary human head",
        "features": {"horns": True, "tail": True, "wings": False, "scales": True, "claws": True},
        "face_model": "draconic_humanoid", "face_allowed": False,
        "traits": {"ears": "reptilian", "eyes": "reptilian eyes", "nose": "dragon muzzle", "mouth": "dragon jaws", "skin": "scales"},
        "feature_loci": {"horn_type": ["short", "swept", "ridged"], "scale_pattern": ["fine", "overlapping", "armoured"]},
    },
    "Half-Elf": {
        "category": "hybrid", "body_type": "humanoid", "heritage_compatible": True,
        "prompt": "a half-elf humanoid with subtly elven features and slightly pointed ears",
        "negative_prompt": "non-humanoid anatomy, animal muzzle, scales",
        "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
        "face_model": "humanoid", "face_allowed": True,
        "traits": {"ears": "slightly pointed ears", "eyes": "humanoid", "nose": "humanoid", "mouth": "humanoid", "skin": "skin"},
    },
    "Half-Orc": {
        "category": "hybrid", "body_type": "orcish humanoid", "heritage_compatible": True,
        "prompt": "a half-orc humanoid with pronounced tusks, strong jaw and orcish features",
        "negative_prompt": "delicate human-only features, animal muzzle",
        "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
        "face_model": "humanoid", "face_allowed": True,
        "traits": {"ears": "orcish ears", "eyes": "humanoid", "nose": "broad orcish nose", "mouth": "orcish mouth with tusks", "skin": "skin"},
    },
    "Dwarf": {
        "category": "humanoid", "body_type": "dwarven humanoid", "heritage_compatible": True,
        "prompt": "a dwarven humanoid with a sturdy compact build and broad facial structure",
        "negative_prompt": "non-humanoid anatomy, animal muzzle, scales",
        "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
        "face_model": "humanoid", "face_allowed": True,
        "traits": {"ears": "dwarven ears", "eyes": "humanoid", "nose": "broad humanoid", "mouth": "humanoid", "skin": "skin"},
    },
    "Orc": {
        "category": "humanoid", "body_type": "orcish humanoid", "heritage_compatible": True,
        "prompt": "an orc humanoid with prominent lower tusks and strong orcish facial features",
        "negative_prompt": "delicate human-only features, animal muzzle",
        "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
        "face_model": "humanoid", "face_allowed": True,
        "traits": {"ears": "orcish ears", "eyes": "humanoid", "nose": "broad orcish nose", "mouth": "orcish mouth with tusks", "skin": "skin"},
    },
    "Aasimar": {
        "category": "humanoid", "body_type": "celestial humanoid", "heritage_compatible": True,
        "prompt": "an aasimar humanoid with an otherworldly celestial appearance",
        "negative_prompt": "animal muzzle, scales",
        "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
        "face_model": "humanoid", "face_allowed": True,
        "traits": {"ears": "humanoid ears", "eyes": "luminous humanoid eyes", "nose": "humanoid", "mouth": "humanoid", "skin": "skin"},
    },
    "Goblin": {
        "category": "humanoid", "body_type": "goblinoid humanoid", "heritage_compatible": False,
        "prompt": "a goblin humanoid with large pointed ears, a small nose and wiry goblin features",
        "negative_prompt": "ordinary human face",
        "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
        "face_model": "goblinoid", "face_allowed": False,
        "traits": {"ears": "large pointed ears", "eyes": "goblin eyes", "nose": "small goblin nose", "mouth": "goblin mouth", "skin": "goblin skin"},
    },
    "Kobold": {
        "category": "reptilian", "body_type": "reptilian humanoid", "heritage_compatible": False,
        "prompt": "a kobold humanoid with a distinctly reptilian head, scales, pointed snout, tail and claws",
        "negative_prompt": "human face, human skin, human ears",
        "features": {"horns": False, "tail": True, "wings": False, "scales": True, "claws": True},
        "face_model": "reptilian", "face_allowed": False,
        "traits": {"ears": "reptilian", "eyes": "reptilian eyes", "nose": "reptilian snout", "mouth": "reptilian mouth", "skin": "scales"},
        "feature_loci": {"scale_pattern": ["fine", "pebbled", "overlapping"]},
    },
    "Lizardfolk": {
        "category": "reptilian", "body_type": "reptilian humanoid", "heritage_compatible": False,
        "prompt": "a lizardfolk humanoid with a reptilian head, scales, long snout, tail and clawed hands",
        "negative_prompt": "human face, human skin, human ears",
        "features": {"horns": False, "tail": True, "wings": False, "scales": True, "claws": True},
        "face_model": "reptilian", "face_allowed": False,
        "traits": {"ears": "reptilian", "eyes": "reptilian eyes", "nose": "reptilian snout", "mouth": "reptilian mouth", "skin": "scales"},
        "feature_loci": {"scale_pattern": ["fine", "pebbled", "overlapping"]},
    },
    "Aarakocra": {
        "category": "avian", "body_type": "avian humanoid", "heritage_compatible": False,
        "prompt": "an aarakocra avian humanoid with a feathered head, hooked beak, wings and taloned feet",
        "negative_prompt": "human face, human skin, human nose, human ears",
        "features": {"horns": False, "tail": False, "wings": True, "scales": False, "claws": True},
        "face_model": "avian", "face_allowed": False,
        "traits": {"ears": "no human ears", "eyes": "avian eyes", "nose": "beak", "mouth": "beak", "skin": "feathers"},
    },
}

# Existing V2 races that do not yet have a dedicated Gen 3 definition use a
# safe humanoid fallback rather than leaking their legacy prompt into DNA.
DEFAULT_LINEAGE = {
    "category": "fantasy",
    "body_type": "humanoid",
    "heritage_compatible": True,
    "prompt": "a fantasy humanoid",
    "negative_prompt": "incompatible non-humanoid anatomy",
    "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
    "face_model": "humanoid", "face_allowed": True,
    "traits": {"ears": "humanoid ears", "eyes": "humanoid", "nose": "humanoid", "mouth": "humanoid", "skin": "skin"},
}

def get_lineage(race):
    return LINEAGE_DATA.get(race, DEFAULT_LINEAGE)
