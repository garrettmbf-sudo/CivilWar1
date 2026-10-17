# Shared map frame for the PowerShell Valley tools (valley_map_data.ps1 and build_valley_map.ps1).
# One frame, one rounding rule, so both scripts put every feature on the same game hex.
# Dot-source it:  . (Join-Path $PSScriptRoot 'ValleyFrame.ps1')
#
# Frame: equirectangular about 38.75 N, origin at the SW corner (westBound, southBound).
# Grid: native even-q (HexEvenQ.ps1 = src/hex_utils.py), 1 mile between rows, 0.8667 mile between columns.
# Note (Major Hotchkiss, PR #21 review): this 1-mile box is NOT data/map_shape.json. Take W, H and the
# frame from map_shape.json (scripts/valley_map_shape.py) for the 500-yd valley map.

. (Join-Path $PSScriptRoot 'HexEvenQ.ps1')

# --- Geographic Constants ---
$centerLat = 38.75
$miPerDegLat = 69.0
$miPerDegLon = 69.0 * [Math]::Cos($centerLat * [Math]::PI / 180)  # ~53.8

# --- Map Bounds ---
$southBound = 37.70   # South of Lexington (was 37.90, south of Staunton; extended 2026-10-17 to include Lexington/VMI)
$northBound = 39.71   # North of Martinsburg
$westBound  = 79.65   # Into Alleghenies (west of McDowell)
$eastBound  = 77.70   # East of Harpers Ferry

$heightMi  = ($northBound - $southBound) * $miPerDegLat   # ~138.7 mi
$widthMi   = ($westBound - $eastBound) * $miPerDegLon     # ~104.9 mi
# Exact minimum grid: the largest snapped column is round(w / 0.8667), the largest row is round(h).
$mapWidth  = [int][Math]::Round($widthMi / $script:HexColPitchRatio) + 1   # 122 columns
$mapHeight = [int][Math]::Round($heightMi) + 1                             # 140 rows

# lat (N) / lon (W, positive) -> frame miles [x east, y north] from the SW corner.
function Get-FrameMiles($latN, $lonW) {
    return @((($westBound - $lonW) * $miPerDegLon), (($latN - $southBound) * $miPerDegLat))
}

# lat/lon -> nearest even-q hex (game PosX, PosY).
function Get-HexLatLon($latN, $lonW) {
    $m = Get-FrameMiles $latN $lonW
    return (Get-HexFromXY $m[0] $m[1] 1.0)
}
