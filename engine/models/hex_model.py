"""
FILE:    engine/models/hex_model.py
LAYER:   Backend
ROLE:    TypedDict schema for hex/tile data stored in the map.

DESCRIPTION:
    Defines the canonical shape of a hex cell's data dictionary.
    Every function that reads or writes hex terrain data should
    reference HexData to stay consistent.

    This is a READ-ONLY schema definition — no logic here.

DOES NOT IMPORT FROM:
    - Any UI code
    - services/
    - engine.state
"""

from typing import TypedDict, Optional, List

class HexData(TypedDict, total=False):
    """
    The canonical shape of a single hex tile's terrain data.

    Keys align with the content/Master Database terrain JSON files.
    All fields are optional to handle partially-defined or procedural hexes.
    """
    # Terrain identification
    type:       str             # Terrain type key (e.g. "forest", "plains")
    subtype:    str             # Optional subtype for variants
    label:      str             # Human-readable display name

    # Movement
    cost:       float           # Movement cost (1.0 = clear, 2.0 = terrain, 99.0 = impassable)
    passable:   bool            # False if no unit can enter

    # Combat modifiers
    cover:      float           # Cover bonus (0.0–1.0, higher = more protection)
    concealment: float          # Concealment bonus (0.0–1.0)

    # Visual
    color:      str             # Hex colour string (e.g. "#3a5f3a")
    elevation:  int             # Elevation level (0 = sea level)

    # Metadata
    zone_id:    Optional[str]   # ID of zone this hex belongs to, if any
    section_id: Optional[str]   # ID of scenario section this hex belongs to, if any
