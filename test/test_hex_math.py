"""
test/test_hex_math.py
QA tests for engine.core.hex_math

Validates hex coordinate math: DIRECTION_MAP integrity, distance,
neighbor finding, and pixel↔hex round-trip conversion.
"""
import pytest
from engine.core.hex_math import Hex, HexMath, DIRECTION_MAP


# ---------------------------------------------------------------------------
# DIRECTION_MAP integrity
# ---------------------------------------------------------------------------

class TestDirectionMap:
    def test_has_six_directions(self):
        assert len(DIRECTION_MAP) == 6

    def test_all_values_are_three_tuples(self):
        for direction, vec in DIRECTION_MAP.items():
            assert len(vec) == 3, f"Direction '{direction}' vector must have 3 components"

    def test_cube_coordinates_sum_to_zero(self):
        """All hex directions must satisfy q + r + s == 0 (cube coordinate constraint)."""
        for direction, (dq, dr, ds) in DIRECTION_MAP.items():
            assert dq + dr + ds == 0, (
                f"Direction '{direction}' violates cube constraint: "
                f"{dq}+{dr}+{ds} = {dq+dr+ds}"
            )

    def test_opposite_directions_cancel(self):
        """Opposite direction pairs must sum to (0, 0, 0)."""
        opposites = [("e", "w"), ("ne", "sw"), ("nw", "se")]
        for d1, d2 in opposites:
            if d1 in DIRECTION_MAP and d2 in DIRECTION_MAP:
                v1, v2 = DIRECTION_MAP[d1], DIRECTION_MAP[d2]
                assert tuple(a + b for a, b in zip(v1, v2)) == (0, 0, 0), (
                    f"Opposite directions '{d1}'/'{d2}' do not cancel"
                )

    def test_all_directions_are_unit_length(self):
        """Each direction vector should have max(|dq|, |dr|, |ds|) == 1."""
        for direction, vec in DIRECTION_MAP.items():
            max_component = max(abs(c) for c in vec)
            assert max_component == 1, (
                f"Direction '{direction}' has non-unit magnitude: {vec}"
            )


# ---------------------------------------------------------------------------
# Hex construction
# ---------------------------------------------------------------------------

class TestHexConstruction:
    def test_hex_cube_constraint(self):
        """Hex(q, r, s) must satisfy q + r + s == 0."""
        h = Hex(1, -1, 0)
        assert h.q + h.r + h.s == 0

    def test_hex_equality(self):
        assert Hex(2, -1, -1) == Hex(2, -1, -1)

    def test_hex_inequality(self):
        assert Hex(1, 0, -1) != Hex(0, 1, -1)


# ---------------------------------------------------------------------------
# Distance
# ---------------------------------------------------------------------------

class TestDistance:
    def test_same_hex_distance_is_zero(self):
        h = Hex(3, -2, -1)
        assert HexMath.distance(h, h) == 0

    def test_adjacent_hex_distance_is_one(self):
        origin = Hex(0, 0, 0)
        for dq, dr, ds in DIRECTION_MAP.values():
            neighbor = Hex(dq, dr, ds)
            assert HexMath.distance(origin, neighbor) == 1

    def test_known_distance(self):
        a = Hex(0, 0, 0)
        b = Hex(3, -3, 0)
        assert HexMath.distance(a, b) == 3

    def test_distance_is_symmetric(self):
        a = Hex(1, -2, 1)
        b = Hex(-2, 3, -1)
        assert HexMath.distance(a, b) == HexMath.distance(b, a)

    def test_distance_far_hex(self):
        a = Hex(0, 0, 0)
        b = Hex(5, -5, 0)
        assert HexMath.distance(a, b) == 5


# ---------------------------------------------------------------------------
# Neighbors
# ---------------------------------------------------------------------------

class TestNeighbors:
    def _all_neighbors(self, h):
        """Collect all 6 neighbors using HexMath.neighbor(hex, 0..5)."""
        return [HexMath.neighbor(h, i) for i in range(6)]

    def test_origin_has_six_neighbors(self):
        origin = Hex(0, 0, 0)
        neighbors = self._all_neighbors(origin)
        assert len(neighbors) == 6

    def test_all_neighbors_are_adjacent(self):
        origin = Hex(2, -1, -1)
        for n in self._all_neighbors(origin):
            assert HexMath.distance(origin, n) == 1

    def test_neighbors_are_unique(self):
        neighbors = self._all_neighbors(Hex(0, 0, 0))
        assert len(set(neighbors)) == 6


# ---------------------------------------------------------------------------
# Pixel ↔ Hex round-trip
# ---------------------------------------------------------------------------

class TestPixelConversion:
    @pytest.mark.parametrize("q,r,s", [
        (0, 0, 0),
        (2, -1, -1),
        (-3, 2, 1),
        (5, -3, -2),
    ])
    def test_pixel_round_trip(self, q, r, s):
        """hex → pixel → hex should return the original hex (within rounding)."""
        h = Hex(q, r, s)
        hex_size = 40
        px, py = HexMath.hex_to_pixel(h, hex_size)
        recovered = HexMath.pixel_to_hex(px, py, hex_size)
        assert recovered.q == h.q, f"Round-trip q mismatch for {h}"
        assert recovered.r == h.r, f"Round-trip r mismatch for {h}"
