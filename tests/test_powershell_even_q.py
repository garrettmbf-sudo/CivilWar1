"""PowerShell map tools use the same native even-q math as src/hex_utils.py.

Two layers:
* Formula checks (always run): parse tools/powershell/*.ps1 and compare constants, neighbour
  tables and the absence of the old square-grid / mirrored code with hex_utils.
* Execution checks (need pwsh): run HexEvenQ.ps1, valley_map_data.ps1 and the hex part of
  build_valley_map.ps1 under PowerShell 7 and compare every result with hex_utils on sample cells.
  These are skipped when pwsh is missing, and on CI unless RUN_PWSH_TESTS=1 (PowerShell
  tooling is not part of CI by project decision).
"""
from __future__ import annotations

import json
import math
import os
import random
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from src import hex_utils as hu

ROOT = Path(__file__).resolve().parents[1]
PS = ROOT / "tools" / "powershell"
MOD = PS / "HexEvenQ.ps1"


def _ps_array(text: str, name: str) -> list[int]:
    m = re.search(r"\$script:%s\s*=\s*@\(([^)]*)\)" % re.escape(name), text)
    assert m, name
    return [int(v) for v in re.findall(r"-?\d+", m.group(1))]


def _ps_number(text: str, name: str) -> float:
    m = re.search(r"\$script:%s\s*=\s*([0-9.]+)" % re.escape(name), text)
    assert m, name
    return float(m.group(1))


# ---------------------------------------------------------------- formula checks (no pwsh)
def test_module_constants_match_hex_utils():
    t = MOD.read_text()
    assert _ps_number(t, "HexGameColPitch") == hu.GAME_COL_PITCH
    assert _ps_number(t, "HexGameRowPitch") == hu.GAME_ROW_PITCH
    assert _ps_number(t, "HexGameEvenShift") == hu.GAME_EVEN_COL_SHIFT


def test_module_neighbour_tables_match_hex_utils():
    t = MOD.read_text()
    even, odd = _ps_array(t, "HexEvenColDeltas"), _ps_array(t, "HexOddColDeltas")
    assert list(zip(even[::2], even[1::2])) == [tuple(d) for d in hu._EVEN_COL_DELTAS]
    assert list(zip(odd[::2], odd[1::2])) == [tuple(d) for d in hu._ODD_COL_DELTAS]
    assert "($col % 2 -eq 0)" in t  # even columns are the north-shifted ones


@pytest.mark.parametrize("script,module", [("beautify_map.ps1", "HexEvenQ.ps1"), ("ValleyFrame.ps1", "HexEvenQ.ps1"),
                                           ("valley_map_data.ps1", "ValleyFrame.ps1"),
                                           ("build_valley_map.ps1", "valley_map_data.ps1")])
def test_tools_dot_source_the_shared_module(script, module):
    assert ". (Join-Path $PSScriptRoot '%s')" % module in (PS / script).read_text()


def test_one_frame_for_both_scripts():
    # bounds live only in ValleyFrame.ps1; the builder has no frame or hand-placed geography of its own
    for script in ("valley_map_data.ps1", "build_valley_map.ps1"):
        t = (PS / script).read_text()
        assert not re.search(r"^\$(south|north|west|east)Bound\s*=", t, re.M), script
    b = (PS / "build_valley_map.ps1").read_text()
    assert "37.90" not in b.replace("(Until 2026-10-17 this script had its own hand-placed copy in an old 37.90 N frame", "")
    assert not re.search(r"\$valleyPike = @\(\d", b) and not re.search(r'X=\d+;\s*Y=\d+', b)


def _ps_table(text, name):
    """Edge-pair -> variant from either $name["a,b"] = n lines or a $name = @{ "a,b"=n; ... } literal."""
    out = {k: int(v) for k, v in re.findall(r'\$%s\["([0-9,]+)"\]\s*=\s*(\d+)' % name, text)}
    m = re.search(r"\$%s\s*=\s*@\{([^}]*)\}" % name, text)
    if m:
        out.update({k: int(v) for k, v in re.findall(r'"([0-9,]+)"\s*=\s*(\d+)', m.group(1))})
    return out


