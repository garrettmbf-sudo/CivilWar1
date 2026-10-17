# Valley Campaign Map Data Generator
# Calculates hex positions for all geographic features at 1-mile-per-hex scale

# Frame, bounds, grid size and lat/lon -> hex snapping are shared with build_valley_map.ps1.
# Native even-q grid (HexEvenQ.ps1 = src/hex_utils.py): rows 1 mile apart N-S, columns 0.8667 mile apart E-W.
. (Join-Path $PSScriptRoot 'ValleyFrame.ps1')

Write-Output "=== VALLEY CAMPAIGN MAP DIMENSIONS ==="
Write-Output "Size: $mapWidth x $mapHeight hexes ($($mapWidth * $mapHeight) total)"
Write-Output "Scale: 1 mile per hex (native even-q, columns 0.8667 mi apart)"
Write-Output "Geographic bounds:"
Write-Output "  South: $southBound N  North: $northBound N"
Write-Output "  West:  $westBound W   East:  $eastBound W"
Write-Output "  Miles per degree lat: $miPerDegLat"
Write-Output "  Miles per degree lon: $([Math]::Round($miPerDegLon, 1))"
Write-Output ""

# --- Coordinate conversion: Get-HexLatLon (ValleyFrame.ps1) ---

# --- KEY TOWNS ---
$towns = @(
    # Campaign-critical towns
    @{ Name="Staunton";        Lat=38.1496; Lon=79.0717; Type="city";    VP=$true;  Primary=$true  }
    @{ Name="Lexington";       Lat=37.7840; Lon=79.4428; Type="town";    VP=$false; Primary=$false }  # Rockbridge Co. seat, VMI; southern map anchor. VERIFIED 2026-10-17: USGS GNIS 1498506 (37.784028 N, 79.442819 W); period map: Hotchkiss Rockbridge Co. map, LoC G3883.R6 186- .R6 (H57) - see historical_data/sources_1862.csv SRC020, SRC027
    @{ Name="Waynesboro";      Lat=38.0686; Lon=78.8894; Type="town";    VP=$false; Primary=$false }
    @{ Name="McDowell";        Lat=38.3357; Lon=79.4906; Type="village"; VP=$true;  Primary=$true  }  # VERIFIED 2026-10-17 (Captain Archivist, PR #16): SRC020 USGS GNIS (official point; was ~3.4 km off)
    @{ Name="Port Republic";   Lat=38.2962; Lon=78.8106; Type="village"; VP=$true;  Primary=$true  }  # FIXED 2026-10-17: GNIS 1496108 (Captain Archivist review of PR #21; USGS GNIS via The National Map geonames service, queried 2026-10-17, SRC020)
    @{ Name="Cross Keys";      Lat=38.3593; Lon=78.8420; Type="village"; VP=$true;  Primary=$true  }  # FIXED 2026-10-17: GNIS 1495443 (Captain Archivist review of PR #21; USGS GNIS via The National Map geonames service, queried 2026-10-17, SRC020); was 4.4 mi NNE
    @{ Name="Harrisonburg";    Lat=38.4496; Lon=78.8689; Type="town";    VP=$true;  Primary=$true  }
    @{ Name="New Market";      Lat=38.6479; Lon=78.6717; Type="town";    VP=$true;  Primary=$true  }
    @{ Name="Luray";           Lat=38.6654; Lon=78.4594; Type="town";    VP=$false; Primary=$true  }
    @{ Name="Mount Jackson";   Lat=38.7461; Lon=78.6428; Type="village"; VP=$false; Primary=$false }
    @{ Name="Woodstock";       Lat=38.8814; Lon=78.5058; Type="town";    VP=$false; Primary=$false }
    @{ Name="Strasburg";       Lat=38.9885; Lon=78.3586; Type="town";    VP=$true;  Primary=$true  }
    @{ Name="Front Royal";     Lat=38.9182; Lon=78.1944; Type="town";    VP=$true;  Primary=$true  }
    @{ Name="Middletown";      Lat=39.0275; Lon=78.2814; Type="village"; VP=$false; Primary=$false }
    @{ Name="Newtown";         Lat=39.0834; Lon=78.2181; Type="village"; VP=$false; Primary=$false }  # 1862 Newtown = Stephens City. FIXED 2026-10-17: GNIS 1500159 (Captain Archivist review of PR #21; USGS GNIS via The National Map geonames service, queried 2026-10-17, SRC020)
    @{ Name="Kernstown";       Lat=39.1500; Lon=78.1833; Type="village"; VP=$true;  Primary=$true  }
    @{ Name="Winchester";      Lat=39.1857; Lon=78.1633; Type="city";    VP=$true;  Primary=$true  }
    @{ Name="Martinsburg";     Lat=39.4562; Lon=77.9639; Type="town";    VP=$true;  Primary=$true  }
    @{ Name="Harpers Ferry";   Lat=39.3253; Lon=77.7294; Type="town";    VP=$true;  Primary=$true  }
    @{ Name="Charles Town";    Lat=39.2886; Lon=77.8600; Type="town";    VP=$false; Primary=$false }
    # Western approaches
    @{ Name="Moorefield";      Lat=39.0622; Lon=78.9692; Type="village"; VP=$false; Primary=$false }
    @{ Name="Franklin";        Lat=38.6428; Lon=79.3306; Type="village"; VP=$false; Primary=$false }
    @{ Name="Monterey";        Lat=38.4128; Lon=79.5806; Type="village"; VP=$false; Primary=$false }
    # Valley Turnpike stops (Winchester-Staunton; the Valley Turnpike ends at Staunton)
    @{ Name="Edinburg";        Lat=38.8261; Lon=78.5658; Type="village"; VP=$false; Primary=$false }
    @{ Name="Toms Brook";      Lat=38.9394; Lon=78.4386; Type="village"; VP=$false; Primary=$false }
    # Eastern passes
    @{ Name="Manassas Gap";    Lat=38.9090; Lon=78.0753; Type="pass";    VP=$false; Primary=$false }  # VERIFIED 2026-10-17 (Captain Archivist, PR #16): SRC020 USGS GNIS 1470040
    @{ Name="Thornton's Gap";  Lat=38.6612; Lon=78.3197; Type="pass";    VP=$false; Primary=$false }  # VERIFIED 2026-10-17 (Captain Archivist, PR #16): SRC020 USGS GNIS 1475667
    @{ Name="Swift Run Gap";   Lat=38.3571; Lon=78.5450; Type="pass";    VP=$false; Primary=$true  }  # VERIFIED 2026-10-17 (Captain Archivist, PR #16): SRC020 USGS GNIS 1475392 (was ~14 km too far west); road from Harrisonburg to Gordonsville
    @{ Name="Brown's Gap";     Lat=38.2404; Lon=78.7106; Type="pass";    VP=$false; Primary=$false }  # VERIFIED 2026-10-17 (Captain Archivist, PR #16): SRC020 USGS GNIS 1463928
    @{ Name="Rockfish Gap";    Lat=38.0333; Lon=78.8500; Type="pass";    VP=$false; Primary=$false }
    # Massanutten gaps
    @{ Name="New Market Gap";  Lat=38.6429; Lon=78.6122; Type="pass";    VP=$false; Primary=$true  }  # FIXED 2026-10-17: GNIS 1485851 (Gap; Page/Shenandoah county line) (Captain Archivist review of PR #21; USGS GNIS via The National Map geonames service, queried 2026-10-17, SRC020); was 3.4 mi east
    @{ Name="Massanutten Gap"; Lat=38.9167; Lon=78.3000; Type="pass";    VP=$false; Primary=$false }  # UNIDENTIFIED: no GNIS feature of this name (geonames query 2026-10-17 returned none); position UNVERIFIED, not fixed. Needs Archivist identification
)

