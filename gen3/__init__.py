"""Gen 3 structured character-DNA system.

Gen 3 lives alongside the V2 nodes while development is isolated on the
gen3-development branch.  The package is intentionally small: character DNA
is the contract that future portrait, turnaround, pose and H3 nodes consume.
"""

from .nodes.character_gen3_node import (
    NODE_CLASS_MAPPINGS as CHARACTER_GEN3_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as CHARACTER_GEN3_DISPLAY,
)
from .nodes.dna_pipe import (
    NODE_CLASS_MAPPINGS as DNA_PIPE_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as DNA_PIPE_DISPLAY,
)
from .nodes.dna_editor import (
    NODE_CLASS_MAPPINGS as DNA_EDITOR_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as DNA_EDITOR_DISPLAY,
)

NODE_CLASS_MAPPINGS = {}
NODE_CLASS_MAPPINGS.update(CHARACTER_GEN3_MAPPINGS)
NODE_CLASS_MAPPINGS.update(DNA_PIPE_MAPPINGS)
NODE_CLASS_MAPPINGS.update(DNA_EDITOR_MAPPINGS)

NODE_DISPLAY_NAME_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS.update(CHARACTER_GEN3_DISPLAY)
NODE_DISPLAY_NAME_MAPPINGS.update(DNA_PIPE_DISPLAY)
NODE_DISPLAY_NAME_MAPPINGS.update(DNA_EDITOR_DISPLAY)