# Pinned by Major Hotchkiss (PR #21 review): River PNG edge sampling + TileEditorGO.SetAutoRivers,
# and TileEditorGO.SetAutoRoads (roads use only Road1-5 and Road10-13). Ports 0=N 1=NE 2=SE 3=S 4=SW 5=NW.
RIVER_TABLE = {"0,3": 1, "1,4": 2, "2,5": 3, "1,5": 4, "2,4": 5, "0,4": 6, "0,2": 7, "1,3": 8, "3,5": 9}
RIVER_JUNCTIONS = {"1,3,5": 10, "0,2,4": 11, "0,1,3": 12}
RIVER_SHARP = {"0,1": 4, "1,2": 7, "2,3": 5, "3,4": 5, "4,5": 6, "0,5": 4}
ROAD_TABLE = {"0,3": 1, "1,5": 2, "2,4": 3, "1,4": 4, "2,5": 5, "3,5": 10, "0,4": 11, "0,2": 12, "1,3": 13}
ROAD_SHARP = {"0,1": 2, "1,2": 12, "2,3": 3, "3,4": 3, "4,5": 11, "0,5": 2}


def test_beautify_river_and_road_tables_are_pinned():
    t = (PS / "beautify_map.ps1").read_text()
    assert _ps_table(t, "dirLookup") == RIVER_TABLE
    assert _ps_table(t, "junctionLookup") == RIVER_JUNCTIONS
    assert _ps_table(t, "sharpFallback") == RIVER_SHARP
    assert _ps_table(t, "roadLookup") == ROAD_TABLE
    assert _ps_table(t, "roadSharpFallback") == ROAD_SHARP
    assert set(ROAD_TABLE.values()) | set(ROAD_SHARP.values()) <= {1, 2, 3, 4, 5, 10, 11, 12, 13}
    road_pass = t[t.index("# ===== PASS 2: FIX ROAD DIRECTIONS"):t.index("# ===== PASS 3")]
    assert "$dirLookup" not in road_pass and "$sharpFallback" not in road_pass
    assert "may be flipped" not in t and "re-check in game" not in t


def test_old_layouts_are_gone():
    b = (PS / "beautify_map.ps1").read_text()
    assert "$evenOff" not in b and "$oddOff" not in b          # old mirrored N=(0,-1) tables
    v = (PS / "valley_map_data.ps1").read_text()
    assert "Get-HexX" not in v and "Get-HexY" not in v          # old independent x/y rounding
    g = (PS / "build_valley_map.ps1").read_text()
    assert "$e2 = 2 * $err" not in g                            # old square-grid Bresenham
    assert "$W = 105" not in g


# ---------------------------------------------------------------- execution checks (pwsh)
def _pwsh():
    if os.environ.get("CI") and not os.environ.get("RUN_PWSH_TESTS"):
        pytest.skip("PowerShell tooling is not run in CI (set RUN_PWSH_TESTS=1 to enable)")
    exe = os.environ.get("PWSH") or shutil.which("pwsh") or ("/workspace/pwsh/pwsh" if Path("/workspace/pwsh/pwsh").exists() else None)
    if not exe:
        pytest.skip("pwsh not installed")
    return exe


