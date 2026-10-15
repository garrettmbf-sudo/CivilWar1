"""Axial and row-offset hex coordinate helpers for Shenandoah map tooling."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Hex:
    q: int
    r: int


def axial_neighbors(hex_coord: Hex) -> list[Hex]:
    """Return the six axial neighbors."""
    directions = [
        Hex(1, 0), Hex(1, -1), Hex(0, -1),
        Hex(-1, 0), Hex(-1, 1), Hex(0, 1),
    ]
    return [Hex(hex_coord.q + d.q, hex_coord.r + d.r) for d in directions]


def axial_distance(a: Hex, b: Hex) -> int:
    """Shortest number of edges between two axial hexes."""
    dq, dr = a.q - b.q, a.r - b.r
    return max(abs(dq), abs(dr), abs(dq + dr))


def offset_to_axial(col: int, row: int, odd_r: bool = True) -> Hex:
    """Convert a pointy-top odd-r (or even-r) offset hex to axial."""
    offset = (row - (row & 1)) // 2 if odd_r else (row + (row & 1)) // 2
    return Hex(col - offset, row)


def axial_to_offset(hex_coord: Hex, odd_r: bool = True) -> tuple[int, int]:
    """Convert an axial hex to pointy-top odd-r (or even-r) offset."""
    row = hex_coord.r
    offset = (row - (row & 1)) // 2 if odd_r else (row + (row & 1)) // 2
    return hex_coord.q + offset, row
