# Valley Campaign Map Beautifier
# Loads the existing map and applies visual improvements:
# 1. Directional river tiles (River1-9 based on neighbor connectivity)
# 2. Directional road tiles (Road1-5, Road10-13: the game's own SetAutoRoads numbering, NOT the river one)
# 3. Valley floor variety (scatter ThinForest into plains)
# 4. Mountain/forest transition smoothing
# 5. Off-map edge cleanup

param(
    [string]$MapFile = "C:\Users\garre\ValleyCampaign\maps\Valley Campaign 1862.sav",
    [string]$OutputFile = "C:\Users\garre\ValleyCampaign\maps\Valley Campaign 1862.sav"
)

$ErrorActionPreference = "Stop"
$gameDir = "C:\Program Files (x86)\Steam\steamapps\common\Hex of Steel"
$managedDir = "$gameDir\Hex of Steel_Data\Managed"

Write-Output "Loading game assemblies..."
[System.Reflection.Assembly]::LoadFrom("$managedDir\UnityEngine.CoreModule.dll") | Out-Null
[System.Reflection.Assembly]::LoadFrom("$managedDir\UnityEngine.dll") | Out-Null
[System.Reflection.Assembly]::LoadFrom("$managedDir\Assembly-CSharp.dll") | Out-Null

# ===== LOAD MAP =====
Write-Output "Loading Valley Campaign map..."
$bytes = [System.IO.File]::ReadAllBytes($MapFile)
$ms = New-Object System.IO.MemoryStream(,$bytes)
$ds = New-Object System.IO.Compression.DeflateStream($ms, [System.IO.Compression.CompressionMode]::Decompress)
$outMs = New-Object System.IO.MemoryStream
$ds.CopyTo($outMs); $ds.Close(); $ms.Close()
$rawData = $outMs.ToArray(); $outMs.Close()

$memStr = New-Object System.IO.MemoryStream(,$rawData)
$bf = New-Object System.Runtime.Serialization.Formatters.Binary.BinaryFormatter
$gameData = $bf.Deserialize($memStr); $memStr.Close()

$map = $gameData.map
$W = $map.SizeX
$mapH = $map.SizeY
$tiles = $map.TilesTable
Write-Output "Map loaded: $W x $mapH ($($W * $mapH) hexes)"

# ===== HEX NEIGHBOR SYSTEM =====
# Hex of Steel native flat-top EVEN-Q (MapGO / Utils.GetAllTilesNeighbours), shared with
# src/hex_utils.py via HexEvenQ.ps1: even columns half a row north, rows increase north.
# Edge numbering: 0=N, 1=NE, 2=SE, 3=S, 4=SW, 5=NW (geographic, north up).
# (Before 2026-10-17 this script used N=(0,-1) with odd columns north, which is not the game's layout.)
. (Join-Path $PSScriptRoot 'HexEvenQ.ps1')

function Get-Neighbor {
    param([int]$cx, [int]$cy, [int]$dir)
    return (Get-HexNeighbor $cx $cy $dir)
}

# ===== DIRECTION LOOKUP TABLE =====
# Maps sorted edge-pair string to River/Road variant number
# Derived from visual analysis of the River PNGs; edges are geographic N..NW (PNG up = north in game).
# VERIFIED 2026-10-17 by Major Hotchkiss (PR #21 review): PNG edge sampling of River1-12 and the editor's
# TileEditorGO.SetAutoRivers give exactly this table. Do NOT mirror it (the old mirrored neighbour table
# was the bug; with geographic ports this table is right). Pinned by tests/test_powershell_even_q.py.

$dirLookup = @{}
# Straight through (opposite edges, 180°)
$dirLookup["0,3"] = 1   # N-S
$dirLookup["1,4"] = 2   # NE-SW
$dirLookup["2,5"] = 3   # NW-SE
# Gentle bends (skip one edge, 120°)
$dirLookup["1,5"] = 4   # across top (NW-NE)
$dirLookup["2,4"] = 5   # across bottom (SW-SE)
$dirLookup["0,4"] = 6   # N-SW
$dirLookup["0,2"] = 7   # N-SE
$dirLookup["1,3"] = 8   # NE-S
$dirLookup["3,5"] = 9   # S-NW

