"""
FILE: engine/core/hex_math.py
ROLE: Foundation library for Hexagonal Grid Mathematics.

DESCRIPTION:
This file contains the "brain" for all hexagonal calculations in the game. 
Because humans usually think in squares (rows and columns), but our game uses hexagons, 
we need special math to:
1. Figure out which hexagon a user clicked on with their mouse.
2. Determine where to draw a hexagon on the screen.
3. Calculate distances between units.
4. Find neighboring hexagons (North, South, etc.).
5. Draw straight lines and polygons across the grid.

We use 'Cube Coordinates' (q, r, s) internally because they make hex math 
behave almost exactly like 3D math, which is much simpler than 2D hex math.
"""

"""
FILE: engine/core/hex_math.py
ROLE: The "Mathematician" (Coordinate System).

DESCRIPTION:
    This file handles all things Hexagonal. It uses the "Cube Coordinate" 
    system (q, r, s) which makes calculations for distance, rotation, 
    and lines extremely simple.
    
    If you're wondering how the grid 'works', this is the file.
"""

import math
from collections import namedtuple

# A Hex is a simple container for three numbers: q, r, and s.
# In a cube coordinate system, these three must always add up to zero (q + r + s = 0).
Hex = namedtuple("Hex", ["q", "r", "s"])

# Flat-top hex direction map (cube coordinate deltas)
# Matches HexMath.neighbor() direction indices:
#   0=E, 1=NE, 2=NW, 3=W, 4=SW, 5=SE
DIRECTION_MAP = {
    "east":      (1,  0, -1),   # dir 0
    "northeast": (1, -1,  0),   # dir 1
    "northwest": (0, -1,  1),   # dir 2
    "west":      (-1, 0,  1),   # dir 3
    "southwest": (-1, 1,  0),   # dir 4
    "southeast": (0,  1, -1),   # dir 5
}