def _run(script: str) -> str:
    r = subprocess.run([_pwsh(), "-NoProfile", "-NonInteractive", "-Command", script],
                       capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stderr
    return r.stdout


def _sample():
    rnd = random.Random(1862)
    cells = [(c, r) for c in range(-3, 21) for r in range(-3, 21)]
    pts = [(rnd.uniform(-5, 120), rnd.uniform(-5, 140)) for _ in range(400)]
    pts += [hu.hex_center(c, r) for c, r in cells[::7]]  # exact centres too
    pairs = [((rnd.randint(0, 122), rnd.randint(0, 140)), (rnd.randint(0, 122), rnd.randint(0, 140))) for _ in range(150)]
    return cells, pts, pairs


def test_module_matches_hex_utils_on_samples(tmp_path):
    cells, pts, pairs = _sample()
    inp = tmp_path / "in.json"
    inp.write_text(json.dumps({"cells": cells, "pts": pts, "pairs": pairs}))
    out = json.loads(_run(f"""
. '{MOD}'
$in = Get-Content -Raw '{inp}' | ConvertFrom-Json
$res = @{{ nb=@(); ctr=@(); game=@(); ax=@(); dist=@(); snap=@(); line=@() }}
foreach ($c in $in.cells) {{
  $col=[int]$c[0]; $row=[int]$c[1]
  $res.nb   += ,@(0..5 | ForEach-Object {{ ,(Get-HexNeighbor $col $row $_) }})
  $res.ctr  += ,(Get-HexCenter $col $row 1.0)
  $res.game += ,(Get-HexGamePosition $col $row)
  $res.ax   += ,(ConvertTo-HexAxial $col $row)
  $res.dist += (Get-HexDistance 0 0 $col $row)
}}
foreach ($p in $in.pts) {{ $res.snap += ,(Get-HexFromXY ([double]$p[0]) ([double]$p[1]) 1.0) }}
foreach ($pr in $in.pairs) {{ $res.line += ,@((Get-HexLine $pr[0][0] $pr[0][1] $pr[1][0] $pr[1][1]) | ForEach-Object {{ ,@($_[0], $_[1]) }}) }}
$res | ConvertTo-Json -Depth 6 -Compress
"""))
    for i, (c, r) in enumerate(cells):
        assert [tuple(n) for n in out["nb"][i]] == hu.offset_neighbors(c, r), (c, r)
        assert tuple(out["ctr"][i]) == pytest.approx(hu.hex_center(c, r), abs=1e-12)
        assert tuple(out["game"][i]) == pytest.approx(hu.game_position(c, r), abs=1e-12)
        a = hu.offset_to_axial(c, r)
        assert tuple(out["ax"][i]) == (a.q, a.r)
        assert out["dist"][i] == hu.offset_distance((0, 0), (c, r))
    for p, s in zip(pts, out["snap"]):
        assert tuple(s) == hu.point_to_offset(*p), p
    for (a, b), line in zip(pairs, out["line"]):
        assert [tuple(x) for x in line] == hu.hex_line(a, b), (a, b)


def test_valley_map_data_positions_match_hex_utils():
    text = (PS / "valley_map_data.ps1").read_text()
    frame = (PS / "ValleyFrame.ps1").read_text()
    out = _run(f"& '{PS / 'valley_map_data.ps1'}'")
    m = re.search(r"Size: (\d+) x (\d+) hexes", out)
    lat = lambda n: float(re.search(r"\$%s\s*=\s*([0-9.]+)" % n, frame).group(1))  # noqa: E731
    south, north, west, east = lat("southBound"), lat("northBound"), lat("westBound"), lat("eastBound")
    mi_lon = 69.0 * math.cos(38.75 * math.pi / 180)
    assert (int(m.group(1)), int(m.group(2))) == (
        round((west - east) * mi_lon / hu.COL_PITCH_RATIO) + 1, round((north - south) * 69.0) + 1)
    towns = re.findall(r'Name="([^"]+)";\s*Lat=([0-9.]+);\s*Lon=([0-9.]+);\s*Type="[^"]+";\s*VP=\$\w+;\s*Primary=\$true', text)
    assert len(towns) >= 10
    for name, la, lo in towns:
        want = hu.point_to_offset((west - float(lo)) * mi_lon, (float(la) - south) * 69.0)
        row = re.search(r"^%s\s+(-?\d+)\s+(-?\d+)\s" % re.escape(name), out, re.M)
        assert row and (int(row.group(1)), int(row.group(2))) == want, name
    pike = re.search(r"Valley Pike: (.*)", out).group(1)
    assert len(re.findall(r"\((\d+),(\d+)\)", pike)) == 19


def test_build_valley_map_hex_part_matches_hex_utils():
    src = (PS / "build_valley_map.ps1").read_text()
    part = src[src.index("# ===== HEX GRID"):src.index("# ===== LOAD TEMPLATE =====")]
    part = part.replace("$PSScriptRoot", f"'{PS}'")
    out = json.loads(_run(part + r"""
$res = @{ W=$W; H=$H; road=@($roadSet); river=@($riverSet);
          towns=@($towns | ForEach-Object { ,@($_.N, $_.D, $_.X, $_.Y) }) }
$res | ConvertTo-Json -Depth 5 -Compress
""").strip().splitlines()[-1])  # the script part also prints its terrain summary
    assert (out["W"], out["H"]) == (122, 140)  # same frame and rounding as valley_map_data.ps1
    W, H = out["W"], out["H"]

    def trace(name):
        wps = _vmd_trace(name)
        cells = set()
        for a, b in zip(wps, wps[1:]):
            for c, r in hu.hex_line(a, b):
                if 0 <= c < W and 0 <= r < H:
                    cells.add(r * W + c)
        return cells

    assert set(out["road"]) == trace("valleyPike")
    rivers = set()
    for n in ("southFork", "northFork", "mainShenandoah", "potomac", "southRiver"):
        rivers |= trace(n)
    assert set(out["river"]) == rivers
    # identical town hexes in both scripts: the builder vs valley_map_data.ps1's own run
    data = _run(f"& '{PS / 'valley_map_data.ps1'}'")
    places = _vmd_places()
    for n, d, x, y in out["towns"]:
        assert (x, y) == places[d], n
        row = re.search(r"^%s\s+(-?\d+)\s+(-?\d+)\s" % re.escape(d), data, re.M)
        if row:  # primary places are printed by the data script
            assert (int(row.group(1)), int(row.group(2))) == (x, y), n
        assert 0 <= x < W and 0 <= y < H, n
    assert len(out["towns"]) == 22
    assert dict((n, (x, y)) for n, _, x, y in out["towns"])["Staunton"] == (36, 31)


def test_beautify_get_neighbor_matches_hex_utils():
    src = (PS / "beautify_map.ps1").read_text()
    part = src[src.index("# ===== HEX NEIGHBOR SYSTEM ====="):src.index("# ===== DIRECTION LOOKUP TABLE =====")]
    part = part.replace("$PSScriptRoot", f"'{PS}'")
    cells = [(c, r) for c in range(0, 12) for r in range(0, 12)]
    out = json.loads(_run(part + "\n@(" + ",".join(
        f"@(0..5 | ForEach-Object {{ ,(Get-Neighbor {c} {r} $_) }})" for c, r in cells) + ") | ConvertTo-Json -Depth 4 -Compress"))
    for (c, r), nbs in zip(cells, out):
        assert [tuple(n) for n in nbs] == hu.offset_neighbors(c, r), (c, r)


# ---------------------------------------------------------------- pinned geography (Archivist review, PR #21)
def _vmd_frame():
    text = (PS / "valley_map_data.ps1").read_text()
    frame = (PS / "ValleyFrame.ps1").read_text()
    num = lambda n: float(re.search(r"\$%s\s*=\s*([0-9.]+)" % n, frame).group(1))  # noqa: E731
    mi_lon = 69.0 * math.cos(38.75 * math.pi / 180)
    south, west = num("southBound"), num("westBound")
    snap = lambda la, lo: hu.point_to_offset((west - lo) * mi_lon, (la - south) * 69.0)  # noqa: E731
    return text, snap


def _vmd_places():
    text, snap = _vmd_frame()
    return {n: snap(float(la), float(lo)) for n, la, lo in
            re.findall(r'Name="([^"]+)";\s*Lat=([0-9.]+);\s*Lon=([0-9.]+)', text)}


def _vmd_trace(name):
    text, snap = _vmd_frame()
    block = re.search(r"\$%s = @\((.*?)\n\)" % name, text, re.S).group(1)
    return [snap(float(la), float(lo)) for la, lo in re.findall(r"Lat=([0-9.]+); Lon=([0-9.]+)", block)]


# Correct hexes from Captain Archivist's review table (PR #21 comment 6229686760), from GNIS coordinates.
ARCHIVIST_HEXES = {
    "Swift Run Gap": (69, 45),
    "Cross Keys": (50, 45),
    "New Market Gap": (65, 65),
    "Brown's Gap": (58, 37),
    "McDowell": (10, 43),
    "Thornton's Gap": (83, 66),
    "Manassas Gap": (98, 83),
    "Newtown": (89, 95),
    "Luray": (74, 66),
    "Rockfish Gap": (50, 22),
    # The Archivist's table gives (52,40) from the Wikipedia coordinates 38.2892/-78.8133. The official
    # GNIS 1496108 point (38.2962/-78.8106) snaps to (52,41), and the file follows GNIS. FLAGGED in the PR.
    "Port Republic": (52, 41),
}


@pytest.mark.parametrize("name", sorted(ARCHIVIST_HEXES))
def test_valley_map_data_pinned_hexes(name):
    assert _vmd_places()[name] == ARCHIVIST_HEXES[name]


def test_valley_pike_rows_north_to_south():
    p = _vmd_places()
    rows = [p[n][1] for n in ("Martinsburg", "Winchester", "Kernstown", "Newtown", "Middletown", "Strasburg",
                              "Toms Brook", "Woodstock", "Edinburg", "Mount Jackson", "New Market",
                              "Harrisonburg", "Staunton", "Lexington")]
    assert rows == [121, 102, 100, 95, 92, 88, 86, 82, 78, 72, 65, 51, 31, 6]


def test_south_fork_runs_west_of_luray():
    luray = _vmd_places()["Luray"]
    same_row = [c for c, r in _vmd_trace("southFork") if abs(r - luray[1]) <= 1]
    assert same_row and max(same_row) < luray[0]


def test_ridges_pass_through_their_gaps():
    p = _vmd_places()
    assert p["New Market Gap"] in _vmd_trace("massanutten")
    br = _vmd_trace("blueRidge")
    for g in ("Swift Run Gap", "Brown's Gap", "Thornton's Gap", "Manassas Gap"):
        assert p[g] in br, g


def test_massanutten_gap_stays_flagged_unidentified():
    line = next(l for l in (PS / "valley_map_data.ps1").read_text().splitlines() if 'Name="Massanutten Gap"' in l)
    assert "UNIDENTIFIED" in line