Write-Output "=== KEY LOCATIONS ==="
Write-Output ("{0,-20} {1,4} {2,4}  {3}" -f "Location", "HexX", "HexY", "Type")
Write-Output ("-" * 50)
foreach ($t in $towns) {
    $townHex = Get-HexLatLon $t.Lat $t.Lon
    $hx = $townHex[0]; $hy = $townHex[1]
    $t.HexX = $hx
    $t.HexY = $hy
    if ($t.Primary) {
        Write-Output ("{0,-20} {1,4} {2,4}  {3}" -f $t.Name, $hx, $hy, $t.Type)
    }
}

Write-Output ""
Write-Output "=== MOUNTAIN RIDGELINES (hex coordinate waypoints) ==="

# --- MOUNTAIN RIDGELINES ---
# Each ridge defined as a series of lat/lon waypoints, with width in hexes

# Blue Ridge - eastern boundary
$blueRidge = @(
    @{ Lat=39.35; Lon=77.75 }  # Harpers Ferry area
    @{ Lat=39.25; Lon=77.80 }
    @{ Lat=39.10; Lon=77.90 }
    @{ Lat=38.95; Lon=78.00 }
    @{ Lat=38.909; Lon=78.075 }  # Manassas Gap (SRC020 GNIS 1470040)
    @{ Lat=38.70; Lon=78.25 }
    @{ Lat=38.661; Lon=78.320 }  # Thornton's Gap (SRC020 GNIS 1475667)
    @{ Lat=38.4679; Lon=78.4572 }  # Bootens Gap, Blue Ridge crest (GNIS 1463669, on the Greene/Page county line); was 38.45/78.55, ~5 mi west of the crest
    @{ Lat=38.357; Lon=78.545 }  # Swift Run Gap (SRC020 GNIS 1475392)
    @{ Lat=38.2404; Lon=78.7106 }  # Brown's Gap, Blue Ridge crest (SRC020 GNIS 1463928); was 38.20/78.75
    @{ Lat=38.05; Lon=78.85 }  # Rockfish Gap
    @{ Lat=37.95; Lon=78.90 }
)
$blueRidgeWidth = 4  # hexes wide