# Sharp turns (adjacent edges, 60°) - use gentle bend fallback since
# 60° rivers are rare; we pick the nearest gentle variant
$sharpFallback = @{}
$sharpFallback["0,1"] = 4   # N+NE → use across-top
$sharpFallback["1,2"] = 7   # NE+SE → use N-SE (close enough)
$sharpFallback["2,3"] = 5   # SE+S → use across-bottom
$sharpFallback["3,4"] = 5   # S+SW → use across-bottom
$sharpFallback["4,5"] = 6   # SW+NW → use N-SW (close enough)
$sharpFallback["0,5"] = 4   # N+NW → use across-top

# 3-way junction lookup (for confluences)
# From visual analysis of River10-12 PNGs
$junctionLookup = @{}
$junctionLookup["1,3,5"] = 10  # alternating Y
$junctionLookup["0,2,4"] = 11  # alternating Y (rotated)
$junctionLookup["0,1,3"] = 12  # T-junction

# ===== ROAD LOOKUP TABLE =====
# Roads do NOT use the river numbering. The game's TileEditorGO.SetAutoRoads uses only Road1-5 and Road10-13:
# 1=N-S, 2=NW-NE, 3=SW-SE, 4=NE-SW, 5=NW-SE, 10=S-NW, 11=N-SW, 12=N-SE, 13=NE-S
# (Major Hotchkiss, PR #21 review, cross-checked against SetAutoRivers and the Railroad PNGs).
$roadLookup = @{ "0,3"=1; "1,5"=2; "2,4"=3; "1,4"=4; "2,5"=5; "3,5"=10; "0,4"=11; "0,2"=12; "1,3"=13 }
$roadSharpFallback = @{ "0,1"=2; "1,2"=12; "2,3"=3; "3,4"=3; "4,5"=11; "0,5"=2 }

# ===== PASS 1: FIX RIVER DIRECTIONS =====
Write-Output "`n--- Pass 1: Fixing river directions ---"

$riverCount = 0
$riverFixed = 0

for ($x = 0; $x -lt $W; $x++) {
    for ($y = 0; $y -lt $mapH; $y++) {
        $tile = $tiles[$x, $y]
        if ($tile -eq $null) { continue }
        if ($tile.Name -notmatch '^River\d+$') { continue }
        $riverCount++

        # Find which edges have river/town neighbors (rivers flow through towns too)
        $connEdges = @()
        for ($dir = 0; $dir -lt 6; $dir++) {
            $nb = Get-Neighbor $x $y $dir
            $nx = $nb[0]; $ny = $nb[1]
            if ($nx -lt 0 -or $nx -ge $W -or $ny -lt 0 -or $ny -ge $mapH) { continue }
            $nTile = $tiles[$nx, $ny]
            if ($nTile -eq $null) { continue }
            if ($nTile.Name -match '^River\d+$' -or $nTile.FilterType -eq "FilterVP") {
                $connEdges += $dir
            }
        }

        if ($connEdges.Count -lt 2) { continue }

        $edgeKey = ($connEdges | Sort-Object) -join ","

        $variant = $null
        if ($connEdges.Count -eq 2) {
            if ($dirLookup.ContainsKey($edgeKey)) {
                $variant = $dirLookup[$edgeKey]
            } elseif ($sharpFallback.ContainsKey($edgeKey)) {
                $variant = $sharpFallback[$edgeKey]
            }
        } elseif ($connEdges.Count -ge 3) {
            # Try 3-way junction lookup
            $triKey = ($connEdges | Sort-Object | Select-Object -First 3) -join ","
            if ($junctionLookup.ContainsKey($triKey)) {
                $variant = $junctionLookup[$triKey]
            } else {
                # Pick the two most "opposite" edges for best visual
                $bestPair = $null; $bestDist = -1
                for ($i = 0; $i -lt $connEdges.Count; $i++) {
                    for ($j = $i + 1; $j -lt $connEdges.Count; $j++) {
                        $e1 = $connEdges[$i]; $e2 = $connEdges[$j]
                        $dist = [Math]::Min([Math]::Abs($e1 - $e2), 6 - [Math]::Abs($e1 - $e2))
                        if ($dist -gt $bestDist) {
                            $bestDist = $dist
                            $bestPair = (($e1, $e2) | Sort-Object) -join ","
                        }
                    }
                }
                if ($bestPair -ne $null -and $dirLookup.ContainsKey($bestPair)) {
                    $variant = $dirLookup[$bestPair]
                }
            }
        }

        if ($variant -ne $null -and $tile.Name -ne "River$variant") {
            $tile.Name = "River$variant"
            $riverFixed++
        }
    }
}
Write-Output "  Rivers: $riverCount total, $riverFixed updated"

