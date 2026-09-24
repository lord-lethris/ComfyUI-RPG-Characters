"""Deterministic Gen 3 character genome.

The genome is a persistent, model-independent genotype/phenotype source. It is
derived once from character inputs and then used by downstream DNA sections.
It is not a collection of unrelated prompt rerolls.
"""

import hashlib
import json


GENOME_VERSION = 1


def _unit(seed_material, key):
    payload = f"{seed_material}|{key}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return int(digest[:12], 16) / float(0xFFFFFFFFFFFF)


def _choice(seed_material, key, options):
    options = list(options or [])
    if not options:
        return None
    return options[int(_unit(seed_material, key) * len(options)) % len(options)]


def _range(seed_material, key, minimum=0.0, maximum=1.0):
    return round(minimum + (_unit(seed_material, key) * (maximum - minimum)), 4)


def make_genome(*, seed, lineage, heritage, gender, age, lineage_data, heritage_data):
    """Create a stable genome and derived phenotype state."""
    heritage = (
        None
        if heritage is None
        or not str(heritage).strip()
        or str(heritage).strip().lower() == "none"
        else str(heritage).strip()
    )
    seed_material = json.dumps({
        "version": GENOME_VERSION,
        "seed": seed,
        "lineage": lineage,
        "heritage": heritage,
        "gender": gender,
        "age": age,
    }, sort_keys=True, separators=(",", ":"))

    features = lineage_data.get("features", {})
    feature_loci = lineage_data.get("feature_loci", {})
    body_plan = dict(lineage_data.get("body_plan", {}))

    species_traits = {}
    for feature, enabled in features.items():
        species_traits[feature] = {
            "present": bool(enabled),
            "strength": _range(seed_material, f"feature:{feature}") if enabled else 0.0,
        }

    for locus, options in feature_loci.items():
        species_traits[locus] = _choice(seed_material, f"species:{locus}", options)

    compatible_heritage = bool(lineage_data.get("heritage_compatible", False))
    heritage_components = (
        dict(heritage_data.get("components", {}))
        if compatible_heritage and isinstance(heritage_data.get("components", {}), dict)
        else {}
    )
    protected_components = set(lineage_data.get("heritage_protected_components", []))
    heritage_components = {
        key: value for key, value in heritage_components.items()
        if key not in protected_components
    }
    for key, value in lineage_data.get("heritage_component_overrides", {}).items():
        heritage_components[key] = value
    heritage_phenotype = (
        ", ".join(str(value) for value in heritage_components.values())
        if heritage_components
        else ""
    )

    genome = {
        "version": GENOME_VERSION,
        "lineage": {
            "prompt": lineage_data.get("prompt", ""),
            "negative_prompt": lineage_data.get("negative_prompt", ""),
            "features": dict(lineage_data.get("features", {})),
            "traits": dict(lineage_data.get("traits", {})),
            "face_model": lineage_data.get("face_model"),
            "body_plan": body_plan,
        },
        "identity": {
            "lineage": lineage,
            "heritage": heritage,
            "heritage_compatible": compatible_heritage,
            "gender": gender,
            "age": age,
        },
        "species_traits": species_traits,
        "morphology": {
            "build": _range(seed_material, "morphology:build"),
            "height": _range(seed_material, "morphology:height"),
            "shoulder_width": _range(seed_material, "morphology:shoulder_width"),
            "body_fat": _range(seed_material, "morphology:body_fat"),
        },
        "phenotype": {
            "heritage": heritage_phenotype,
            "heritage_components": heritage_components,
            "body_plan": body_plan,
            "anatomy": {
                "head": body_plan.get("head"),
                "body": body_plan.get("body"),
                "limbs": body_plan.get("limbs"),
                "hands": body_plan.get("hands"),
                "feet": body_plan.get("feet"),
                "wings": body_plan.get("wings"),
                "tail": body_plan.get("tail"),
            },
            "hair_allowed": bool(body_plan.get("hair_allowed", True)),
            "facial_hair_allowed": bool(body_plan.get("facial_hair_allowed", True)),
        },
        "signature": hashlib.sha256(seed_material.encode("utf-8")).hexdigest(),
    }
    return genome