# Massanutten Mountain - central ridge splitting the valley
$massanutten = @(
    @{ Lat=38.40; Lon=78.72 }  # Southern tip near Harrisonburg
    @{ Lat=38.45; Lon=78.68 }
    @{ Lat=38.50; Lon=78.65 }
    @{ Lat=38.55; Lon=78.60 }
    @{ Lat=38.6032; Lon=78.6433 }  # Bird Knob, Massanutten crest (GNIS 1481812, on the Rockingham/Page county line); was 38.60/78.56
    @{ Lat=38.6429; Lon=78.6122 }  # New Market Gap (GNIS 1485851, on the Page/Shenandoah county line); was 38.65/78.52
    @{ Lat=38.6851; Lon=78.5904 }  # Kerns Mountain, Massanutten crest (GNIS 1484565, on the Shenandoah/Page county line); was 38.70/78.48
    @{ Lat=38.75; Lon=78.44 }
    @{ Lat=38.80; Lon=78.40 }
    @{ Lat=38.85; Lon=78.36 }
    @{ Lat=38.90; Lon=78.33 }  # Northern tip near Strasburg
    @{ Lat=38.93; Lon=78.30 }
)
$massanuttenWidth = 5  # hexes wide

# North Mountain - western valley wall
$northMountain = @(
    @{ Lat=39.35; Lon=78.40 }
    @{ Lat=39.20; Lon=78.45 }
    @{ Lat=39.05; Lon=78.55 }
    @{ Lat=38.90; Lon=78.65 }
    @{ Lat=38.75; Lon=78.80 }
    @{ Lat=38.60; Lon=78.90 }
    @{ Lat=38.45; Lon=79.00 }
    @{ Lat=38.30; Lon=79.10 }
    @{ Lat=38.15; Lon=79.20 }
    @{ Lat=38.00; Lon=79.25 }
)
$northMountainWidth = 5

# Allegheny Front - far western boundary
$allegheny = @(
    @{ Lat=39.50; Lon=79.20 }
    @{ Lat=39.30; Lon=79.25 }
    @{ Lat=39.10; Lon=79.30 }
    @{ Lat=38.90; Lon=79.35 }
    @{ Lat=38.70; Lon=79.40 }
    @{ Lat=38.50; Lon=79.50 }
    @{ Lat=38.30; Lon=79.55 }
    @{ Lat=38.10; Lon=79.55 }
    @{ Lat=37.95; Lon=79.60 }
)
$alleghenyWidth = 6