# ===== PASS 2: FIX ROAD DIRECTIONS =====
Write-Output "`n--- Pass 2: Fixing road directions ---"

$roadCount = 0
$roadFixed = 0

for ($x = 0; $x -lt $W; $x++) {
    for ($y = 0; $y -lt $mapH; $y++) {
        $tile = $tiles[$x, $y]
        if ($tile -eq $null) { continue }
        if ($tile.Name -notmatch '^Road\d+$') { continue }
        $roadCount++

        $connEdges = @()
        for ($dir = 0; $dir -lt 6; $dir++) {
            $nb = Get-Neighbor $x $y $dir
            $nx = $nb[0]; $ny = $nb[1]
            if ($nx -lt 0 -or $nx -ge $W -or $ny -lt 0 -or $ny -ge $mapH) { continue }
            $nTile = $tiles[$nx, $ny]
            if ($nTile -eq $null) { continue }
            if ($nTile.Name -match '^Road\d+$' -or $nTile.FilterType -eq "FilterVP") {
                $connEdges += $dir
            }
        }

        if ($connEdges.Count -lt 2) { continue }

        $edgeKey = ($connEdges | Sort-Object) -join ","
        $variant = $null

        if ($connEdges.Count -eq 2) {
            if ($roadLookup.ContainsKey($edgeKey)) {
                $variant = $roadLookup[$edgeKey]
            } elseif ($roadSharpFallback.ContainsKey($edgeKey)) {
                $variant = $roadSharpFallback[$edgeKey]
            }
        } elseif ($connEdges.Count -ge 3) {
            $bestPair = $null; $bestDist = -1
            for ($i = 0; $i -lt $connEdges.Count; $i++) {
                for ($j = $i + 1; $j -lt $connEdges.Count; $j++) {
                    $e1 = $connEdges[$i]; $e2 = $connEdges[$j]
                    $dist = [Math]::Min([Math]::Abs($e1 - $e2), 6 - [Math]::Abs($e1 - $e2))
                    if ($dist -gt $bestDist) {
                        $bestDist = $dist
                        $bestPair = (($e1, $e2) | Sort-Object) -join ","
                    }
                }
            }
            if ($bestPair -ne $null -and $roadLookup.ContainsKey($bestPair)) {
                $variant = $roadLookup[$bestPair]
            }
        }

        if ($variant -ne $null -and $tile.Name -ne "Road$variant") {
            $tile.Name = "Road$variant"
            $roadFixed++
        }
    }
}
Write-Output "  Roads: $roadCount total, $roadFixed updated"

# ===== PASS 3: VALLEY FLOOR VARIETY =====
Write-Output "`n--- Pass 3: Adding valley floor variety ---"

$plainCount = 0
$scatteredForest = 0

$thinTypes = @("ThinForest", "ThinForest2", "ThinForest3")

for ($x = 0; $x -lt $W; $x++) {
    for ($y = 0; $y -lt $mapH; $y++) {
        $tile = $tiles[$x, $y]
        if ($tile -eq $null) { continue }
        if ($tile.Name -ne "Plain") { continue }
        $plainCount++

        # Deterministic hash for reproducible scattering
        $hash = ($x * 31 + $y * 97 + $x * $y * 13) % 100

        # ~15% chance to place scattered ThinForest
        if ($hash -lt 15) {
            $fi = ($x * 7 + $y * 11) % 3
            $tile.Name = $thinTypes[$fi]
            $tile.Type = "ThinForest"
            $tile.FilterType = "FilterForest"
            $tile.MPCost = 2
            $tile.DamageModificator = 25
            $scatteredForest++
        }
    }
}
Write-Output "  Plains: $plainCount total, $scatteredForest converted to scattered forest"

# ===== PASS 4: MOUNTAIN/FOREST TRANSITIONS =====
Write-Output "`n--- Pass 4: Smoothing terrain transitions ---"

$transitionsAdded = 0

