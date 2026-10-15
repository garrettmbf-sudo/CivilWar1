"""Hex-grid utilities for a map system using offset or axial coordinates.

This module provides basic coordinate math for map generation and scenario logic.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Hex:
    q: int
    r: int


def axial_neighbors(hex_coord: Hex) -> list[Hex]:
    """Return six neighboring hexes in axial coordinates."""
    directions = [
        Hex(1, 0),
        Hex(1, -1),
        Hex(0, -1),
        Hex(-1, 0),
        Hex(-1, 1),
        Hex(0, 1),
    ]
    return [Hex(hex_coord.q + d.q, hex_coord.r + d.r) for d in directions]


def axial_distance(a: Hex, b: Hex) -> int:
    """Compute the axial distance between two hexes."""
    dq = abs(a.q - b.q)
    dr = abs(a.r - b.r)
    ds = abs((a.q + a.r) - (b.q + b.r))
    return max(dq, dr, ds) // 2


def offset_to_axial(col: int, row: int, odd_r: bool = True) -> Hex:
    """Convert offset-row coordinates to axial coordinates."""
    q = col - (row - (row & 1 if odd_r else 0)) // 2
    r = row
    return Hex(q, r)


def axial_to_offset(hex_coord: Hex, odd_r: bool = True) -> tuple[int, int]:
    """Convert axial coordinates back to offset-row coordinates."""
    col = hex_coord.q + (hex_coord.r - (hex_coord.r & 1 if odd_r else 0)) // 2
    row = hex_coord.r
    return col, row