Write-Output "Blue Ridge: $(($blueRidge | ForEach-Object { "($((Get-HexLatLon $_.Lat $_.Lon) -join ','))" }) -join ' -> ')"
Write-Output "Massanutten: $(($massanutten | ForEach-Object { "($((Get-HexLatLon $_.Lat $_.Lon) -join ','))" }) -join ' -> ')"
Write-Output "North Mountain: $(($northMountain | ForEach-Object { "($((Get-HexLatLon $_.Lat $_.Lon) -join ','))" }) -join ' -> ')"
Write-Output "Allegheny: $(($allegheny | ForEach-Object { "($((Get-HexLatLon $_.Lat $_.Lon) -join ','))" }) -join ' -> ')"

Write-Output ""
Write-Output "=== RIVER COURSES ==="

# --- RIVERS ---
# South Fork Shenandoah: Port Republic -> Front Royal. Intermediate points = where the USGS NHD High Resolution
# flowline "South Fork Shenandoah River" (GNIS 01487411; hydro.nationalmap.gov nhd/MapServer/6, queried 2026-10-17)
# crosses each latitude. It runs WEST of Luray, not east.
$southFork = @(
    @{ Lat=38.2962; Lon=78.8106 }  # Port Republic (GNIS 1496108)
    @{ Lat=38.35; Lon=78.705 }  # NHD flowline crossing (was 78.75)
    @{ Lat=38.40; Lon=78.627 }  # NHD flowline crossing (was 78.72)
    @{ Lat=38.48; Lon=78.624 }  # NHD flowline crossing (was 78.65)
    @{ Lat=38.55; Lon=78.586 }  # NHD flowline crossing (was 78.55)
    @{ Lat=38.60; Lon=78.572 }  # NHD flowline crossing (was 78.48); Alongside Massanutten (east side)
    @{ Lat=38.65; Lon=78.544 }  # NHD flowline crossing (was 78.42); was east of Luray, now west (Luray GNIS 1498510 is 38.6654/78.4594)
    @{ Lat=38.70; Lon=78.489 }  # NHD flowline crossing (was 78.38); river meanders here (crossings 78.501/78.489/78.487), middle one used
    @{ Lat=38.75; Lon=78.418 }  # NHD flowline crossing (was 78.33)
    @{ Lat=38.80; Lon=78.387 }  # NHD flowline crossing (was 78.28)
    @{ Lat=38.85; Lon=78.331 }  # NHD flowline crossing (was 78.23)
    @{ Lat=38.90; Lon=78.224 }  # NHD flowline crossing (was 78.20); crossings 78.253/78.224/78.219, middle one used
    @{ Lat=38.92; Lon=78.19 }  # Front Royal
)

# North Fork Shenandoah: near Harrisonburg -> Strasburg -> Front Royal
$northFork = @(
    @{ Lat=38.42; Lon=78.90 }  # Near Harrisonburg (springs)
    @{ Lat=38.50; Lon=78.85 }
    @{ Lat=38.55; Lon=78.80 }
    @{ Lat=38.60; Lon=78.75 }
    @{ Lat=38.65; Lon=78.72 }
    @{ Lat=38.72; Lon=78.68 }  # West side of Massanutten
    @{ Lat=38.78; Lon=78.65 }
    @{ Lat=38.85; Lon=78.58 }
    @{ Lat=38.90; Lon=78.52 }
    @{ Lat=38.95; Lon=78.45 }
    @{ Lat=38.98; Lon=78.38 }  # Near Strasburg, turns east
    @{ Lat=38.97; Lon=78.30 }
    @{ Lat=38.95; Lon=78.25 }
    @{ Lat=38.92; Lon=78.20 }  # Joins South Fork at Front Royal
)

# Main Shenandoah: Front Royal -> Harpers Ferry
$mainShenandoah = @(
    @{ Lat=38.92; Lon=78.19 }  # Front Royal (confluence)
    @{ Lat=38.98; Lon=78.10 }
    @{ Lat=39.05; Lon=78.00 }
    @{ Lat=39.10; Lon=77.95 }
    @{ Lat=39.15; Lon=77.90 }
    @{ Lat=39.20; Lon=77.85 }
    @{ Lat=39.25; Lon=77.80 }
    @{ Lat=39.30; Lon=77.75 }
    @{ Lat=39.33; Lon=77.73 }  # Harpers Ferry (joins Potomac)
)