# Find plains directly adjacent to mountains and convert to HillForest
for ($x = 0; $x -lt $W; $x++) {
    for ($y = 0; $y -lt $mapH; $y++) {
        $tile = $tiles[$x, $y]
        if ($tile -eq $null) { continue }
        if ($tile.Name -ne "Plain" -and $tile.Type -ne "ThinForest") { continue }

        $adjMountain = $false
        for ($dir = 0; $dir -lt 6; $dir++) {
            $nb = Get-Neighbor $x $y $dir
            $nx = $nb[0]; $ny = $nb[1]
            if ($nx -lt 0 -or $nx -ge $W -or $ny -lt 0 -or $ny -ge $mapH) { continue }
            $nTile = $tiles[$nx, $ny]
            if ($nTile -ne $null -and $nTile.Name -eq "Mountain") {
                $adjMountain = $true
                break
            }
        }

        if ($adjMountain) {
            $tile.Name = "HillForest"
            $tile.Type = "Hill"
            $tile.FilterType = "FilterTerrain"
            $tile.MPCost = 3
            $tile.DamageModificator = 50
            $transitionsAdded++
        }
    }
}
Write-Output "  Transition buffers added: $transitionsAdded"

# ===== PASS 5: OFF-MAP EDGE CLEANUP =====
Write-Output "`n--- Pass 5: Cleaning map edges ---"

$edgesCleaned = 0
$edgeWidth = 2

for ($x = 0; $x -lt $W; $x++) {
    for ($y = 0; $y -lt $mapH; $y++) {
        $isEdge = ($x -lt $edgeWidth -or $x -ge ($W - $edgeWidth) -or $y -lt $edgeWidth -or $y -ge ($mapH - $edgeWidth))
        if (-not $isEdge) { continue }

        $tile = $tiles[$x, $y]
        if ($tile -eq $null) { continue }
        if ($tile.Name -eq "Mountain") { continue }
        if ($tile.FilterType -eq "FilterVP") { continue }

        $tile.Name = "Mountain"
        $tile.Type = "Mountain"
        $tile.FilterType = "FilterTerrain"
        $tile.MPCost = 3
        $tile.DamageModificator = 60
        $tile.OwnerName = ""
        $tile.CityName = ""
        $tile.IsVictoryPoint = $false
        $edgesCleaned++
    }
}
Write-Output "  Edge hexes cleaned: $edgesCleaned"

# ===== FINAL TERRAIN SUMMARY =====
Write-Output "`n--- Final terrain distribution ---"
$counts = @{}
for ($x = 0; $x -lt $W; $x++) {
    for ($y = 0; $y -lt $mapH; $y++) {
        $tile = $tiles[$x, $y]
        if ($tile -eq $null) { continue }
        $nm = $tile.Type
        if ($counts.ContainsKey($nm)) { $counts[$nm]++ } else { $counts[$nm] = 1 }
    }
}
$counts.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object {
    Write-Output "  $($_.Key): $($_.Value)"
}

# ===== SERIALIZE AND SAVE =====
Write-Output "`nSerializing..."
$serMs = New-Object System.IO.MemoryStream
$bf2 = New-Object System.Runtime.Serialization.Formatters.Binary.BinaryFormatter
$bf2.Serialize($serMs, $gameData)
$serialized = $serMs.ToArray()
$serMs.Close()
Write-Output "Serialized: $($serialized.Length) bytes"

Write-Output "Compressing..."
$compMs = New-Object System.IO.MemoryStream
$compDs = New-Object System.IO.Compression.DeflateStream($compMs, [System.IO.Compression.CompressionLevel]::Optimal)
$compDs.Write($serialized, 0, $serialized.Length)
$compDs.Close()
$finalBytes = $compMs.ToArray()
$compMs.Close()
Write-Output "Compressed: $($finalBytes.Length) bytes"

[System.IO.File]::WriteAllBytes($OutputFile, $finalBytes)
Write-Output "`n=== BEAUTIFICATION COMPLETE ==="
Write-Output "Saved to: $OutputFile"

# Also copy to mod directory
$modDest = "C:\Program Files (x86)\Steam\steamapps\workshop\content\1240630\3773041458\Maps\Valley Campaign 1862.sav"
Copy-Item $OutputFile $modDest -Force
Write-Output "Copied to mod: $modDest"
