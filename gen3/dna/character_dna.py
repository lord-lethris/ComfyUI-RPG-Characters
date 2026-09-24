"""Serializable Character DNA primitives.

DNA is kept JSON-safe on purpose.  A workflow should be able to pass the
character state between nodes without depending on a Python class surviving
serialization or execution boundaries.
"""

from copy import deepcopy
import hashlib
import json

from .dna_schema import DNA_SECTIONS, DNA_SECTION_DEFINITIONS

CHARACTER_DNA_VERSION = 1
SOURCE_SIGNATURE_VERSION = 1


def make_source_signature(section_id, inputs):
    """Return a deterministic signature for the upstream inputs of one section."""
    payload = {
        "version": SOURCE_SIGNATURE_VERSION,
        "section": section_id,
        "inputs": inputs or {},
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def make_empty_section(section_id):
    """Create a stable, empty section record."""
    if section_id not in DNA_SECTION_DEFINITIONS:
        raise ValueError(f"Unknown DNA section: {section_id}")

    definition = DNA_SECTION_DEFINITIONS[section_id]
    return {
        "id": section_id,
        "label": definition["label"],
        "description": definition["description"],
        "values": {},
        "traits": [],
        "loci": [],
        "source": None,
        "source_inputs": {},
        "source_signature": None,
    }


def make_character_dna(*, selections=None, seed=None, source="RPG Character Gen 3",
                       sections=None, genome=None):
    """Build a complete Character DNA document with every stable section."""
    selections = deepcopy(selections or {})
    supplied_sections = deepcopy(sections or {})

    document = {
        "dna_version": CHARACTER_DNA_VERSION,
        "type": "RPG_CHARACTER_DNA",
        "seed": seed,
        "source": source,
        "selections": selections,
        "genome": deepcopy(genome) if isinstance(genome, dict) else None,
        "sections": {},
    }

    for section_id in DNA_SECTIONS:
        section = supplied_sections.get(section_id)
        if isinstance(section, dict):
            base = make_empty_section(section_id)
            base.update(section)
            base["id"] = section_id
            document["sections"][section_id] = base
        else:
            document["sections"][section_id] = make_empty_section(section_id)

    return document
