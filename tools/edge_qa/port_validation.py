"""Typed reciprocal six-edge connectivity gate for CivilWar1 flat-top hexes.

This module checks authored data; it NEVER infers transport routes from concept art.
Edge ids for flat-top, clockwise: 0=N, 1=NE, 2=SE, 3=S, 4=SW, 5=NW.
An adjacent hex uses the opposite edge: (edge + 3) modulo 6.
A property's offset is measured 0..1 along each side clockwise. Since two
adjacent hexes traverse their shared edge in opposite directions, offsets
must satisfy A.position == 1-B.position.
"""
from __future__ import annotations
from typing import Any

PORT_KINDS = frozenset({"pike", "road", "farm_lane", "rail", "river", "creek", "wood_fence", "stone_wall"})
VERIFIED_CROSSINGS = frozenset({"stone_bridge", "wooden_bridge", "covered_bridge", "trestle", "ford", "ferry"})


def validate_network(document: dict[str, Any], tolerance: float = .015, elevation_tolerance_m: float = .25) -> list[str]:
    """Return actionable failures; empty means explicit data passes topology checks.

    A successful result DOES NOT by itself certify historical coordinates or native
    Hex of Steel sprite export. Art edge colors require a separate seam QA pass.
    """
    tiles: dict = document.get("tiles", {})
    neighbors: list[dict] = document.get("adjacencies", [])
    errors: list[str] = []
    linked: set[tuple[str, int]] = set()
    external: set[tuple[str, int]] = {(str(v["tile"]), int(v["edge"])) for v in document.get("perimeter_exits", [])}
    def ports(t: dict, e: int):
        edges = t.get("ports", {})
        return edges.get(str(e), [])

    for tile_id, item in tiles.items():
        if item.get("orientation") != "flat_top":
            errors.append(f"{tile_id}: shape must be flat_top, got {item.get('orientation')}")
        for s, records in item.get("ports", {}).items():
            try: edge = int(s)
            except ValueError: errors.append(f"{tile_id}: invalid edge label {s}"); continue
            if edge not in range(6): errors.append(f"{tile_id}: edge {edge} out of range")
            for port in records:
                if port.get("kind") not in PORT_KINDS:
                    errors.append(f"{tile_id}:{edge}: unknown feature {port.get('kind')}")
                if not (0 <= float(port.get("position", -1)) <= 1):
                    errors.append(f"{tile_id}:{edge}: port position outside 0..1")
                if float(port.get("width",0)) <= 0:
                    errors.append(f"{tile_id}:{edge}: feature width must be positive")
        # Overlay crossings must have explicit type and historical provenance.
        for cross in item.get("crossings", []):
            if cross.get("type") not in VERIFIED_CROSSINGS:
                errors.append(f"{tile_id}: crossing not verified type ({cross.get('type')})")
            if not cross.get("source"):
                errors.append(f"{tile_id}: crossing missing dated historical source")

    for link in neighbors:
        ida = str(link["a"]["tile"]); idb = str(link["b"]["tile"])
        ea = int(link["a"]["edge"]); eb = int(link["b"]["edge"])
        if ida not in tiles or idb not in tiles:
            errors.append(f"Missing tile in link {ida}:{ea} <-> {idb}:{eb}");continue
        if ea not in range(6) or eb not in range(6):
            errors.append(f"Invalid edge in {ida}:{ea} <-> {idb}:{eb}");continue
        if eb != (ea+3)%6:
            errors.append(f"Wrong opposite edge: {ida}:{ea} must meet {idb}:{(ea+3)%6} (not {eb})")
        if (ida,ea) in linked or (idb,eb) in linked:
            errors.append(f"Duplicate adjacency for {ida}:{ea} or {idb}:{eb}")
        linked.add((ida,ea));linked.add((idb,eb))
        aa=ports(tiles[ida],ea); bb=ports(tiles[idb],eb)
        if len(aa)!=len(bb):
            errors.append(f"DANGLING FEATURE: {ida}:{ea} has {len(aa)} exits, {idb}:{eb} has {len(bb)}")
        unmatched=list(bb)
        for ap in aa:
            kind=ap.get("kind")
            found=None
            for bp in unmatched:
                if bp.get("kind")==kind and abs(float(ap.get("position",.5))+float(bp.get("position",.5))-1) <= tolerance:
                    found=bp;break
            if found is None:
                errors.append(f"DISCONNECTED {kind}: {ida}:{ea} -> {idb}:{eb} missing matching typed/positioned port")
                continue
            unmatched.remove(found)
            if abs(float(ap.get("width",0))-float(found.get("width",0)))>tolerance:
                errors.append(f"WIDTH SEAM: {ida}:{ea} -> {idb}:{eb} ({kind})")
            if ap.get("material") != found.get("material"):
                errors.append(f"MATERIAL SEAM: {ida}:{ea} -> {idb}:{eb} ({kind})")
        ha=tiles[ida].get("heights",{}).get(str(ea))
        hb=tiles[idb].get("heights",{}).get(str(eb))
        if ha is None or hb is None:
            errors.append(f"MISSING ELEVATION PROFILE: {ida}:{ea} <-> {idb}:{eb}")
        elif len(ha)!=len(hb) or any(abs(float(a)-float(b))>elevation_tolerance_m for a,b in zip(ha,reversed(hb))):
            errors.append(f"ELEVATION CRACK: {ida}:{ea} <-> {idb}:{eb}")

    for tile_id,item in tiles.items():
        for k,pp in item.get("ports",{}).items():
            p=(tile_id,int(k))
            if pp and p not in linked and p not in external:
                errors.append(f"UNPAIRED INTERIOR EXIT: {tile_id}:{k}")
    return errors