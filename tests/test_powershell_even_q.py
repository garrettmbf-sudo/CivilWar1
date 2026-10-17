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


@pytest.mark.parametrize("script", ["beautify_map.ps1", "valley_map_data.ps1", "build_valley_map.ps1"])
def test_tools_dot_source_the_shared_module(script):
    assert ". (Join-Path $PSScriptRoot 'HexEvenQ.ps1')" in (PS / script).read_text()


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
    out = _run(f"& '{PS / 'valley_map_data.ps1'}'")
    m = re.search(r"Size: (\d+) x (\d+) hexes", out)
    lat = lambda n: float(re.search(r"\$%s\s*=\s*([0-9.]+)" % n, text).group(1))  # noqa: E731
    south, north, west, east = lat("southBound"), lat("northBound"), lat("westBound"), lat("eastBound")
    mi_lon = 69.0 * math.cos(38.75 * math.pi / 180)
    assert (int(m.group(1)), int(m.group(2))) == (
        math.ceil((west - east) * mi_lon / hu.COL_PITCH_RATIO) + 1, math.ceil((north - south) * 69.0) + 1)
    towns = re.findall(r'Name="([^"]+)";\s*Lat=([0-9.]+);\s*Lon=([0-9.]+);\s*Type="[^"]+";\s*VP=\$\w+;\s*Primary=\$true', text)
    assert len(towns) >= 10
    for name, la, lo in towns:
        want = hu.point_to_offset((west - float(lo)) * mi_lon, (float(la) - south) * 69.0)
        row = re.search(r"^%s\s+(-?\d+)\s+(-?\d+)\s" % re.escape(name), out, re.M)
        assert row and (int(row.group(1)), int(row.group(2))) == want, name
    pike = re.search(r"Valley Pike: (.*)", out).group(1)
    assert len(re.findall(r"\((\d+),(\d+)\)", pike)) == 19


def test_build_valley_map_hex_part_matches_hex_utils(tmp_path):
    src = (PS / "build_valley_map.ps1").read_text()
    part = src[src.index("# ===== HEX GRID"):src.index("# ===== LOAD TEMPLATE =====")]
    part = part.replace("$PSScriptRoot", f"'{PS}'")
    out = json.loads(_run(part + r"""
$res = @{ W=$W; H=$H; road=@($roadSet); river=@($riverSet);
          towns=@($towns | ForEach-Object { ,@($_.N, $_.X, $_.Y) }) }
$res | ConvertTo-Json -Depth 5 -Compress
""").strip().splitlines()[-1])  # the script part also prints its terrain summary
    assert (out["W"], out["H"]) == (math.ceil(105 / hu.COL_PITCH_RATIO), 125)
    W = out["W"]

    def arr(name):
        m = re.search(r"\$%s = @\(([^)]*)\)" % name, src)
        v = [int(x) for x in re.findall(r"-?\d+", m.group(1))]
        return list(zip(v[::2], v[1::2]))

    def trace(wps):
        cells = set()
        for a, b in zip(wps, wps[1:]):
            for c, r in hu.hex_line(hu.point_to_offset(*a), hu.point_to_offset(*b)):
                if 0 <= c < W and 0 <= r < out["H"]:
                    cells.add(r * W + c)
        return cells

    assert set(out["road"]) == trace(arr("valleyPike"))
    rivers = set()
    for n in ("riverSouthFork", "riverNorthFork", "riverMainShen", "riverPotomac", "riverSouth"):
        rivers |= trace(arr(n))
    assert set(out["river"]) == rivers
    town_src = re.findall(r'@\{N="([^"]+)";\s*X=(\d+);\s*Y=(\d+);', src)
    got = {n: (x, y) for n, x, y in out["towns"]}
    for n, x, y in town_src:
        assert got[n] == hu.point_to_offset(int(x), int(y)), n
    # the traced pike is a chain of game-adjacent hexes between its waypoints
    wps = [hu.point_to_offset(*p) for p in arr("valleyPike")]
    for a, b in zip(wps, wps[1:]):
        line = hu.hex_line(a, b)
        assert all(q in hu.offset_neighbors(*p) for p, q in zip(line, line[1:]))


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
    num = lambda n: float(re.search(r"\$%s\s*=\s*([0-9.]+)" % n, text).group(1))  # noqa: E731
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
