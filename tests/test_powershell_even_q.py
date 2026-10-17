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