class HexMath:
    """
    A collection of tools to handle everything related to hexagons.
    Orientation: 'Flat-Top' (the hexagon has flat sides on the left and right).
    """
    
    @staticmethod
    def create_hex(q: int, r: int) -> Hex:
        """
        Creates a hexagon coordinate from just two numbers (Axial q and r).
        The third number (s) is automatically calculated to keep the math balanced.
        """
        return Hex(q, r, -q - r)

    @staticmethod
    def add(a: Hex, b: Hex) -> Hex:
        """Adds two hexagon locations together (useful for moving or offsets)."""
        if not hasattr(a, 'q'): a = Hex(a[0], a[1], a[2] if len(a) > 2 else -a[0]-a[1])
        if not hasattr(b, 'q'): b = Hex(b[0], b[1], b[2] if len(b) > 2 else -b[0]-b[1])
        return Hex(a.q + b.q, a.r + b.r, a.s + b.s)

    @staticmethod
    def subtract(a: Hex, b: Hex) -> Hex:
        """Finds the difference between two hexagon locations."""
        if not hasattr(a, 'q'): a = Hex(a[0], a[1], a[2] if len(a) > 2 else -a[0]-a[1])
        if not hasattr(b, 'q'): b = Hex(b[0], b[1], b[2] if len(b) > 2 else -b[0]-b[1])
        return Hex(a.q - b.q, a.r - b.r, a.s - b.s)

    @staticmethod
    def scale(a: Hex, k: int) -> Hex:
        """Multiplies a hexagon coordinate by a number (useful for expanding circles)."""
        return Hex(a.q * k, a.r * k, a.s * k)

    @staticmethod
    def length(hex: Hex) -> int:
        """Calculates the distance from the center of the world (0,0,0) to this hexagon."""
        if not hasattr(hex, 'q'):
            hex = Hex(hex[0], hex[1], hex[2] if len(hex) > 2 else -hex[0]-hex[1])
        return int((abs(hex.q) + abs(hex.r) + abs(hex.s)) / 2)

    @staticmethod
    def distance(a: Hex, b: Hex) -> int:
        """Finds how many hexagons apart two points are (count of steps to get from A to B)."""
        return HexMath.length(HexMath.subtract(a, b))

    @staticmethod
    def neighbor(hex: Hex, direction: int) -> Hex:
        """
        Finds the hexagon right next to the current one in a specific direction.
        
        Directions (0 to 5):
        0: East (Right)
        1: North-East (Top-Right)
        2: North-West (Top-Left)
        3: West (Left)
        4: South-West (Bottom-Left)
        5: South-East (Bottom-Right)
        """
        # These are the mathematical 'steps' to take for each of the 6 directions
        hex_directions = [
            Hex(1, 0, -1), Hex(1, -1, 0), Hex(0, -1, 1),
            Hex(-1, 0, 1), Hex(-1, 1, 0), Hex(0, 1, -1)
        ]
        d = hex_directions[direction % 6]
        return HexMath.add(hex, d)

    @staticmethod
    def hex_to_pixel(hex: Hex, size: float) -> tuple[float, float]:
        """
        CONVERSION: Hex coordinates -> Screen coordinates (Pixels).
        Used by the game to know WHERE to draw a hexagon on your screen.
        'size' is the distance from the center of the hex to one of its corners.
        """
        if not hasattr(hex, 'q'):
            # Resilience Check: If a raw list [q,r,s] was passed, convert back home.
            hex = Hex(hex[0], hex[1], hex[2] if len(hex) > 2 else -hex[0]-hex[1])
            
        q = hex.q
        r = hex.r
        x = size * (3/2 * q)
        y = size * (math.sqrt(3)/2 * q + math.sqrt(3) * r)
        return (x, y)

    @staticmethod
    def pixel_to_hex(x: float, y: float, size: float) -> Hex:
        """
        CONVERSION: Screen coordinates (Pixels) -> Hex coordinates.
        Used when you click the mouse to figure out WHICH hexagon was clicked.
        """
        q = (2/3 * x) / size
        r = (-1/3 * x + math.sqrt(3)/3 * y) / size
        # Fractional results are rounded to the nearest solid hexagon
        return HexMath.round_hex(q, r, -q-r)

    @staticmethod
    def round_hex(frac_q: float, frac_r: float, frac_s: float) -> Hex:
        """
        Rounds floating-point (decimal) coordinates to the nearest whole Hexagon.
        Ensures the q + r + s = 0 rule is maintained after rounding.
        """
        q = round(frac_q)
        r = round(frac_r)
        s = round(frac_s)

        q_diff = abs(q - frac_q)
        r_diff = abs(r - frac_r)
        s_diff = abs(s - frac_s)

        # Adjust the component that had the biggest rounding error to maintain balance
        if q_diff > r_diff and q_diff > s_diff:
            q = -r - s
        elif r_diff > s_diff:
            r = -q - s
        else:
            s = -q - r

        return Hex(int(q), int(r), int(s))

    @staticmethod
    def get_corners(center_x: float, center_y: float, size: float) -> list[tuple[float, float]]:
        """
        Returns the pixel positions of all 6 corners of a hexagon.
        Used for drawing the visual shape on the screen.
        """
        corners = []
        for i in range(6):
            angle_deg = 60 * i
            angle_rad = math.pi / 180 * angle_deg
            corners.append((
                center_x + size * math.cos(angle_rad),
                center_y + size * math.sin(angle_rad)
            ))
        return corners

    @staticmethod
    def is_aligned(a: Hex, b: Hex) -> bool:
        """Checks if two hexagons are in a straight line along any of the 3 axes (q, r, or s)."""
        return a.q == b.q or a.r == b.r or a.s == b.s

    @staticmethod
    def line(start: Hex, end: Hex) -> list[Hex]:
        """
        Finds every hexagon in a straight line from 'start' to 'end'.
        Uses 'linear interpolation' (calculating points along the line segment).
        """
        dist = HexMath.distance(start, end)
        if dist == 0:
            return [start]
        
        results = []
        for i in range(int(dist) + 1):
            t = i / dist if dist > 0 else 0
            # Calculate a point 't' percentage of the way along the line
            q = start.q + (end.q - start.q) * t
            r = start.r + (end.r - start.r) * t
            s = start.s + (end.s - start.s) * t
            results.append(HexMath.round_hex(q, r, s))
        
        return results

    @staticmethod
    def get_shared_corner(hex1: Hex, hex2: Hex, size: float) -> tuple[float, float, float, float]:
        """
        Finds the two specific corners that two adjacent hexagons share.
        Useful for drawing clean borders or paths between hexagons.
        """
        # If they aren't neighbors, we just return the midpoint between their centers as a fallback
        if HexMath.distance(hex1, hex2) != 1:
            wx1, wy1 = HexMath.hex_to_pixel(hex1, size)
            wx2, wy2 = HexMath.hex_to_pixel(hex2, size)
            mid_x = (wx1 + wx2) / 2
            mid_y = (wy1 + wy2) / 2
            return (mid_x, mid_y, mid_x, mid_y)
        
        # Determine the direction from hex1 to hex2
        direction = -1
        for i in range(6):
            if HexMath.neighbor(hex1, i) == hex2:
                direction = i
                break
        
        if direction == -1:
            wx1, wy1 = HexMath.hex_to_pixel(hex1, size)
            wx2, wy2 = HexMath.hex_to_pixel(hex2, size)
            mid_x = (wx1 + wx2) / 2
            mid_y = (wy1 + wy2) / 2
            return (mid_x, mid_y, mid_x, mid_y)
        
        # Each direction corresponds to a specific pair of corners in our flat-top system
        cx1, cy1 = HexMath.hex_to_pixel(hex1, size)
        corners1 = HexMath.get_corners(cx1, cy1, size)
        
        corner_pairs = [
            (0, 5),  # Right edge
            (0, 1),  # Bottom-right edge
            (1, 2),  # Bottom-left edge
            (2, 3),  # Left edge
            (3, 4),  # Top-left edge
            (4, 5),  # Top-right edge
        ]
        
        c1_idx, c2_idx = corner_pairs[direction]
        x1, y1 = corners1[c1_idx]
        x2, y2 = corners1[c2_idx]
        
        return (x1, y1, x2, y2)

    @staticmethod
    def get_neighbor_direction(h1: Hex, h2: Hex) -> int:
        """Returns the direction number (0-5) to get from h1 to h2."""
        for i in range(6):
            if HexMath.neighbor(h1, i) == h2:
                return i
        return -1

    @staticmethod
    def get_hexes_in_polygon(vertices: list[Hex]) -> list[Hex]:
        """
        Finds all hexagons that are trapped inside a closed loop (polygon) of vertices.
        Useful for 'Side Assignment' or 'Zone' creation.
        """
        if not vertices or len(vertices) < 3:
            return vertices 

        # We use a standard 'ray casting' algorithm.
        # We look at every hex in the bounding area and check if it's 'inside' the shape.
        size = 1.0
        pixel_verts = [HexMath.hex_to_pixel(h, size) for h in vertices]
        
        # Find the bounding box limits
        q_min = min(h.q for h in vertices)
        q_max = max(h.q for h in vertices)
        r_min = min(h.r for h in vertices)
        r_max = max(h.r for h in vertices)
        
        inside_hexes = []
        
        # Scan every hex within the rectangle containing our polygon
        for q in range(q_min - 1, q_max + 2):
            for r in range(r_min - 1, r_max + 2):
                h = Hex(q, r, -q-r)
                px, py = HexMath.hex_to_pixel(h, size)
                
                # Check if this center point is inside the polygon
                if HexMath.is_point_in_polygon(px, py, pixel_verts):
                    inside_hexes.append(h)
                    
        return inside_hexes

    @staticmethod
    def is_point_in_polygon(x: float, y: float, poly: list[tuple[float, float]]) -> bool:
        """
        Classic 'Ray Casting' algorithm to check if a single point (x,y)
        is inside a closed loop of points.
        """
        n = len(poly)
        inside = False
        p1x, p1y = poly[0]
        for i in range(n + 1):
            p2x, p2y = poly[i % n]
            # If the ray intersects an edge, toggle the 'inside' state
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    @staticmethod
    def cube_to_offset(h: Hex) -> tuple[int, int]:
        """
        CONVERSION: Cube (internal) -> Offset (human readable grid like 10,5).
        Used for displaying coordinates to the user.
        """
        col = h.q
        row = h.r + (h.q - (h.q & 1)) // 2
        return (col, row)

    @staticmethod
    def offset_to_cube(col: int, row: int) -> Hex:
        """
        CONVERSION: Offset (human readable 10,5) -> Cube (internal).
        Used when you manually type coordinates or load them from a simple file.
        """
        q = col
        r = row - (col - (col & 1)) // 2
        s = -q - r
        return Hex(q, r, s)

    @staticmethod
    def spiral(center: Hex, radius: int) -> list:
        """
        Returns all hexes within 'radius' rings of 'center', including center.
        Ring 0 = just center; ring 1 = 6 neighbors; ring N = (N*6) more.
        Safe for headless use — no UI dependencies.
        """
        results = [center]
        if radius <= 0:
            return results
        # Walk each ring from 1..radius
        for r in range(1, radius + 1):
            # Start at the 'west' corner of this ring
            h = HexMath.add(center, HexMath.scale(Hex(-1, 0, 1), r))
            # Walk around 6 sides
            for direction in range(6):
                for _ in range(r):
                    results.append(h)
                    h = HexMath.neighbor(h, direction)
        return results

