"""Gen 3 lineage definitions.

Lineage is biological/species identity. It describes the creature's anatomical
baseline and which phenotype systems are valid. It deliberately does not use
the legacy prompt strings.
"""

LINEAGE_DATA = {
    "Human": {
        "category": "humanoid", "body_type": "human", "heritage_compatible": True,
        "prompt": "a human character",
        "body_plan": {
            "posture": "bipedal", "body": "human humanoid", "head": "human",
            "limbs": "human", "hands": "human hands", "feet": "human feet",
            "hair_allowed": True, "facial_hair_allowed": True,
        },
        "negative_prompt": "non-human anatomy, horns, tail, wings, scales, muzzle, reptilian face",
        "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
        "face_model": "humanoid",
        "face_allowed": True,
        "traits": {"ears": "human", "eyes": "human", "nose": "human", "mouth": "human", "skin": "skin"},
    },
    "Elf": {
        "category": "humanoid", "body_type": "elven humanoid", "heritage_compatible": True,
        "prompt": "an elven character",
        "body_plan": {
            "posture": "bipedal", "body": "elven humanoid", "head": "elven",
            "limbs": "humanoid", "hands": "humanoid hands", "feet": "humanoid feet",
            "hair_allowed": True, "facial_hair_allowed": False,
        },
        "negative_prompt": "human-only anatomy, animal muzzle, scales, facial hair, body hair",
        "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
        "face_model": "humanoid", "face_allowed": True,
        "traits": {"ears": "pointed elven ears", "eyes": "humanoid", "nose": "humanoid", "mouth": "humanoid", "skin": "skin"},
    },
    "Tiefling": {
        "category": "humanoid", "body_type": "infernal humanoid", "heritage_compatible": True,
        "prompt": "a tiefling character",
        "body_plan": {
            "posture": "bipedal", "body": "human-proportioned infernal humanoid", "head": "infernal humanoid head",
            "limbs": "humanoid", "hands": "humanoid hands", "feet": "humanoid feet",
            "build": "human-proportioned medium build",
            "hair_allowed": True, "facial_hair_allowed": True,
        },
        "negative_prompt": "ordinary human, missing horns, missing tail, dwarf, dwarven proportions, squat body, stocky dwarf-like build",
        "features": {"horns": True, "tail": True, "wings": False, "scales": False, "claws": False},
        "face_model": "humanoid", "face_allowed": True,
        "traits": {"ears": "humanoid ears", "eyes": "infernal eyes", "nose": "humanoid", "mouth": "humanoid", "skin": "infernal skin"},
        "feature_loci": {"horn_type": ["swept back", "curved", "ram", "crown"], "tail_type": ["whip", "forked", "spaded"]},
        "heritage_protected_components": ["eyes"],
        "heritage_component_overrides": {"eyes": "solid infernal eyes with no visible sclera or pupil"},
    },
    "Dragon": {
        "category": "draconic", "body_type": "dragon", "heritage_compatible": False,
        "prompt": "an anthropomorphic dragon character",
        "body_plan": {
            "posture": "bipedal", "body": "fully draconic humanoid", "head": "fully draconic head",
            "limbs": "bipedal draconic limbs", "hands": "clawed draconic hands", "feet": "digitigrade clawed feet",
            "wings": "large bat-like wings", "tail": "long muscular tail",
            "hair_allowed": False, "facial_hair_allowed": False,
        },
        "negative_prompt": "human face, human skin, human ears, human nose, human lips, human body, humanoid head, human anatomy",
        "features": {"horns": True, "tail": True, "wings": True, "scales": True, "claws": True},
        "face_model": "draconic", "face_allowed": False,
        "traits": {"ears": "no external human ears", "eyes": "reptilian eyes", "nose": "dragon muzzle", "mouth": "dragon jaws", "skin": "scales"},
        "feature_loci": {"horn_type": ["swept", "backward curved", "crown", "ridged"], "wing_type": ["bat-like", "leathery", "broad"], "scale_pattern": ["fine", "large", "overlapping", "armoured"]},
    },
    "Dragonkin": {
        "category": "draconic", "body_type": "draconic humanoid", "heritage_compatible": False,
        "prompt": "a dragonkin character",
        "body_plan": {
            "posture": "bipedal", "body": "draconic humanoid", "head": "fully draconic head",
            "limbs": "humanoid-draconic limbs", "hands": "clawed hands", "feet": "clawed humanoid feet",
            "tail": "long reptilian tail", "hair_allowed": False, "facial_hair_allowed": False,
        },
        "negative_prompt": "human face, human skin, human ears, ordinary human head",
        "features": {"horns": True, "tail": True, "wings": False, "scales": True, "claws": True},
        "face_model": "draconic_humanoid", "face_allowed": False,
        "traits": {"ears": "reptilian", "eyes": "reptilian eyes", "nose": "dragon muzzle", "mouth": "dragon jaws", "skin": "scales"},
        "feature_loci": {"horn_type": ["short", "swept", "ridged"], "scale_pattern": ["fine", "overlapping", "armoured"]},
    },
    "Half-Elf": {
        "category": "hybrid", "body_type": "humanoid", "heritage_compatible": True,
        "prompt": "a half-elf character",
        "body_plan": {
            "posture": "bipedal", "body": "humanoid", "head": "human-elven hybrid",
            "limbs": "humanoid", "hands": "humanoid hands", "feet": "humanoid feet",
            "hair_allowed": True, "facial_hair_allowed": True,
        },
        "negative_prompt": "non-humanoid anatomy, animal muzzle, scales",
        "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
        "face_model": "humanoid", "face_allowed": True,
        "traits": {"ears": "slightly pointed ears", "eyes": "humanoid", "nose": "humanoid", "mouth": "humanoid", "skin": "skin"},
    },
    "Half-Orc": {
        "category": "hybrid", "body_type": "orcish humanoid", "heritage_compatible": True,
        "prompt": "a half-orc character",
        "body_plan": {
            "posture": "bipedal", "body": "orcish humanoid", "head": "orcish humanoid",
            "limbs": "humanoid", "hands": "strong humanoid hands", "feet": "humanoid feet",
            "hair_allowed": True, "facial_hair_allowed": True,
        },
        "negative_prompt": "delicate human-only features, animal muzzle",
        "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
        "face_model": "humanoid", "face_allowed": True,
        "traits": {"ears": "orcish ears", "eyes": "humanoid", "nose": "broad orcish nose", "mouth": "orcish mouth with tusks", "skin": "skin"},
    },
    "Dwarf": {
        "category": "humanoid", "body_type": "dwarven humanoid", "heritage_compatible": True,
        "prompt": "a dwarf character",
        "body_plan": {
            "posture": "bipedal", "body": "compact dwarven humanoid", "head": "dwarven",
            "limbs": "humanoid", "hands": "dwarven hands", "feet": "dwarven feet",
            "hair_allowed": True, "facial_hair_allowed": True,
        },
        "negative_prompt": "non-humanoid anatomy, animal muzzle, scales",
        "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
        "face_model": "humanoid", "face_allowed": True,
        "traits": {"ears": "dwarven ears", "eyes": "humanoid", "nose": "broad humanoid", "mouth": "humanoid", "skin": "skin"},
    },
    "Orc": {
        "category": "humanoid", "body_type": "orcish humanoid", "heritage_compatible": True,
        "prompt": "an orc character",
        "body_plan": {
            "posture": "bipedal", "body": "orcish humanoid", "head": "orcish",
            "limbs": "humanoid", "hands": "strong humanoid hands", "feet": "humanoid feet",
            "hair_allowed": True, "facial_hair_allowed": True,
        },
        "negative_prompt": "delicate human-only features, animal muzzle",
        "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
        "face_model": "humanoid", "face_allowed": True,
        "traits": {"ears": "orcish ears", "eyes": "humanoid", "nose": "broad orcish nose", "mouth": "orcish mouth with tusks", "skin": "skin"},
    },
    "Aasimar": {
        "category": "humanoid", "body_type": "celestial humanoid", "heritage_compatible": True,
        "prompt": "an aasimar character",
        "body_plan": {
            "posture": "bipedal", "body": "celestial humanoid", "head": "humanoid with celestial features",
            "limbs": "humanoid", "hands": "humanoid hands", "feet": "humanoid feet",
            "hair_allowed": True, "facial_hair_allowed": True,
        },
        "negative_prompt": "animal muzzle, scales",
        "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
        "face_model": "humanoid", "face_allowed": True,
        "traits": {"ears": "humanoid ears", "eyes": "luminous humanoid eyes", "nose": "humanoid", "mouth": "humanoid", "skin": "skin"},
    },
    "Goblin": {
        "category": "humanoid", "body_type": "goblinoid humanoid", "heritage_compatible": False,
        "prompt": "a goblin character",
        "body_plan": {
            "posture": "bipedal", "body": "goblinoid humanoid", "head": "goblinoid",
            "limbs": "humanoid", "hands": "goblin hands", "feet": "goblin feet",
            "hair_allowed": True, "facial_hair_allowed": False,
        },
        "negative_prompt": "ordinary human face",
        "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
        "face_model": "goblinoid", "face_allowed": False,
        "traits": {"ears": "large pointed ears", "eyes": "goblin eyes", "nose": "small goblin nose", "mouth": "goblin mouth", "skin": "goblin skin"},
    },
    "Kobold": {
        "category": "reptilian", "body_type": "reptilian humanoid", "heritage_compatible": False,
        "prompt": "a kobold character",
        "body_plan": {
            "posture": "bipedal", "body": "small reptilian humanoid", "head": "fully reptilian head",
            "limbs": "reptilian humanoid limbs", "hands": "clawed hands", "feet": "clawed feet",
            "tail": "reptilian tail", "hair_allowed": False, "facial_hair_allowed": False,
        },
        "negative_prompt": "human face, human skin, human ears",
        "features": {"horns": False, "tail": True, "wings": False, "scales": True, "claws": True},
        "face_model": "reptilian", "face_allowed": False,
        "traits": {"ears": "reptilian", "eyes": "reptilian eyes", "nose": "reptilian snout", "mouth": "reptilian mouth", "skin": "scales"},
        "feature_loci": {"scale_pattern": ["fine", "pebbled", "overlapping"]},
    },
    "Lizardfolk": {
        "category": "reptilian", "body_type": "reptilian humanoid", "heritage_compatible": False,
        "prompt": "a lizardfolk character",
        "body_plan": {
            "posture": "bipedal", "body": "reptilian humanoid", "head": "fully reptilian head",
            "limbs": "reptilian humanoid limbs", "hands": "clawed hands", "feet": "clawed feet",
            "tail": "long reptilian tail", "hair_allowed": False, "facial_hair_allowed": False,
        },
        "negative_prompt": "human face, human skin, human ears",
        "features": {"horns": False, "tail": True, "wings": False, "scales": True, "claws": True},
        "face_model": "reptilian", "face_allowed": False,
        "traits": {"ears": "reptilian", "eyes": "reptilian eyes", "nose": "reptilian snout", "mouth": "reptilian mouth", "skin": "scales"},
        "feature_loci": {"scale_pattern": ["fine", "pebbled", "overlapping"]},
    },
    "Halfling": {
        "category": "humanoid", "body_type": "halfling humanoid", "heritage_compatible": True,
        "prompt": "a halfling character",
        "body_plan": {
            "posture": "bipedal", "body": "small halfling humanoid", "head": "halfling",
            "limbs": "humanoid", "hands": "small humanoid hands", "feet": "small humanoid feet",
            "build": "small and sturdy",
            "hair_allowed": True, "facial_hair_allowed": True,
        },
        "negative_prompt": "giant proportions, dwarf body, animal muzzle",
        "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
        "face_model": "humanoid", "face_allowed": True,
        "traits": {"ears": "rounded humanoid ears", "eyes": "humanoid", "nose": "humanoid", "mouth": "humanoid", "skin": "skin"},
    },
    "Gnome": {
        "category": "humanoid", "body_type": "gnomish humanoid", "heritage_compatible": True,
        "prompt": "a gnome character",
        "body_plan": {
            "posture": "bipedal", "body": "small gnomish humanoid", "head": "gnomish",
            "limbs": "humanoid", "hands": "small humanoid hands", "feet": "small humanoid feet",
            "build": "small and compact",
            "hair_allowed": True, "facial_hair_allowed": True,
        },
        "negative_prompt": "giant proportions, dwarf body, animal muzzle",
        "features": {"horns": False, "tail": False, "wings": False, "scales": False, "claws": False},
        "face_model": "gnomish", "face_allowed": True,
        "traits": {"ears": "pointed ears", "eyes": "large gnomish eyes", "nose": "prominent gnomish nose", "mouth": "humanoid", "skin": "skin"},
    },
    "Aarakocra": {
        "category": "avian", "body_type": "avian humanoid", "heritage_compatible": False,
        "prompt": "an aarakocra character",
        "body_plan": {
            "posture": "bipedal", "body": "avian humanoid", "head": "avian head",
            "limbs": "avian humanoid limbs", "hands": "taloned hands", "feet": "taloned feet",
            "wings": "feathered wings", "hair_allowed": False, "facial_hair_allowed": False,
        },
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
    "body_plan": {
        "posture": "bipedal", "body": "fantasy humanoid", "head": "humanoid",
        "limbs": "humanoid", "hands": "humanoid hands", "feet": "humanoid feet",
        "hair_allowed": True, "facial_hair_allowed": True,
    },
    "traits": {"ears": "humanoid ears", "eyes": "humanoid", "nose": "humanoid", "mouth": "humanoid", "skin": "skin"},
}

LINEAGE_ALIASES = {
    "High Elf": "Elf",
    "Wood Elf": "Elf",
    "Dark Elf (Drow)": "Elf",
    "Wild Elf (Grugach)": "Elf",
    "Aquatic Elf": "Elf",
    "Hill Dwarf": "Dwarf",
    "Mountain Dwarf": "Dwarf",
    "Duergar (Gray Dwarf)": "Dwarf",
    "Hairfoot Halfling": "Halfling",
    "Stout Halfling": "Halfling",
    "Tallfellow Halfling": "Halfling",
    "Rock Gnome": "Gnome",
    "Forest Gnome": "Gnome",
    "Deep Gnome (Svirfneblin)": "Gnome",
}

def get_lineage(race):
    key = LINEAGE_ALIASES.get(race, race)
    return LINEAGE_DATA.get(key, DEFAULT_LINEAGE)