# Potomac River: east-west across northern edge
$potomac = @(
    @{ Lat=39.60; Lon=79.00 }  # Far west
    @{ Lat=39.55; Lon=78.70 }
    @{ Lat=39.50; Lon=78.40 }
    @{ Lat=39.45; Lon=78.10 }
    @{ Lat=39.42; Lon=77.95 }  # Near Shepherdstown
    @{ Lat=39.38; Lon=77.80 }
    @{ Lat=39.33; Lon=77.73 }  # Harpers Ferry
)

# South River: flows into South Fork near Port Republic
$southRiver = @(
    @{ Lat=38.07; Lon=78.89 }  # Near Waynesboro
    @{ Lat=38.12; Lon=78.85 }
    @{ Lat=38.18; Lon=78.82 }
    @{ Lat=38.23; Lon=78.80 }
    @{ Lat=38.2962; Lon=78.8106 }  # Port Republic (GNIS 1496108)
)

Write-Output "South Fork: $(($southFork | ForEach-Object { "($((Get-HexLatLon $_.Lat $_.Lon) -join ','))" }) -join ' -> ')"
Write-Output "North Fork: $(($northFork | ForEach-Object { "($((Get-HexLatLon $_.Lat $_.Lon) -join ','))" }) -join ' -> ')"
Write-Output "Main Shenandoah: $(($mainShenandoah | ForEach-Object { "($((Get-HexLatLon $_.Lat $_.Lon) -join ','))" }) -join ' -> ')"
Write-Output "Potomac: $(($potomac | ForEach-Object { "($((Get-HexLatLon $_.Lat $_.Lon) -join ','))" }) -join ' -> ')"

Write-Output ""
Write-Output "=== VALLEY PIKE (main road) ==="

# --- VALLEY PIKE ---
# The main road running SW-NE through the valley
$valleyPike = @(
    @{ Lat=38.15; Lon=79.07 }  # Staunton
    @{ Lat=38.25; Lon=78.97 }
    @{ Lat=38.35; Lon=78.90 }
    @{ Lat=38.45; Lon=78.87 }  # Harrisonburg
    @{ Lat=38.55; Lon=78.82 }
    @{ Lat=38.65; Lon=78.77 }
    @{ Lat=38.65; Lon=78.67 }  # New Market
    @{ Lat=38.75; Lon=78.64 }  # Mount Jackson
    @{ Lat=38.83; Lon=78.57 }  # Edinburg
    @{ Lat=38.88; Lon=78.51 }  # Woodstock
    @{ Lat=38.94; Lon=78.44 }  # Toms Brook
    @{ Lat=38.99; Lon=78.36 }  # Strasburg
    @{ Lat=39.03; Lon=78.28 }  # Middletown
    @{ Lat=39.09; Lon=78.23 }  # Newtown (Stephens City)
    @{ Lat=39.15; Lon=78.18 }  # Kernstown
    @{ Lat=39.19; Lon=78.16 }  # Winchester
    @{ Lat=39.30; Lon=78.05 }
    @{ Lat=39.40; Lon=77.98 }
    @{ Lat=39.46; Lon=77.96 }  # Martinsburg
)

Write-Output "Valley Pike: $(($valleyPike | ForEach-Object { "($((Get-HexLatLon $_.Lat $_.Lon) -join ','))" }) -join ' -> ')"

Write-Output ""
Write-Output "=== SUMMARY ==="
Write-Output "Map: $mapWidth x $mapHeight = $($mapWidth * $mapHeight) hexes"
Write-Output "Towns: $($towns.Count)"
Write-Output "Mountain ridgelines: 4 (Blue Ridge, Massanutten, North Mountain, Allegheny)"
Write-Output "Rivers: 5 (South Fork, North Fork, Main Shenandoah, Potomac, South River)"
Write-Output "Roads: Valley Pike + secondary roads (to be added)"
