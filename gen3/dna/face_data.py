"""Gen 3 semantic face DNA definitions.

Face data is deliberately model-independent. These descriptors describe the
character's facial structure; downstream prompt adapters decide how to render
them for a particular model.
"""

FACE_LOCUS_DATA = {
    "face_shape": {
        "label": "Face Shape",
        "options": {
            "Oval": {"prompt": "an oval face shape"},
            "Round": {"prompt": "a round face shape"},
            "Square": {"prompt": "a square face shape"},
            "Heart": {"prompt": "a heart-shaped face"},
            "Diamond": {"prompt": "a diamond-shaped face"},
            "Oblong": {"prompt": "an oblong face shape"},
            "Angular": {"prompt": "an angular face shape"},
        },
    },
    "jaw_shape": {
        "label": "Jaw Shape",
        "options": {
            "Soft": {"prompt": "a soft jawline"},
            "Rounded": {"prompt": "a rounded jawline"},
            "Defined": {"prompt": "a defined jawline"},
            "Square": {"prompt": "a square jawline"},
            "Tapered": {"prompt": "a tapered jawline"},
            "Strong": {"prompt": "a strong jawline"},
        },
    },
    "cheekbones": {
        "label": "Cheekbones",
        "options": {
            "Subtle": {"prompt": "subtle cheekbones"},
            "Balanced": {"prompt": "balanced cheekbones"},
            "High": {"prompt": "high cheekbones"},
            "Prominent": {"prompt": "prominent cheekbones"},
            "Broad": {"prompt": "broad cheekbones"},
            "Angular": {"prompt": "angular cheekbones"},
        },
    },
    "chin": {
        "label": "Chin",
        "options": {
            "Rounded": {"prompt": "a rounded chin"},
            "Soft": {"prompt": "a soft chin"},
            "Defined": {"prompt": "a defined chin"},
            "Square": {"prompt": "a square chin"},
            "Pointed": {"prompt": "a pointed chin"},
            "Broad": {"prompt": "a broad chin"},
        },
    },
    "nose_shape": {
        "label": "Nose Shape",
        "options": {
            "Straight": {"prompt": "a straight nose"},
            "Slightly Upturned": {"prompt": "a slightly upturned nose"},
            "Aquiline": {"prompt": "an aquiline nose"},
            "Roman": {"prompt": "a Roman nose"},
            "Button": {"prompt": "a button nose"},
            "Broad": {"prompt": "a broad nose"},
            "Narrow": {"prompt": "a narrow nose"},
        },
    },
    "eye_shape": {
        "label": "Eye Shape",
        "options": {
            "Almond": {"prompt": "almond-shaped eyes"},
            "Round": {"prompt": "round eyes"},
            "Hooded": {"prompt": "hooded eyes"},
            "Upturned": {"prompt": "upturned eyes"},
            "Downturned": {"prompt": "downturned eyes"},
            "Deep Set": {"prompt": "deep-set eyes"},
            "Wide Set": {"prompt": "wide-set eyes"},
        },
    },
    "brow_shape": {
        "label": "Brow Shape",
        "options": {
            "Straight": {"prompt": "straight eyebrows"},
            "Soft Arch": {"prompt": "softly arched eyebrows"},
            "High Arch": {"prompt": "high-arched eyebrows"},
            "Rounded": {"prompt": "rounded eyebrows"},
            "Angular": {"prompt": "angular eyebrows"},
            "Flat": {"prompt": "flat eyebrows"},
        },
    },
    "lip_shape": {
        "label": "Lip Shape",
        "options": {
            "Balanced": {"prompt": "balanced lips"},
            "Full": {"prompt": "full lips"},
            "Thin": {"prompt": "thin lips"},
            "Wide": {"prompt": "wide lips"},
            "Small": {"prompt": "small lips"},
            "Defined Cupid's Bow": {"prompt": "lips with a defined cupid's bow"},
            "Full Lower Lip": {"prompt": "lips with a fuller lower lip"},
        },
    },
}
