# Valley Campaign Map Builder
# Generates a complete Shenandoah Valley 1862 .sav map file
# Uses an existing .sav as template (for valid GameData structure), then replaces everything

param(
    [string]$OutputFile = "C:\Users\garre\ValleyCampaign\maps\Valley Campaign 1862.sav"
)

$ErrorActionPreference = "Stop"
$gameDir = "C:\Program Files (x86)\Steam\steamapps\common\Hex of Steel"
$managedDir = "$gameDir\Hex of Steel_Data\Managed"
$workshopDir = "C:\Program Files (x86)\Steam\steamapps\workshop\content\1240630\3773041458"
$templateMap = "$workshopDir\Maps\An American Civil War.sav"

# ===== LOAD ASSEMBLIES =====
Write-Output "Loading game assemblies..."
[System.Reflection.Assembly]::LoadFrom("$managedDir\UnityEngine.CoreModule.dll") | Out-Null
[System.Reflection.Assembly]::LoadFrom("$managedDir\UnityEngine.dll") | Out-Null
[System.Reflection.Assembly]::LoadFrom("$managedDir\Assembly-CSharp.dll") | Out-Null

# ===== HEX GRID AND FRAME (shared with valley_map_data.ps1) =====
# Native even-q (HexEvenQ.ps1 = src/hex_utils.py): columns west -> east, rows increase NORTH, EVEN
# columns half a row north, MapGO pitch 4.42:5.1. (col,row) is exactly the game's Tile (PosX, PosY).
# The frame (37.70-39.71 N, 79.65-77.70 W), the grid size, the lat/lon -> hex rule AND all geography
# come from valley_map_data.ps1 (via ValleyFrame.ps1), so both scripts put every feature on the same hex.
# (Until 2026-10-17 this script had its own hand-placed copy in an old 37.90 N frame, ~14 rows south.)
. (Join-Path $PSScriptRoot 'valley_map_data.ps1') | Out-Null   # defines the frame, $towns and the feature lists

# ===== MAP DIMENSIONS =====
$Wmi = $widthMi    # frame width, miles east of $westBound
$Hmi = $heightMi   # frame height, miles north of $southBound
$W = $mapWidth     # 122 columns (0.8667 mi apart)
$H = $mapHeight    # 140 rows (1 mi apart)

# ===== GEOGRAPHIC DATA =====
# Lat/lon lists from valley_map_data.ps1 -> flat arrays of FRAME MILES [x0,y0, x1,y1, ...].
# Ridges are sorted south -> north (Interp-Ridge needs ascending y) and tested at each hex centre;
# rivers and roads are snapped to hexes and traced as game-adjacent chains (Trace-Path).
function ConvertTo-FrameMileArray {
    param($Points, [switch]$SortByY)
    $xy = foreach ($p in $Points) { ,(Get-FrameMiles $p.Lat $p.Lon) }
    if ($SortByY) { $xy = $xy | Sort-Object { $_[1] } }
    $flat = New-Object System.Collections.Generic.List[double]
    foreach ($m in $xy) { $flat.Add($m[0]); $flat.Add($m[1]) }
    return ,([double[]]$flat.ToArray())
}

# Mountain ridge waypoints
$blueRidge   = ConvertTo-FrameMileArray $blueRidge -SortByY
$massanutten = ConvertTo-FrameMileArray $massanutten -SortByY
$northMtn    = ConvertTo-FrameMileArray $northMountain -SortByY
$allegheny   = ConvertTo-FrameMileArray $allegheny -SortByY

# River waypoints
$riverSouthFork = ConvertTo-FrameMileArray $southFork
$riverNorthFork = ConvertTo-FrameMileArray $northFork
$riverMainShen  = ConvertTo-FrameMileArray $mainShenandoah
$riverPotomac   = ConvertTo-FrameMileArray $potomac
$riverSouth     = ConvertTo-FrameMileArray $southRiver
$allRivers = @($riverSouthFork, $riverNorthFork, $riverMainShen, $riverPotomac, $riverSouth)

# Valley Pike waypoints
$valleyPike = ConvertTo-FrameMileArray $valleyPike

# Town definitions: Name, D = name in valley_map_data.ps1 (hex taken from there), Size (1=village, 2=city), VP, Owner
$dataTowns = @{}
foreach ($dt in $towns) { $dataTowns[$dt.Name] = $dt }
$towns = @(
    @{N="Staunton";        D="Staunton";        S=2; VP=$true;  O="Confederacy"}
    @{N="Waynesboro";      D="Waynesboro";      S=1; VP=$false; O="Confederacy"}
    @{N="McDowell";        D="McDowell";        S=1; VP=$true;  O="Confederacy"}
    @{N="Port Republic";   D="Port Republic";   S=1; VP=$true;  O="Confederacy"}
    @{N="Cross Keys";      D="Cross Keys";      S=1; VP=$true;  O="Confederacy"}
    @{N="Harrisonburg";    D="Harrisonburg";    S=2; VP=$true;  O="Confederacy"}
    @{N="New Market";      D="New Market";      S=2; VP=$true;  O="Confederacy"}
    @{N="Luray";           D="Luray";           S=1; VP=$false; O="Confederacy"}
    @{N="Mt. Jackson";     D="Mount Jackson";   S=1; VP=$false; O="Confederacy"}
    @{N="Edinburg";        D="Edinburg";        S=1; VP=$false; O="Confederacy"}
    @{N="Woodstock";       D="Woodstock";       S=1; VP=$false; O="Confederacy"}
    @{N="Strasburg";       D="Strasburg";       S=2; VP=$true;  O="Confederacy"}
    @{N="Front Royal";     D="Front Royal";     S=2; VP=$true;  O="Confederacy"}
    @{N="Middletown";      D="Middletown";      S=1; VP=$false; O="Confederacy"}
    @{N="Newtown";         D="Newtown";         S=1; VP=$false; O="Confederacy"}
    @{N="Kernstown";       D="Kernstown";       S=1; VP=$true;  O="Union"}
    @{N="Winchester";      D="Winchester";      S=2; VP=$true;  O="Union"}
    @{N="Charles Town";    D="Charles Town";    S=1; VP=$false; O="Union"}
    @{N="Martinsburg";     D="Martinsburg";     S=2; VP=$true;  O="Union"}
    @{N="Harpers Ferry";   D="Harpers Ferry";   S=2; VP=$true;  O="Union"}
    @{N="Moorefield";      D="Moorefield";      S=1; VP=$false; O="Confederacy"}
    @{N="Franklin";        D="Franklin";        S=1; VP=$false; O="Confederacy"}
)
foreach ($t in $towns) {
    $src = $dataTowns[$t.D]
    if ($null -eq $src) { throw "Town '$($t.D)' is missing from valley_map_data.ps1" }
    $t.X = $src.HexX; $t.Y = $src.HexY
}

# ===== HELPER FUNCTIONS =====

function Interp-Ridge {
    param([double[]]$Ridge, [double]$Y)   # $Ridge in frame miles; returns ridge x (miles) at y = $Y miles
    $count = $Ridge.Count / 2
    if ($Y -lt $Ridge[1] -or $Y -gt $Ridge[($count-1)*2+1]) { return $null }
    for ($i = 0; $i -lt $count - 1; $i++) {
        $x1 = $Ridge[$i*2]; $y1 = $Ridge[$i*2+1]
        $x2 = $Ridge[($i+1)*2]; $y2 = $Ridge[($i+1)*2+1]
        if ($Y -ge $y1 -and $Y -le $y2) {
            if ($y2 -eq $y1) { return $x1 }
            $t = ($Y - $y1) / ($y2 - $y1)
            return ($x1 + $t * ($x2 - $x1))
        }
    }
    return $null
}

function Trace-Path {
    # Waypoints in frame miles -> each snapped to its even-q hex -> joined by chains of
    # adjacent hexes (Get-HexLine = hex_utils.hex_line). Returns row*W+col indices.
    param([double[]]$Waypoints)
    $hexes = New-Object System.Collections.Generic.HashSet[int]
    $count = $Waypoints.Count / 2
    for ($i = 0; $i -lt $count - 1; $i++) {
        $a = Get-HexFromXY $Waypoints[$i*2] $Waypoints[$i*2+1] 1.0
        $b = Get-HexFromXY $Waypoints[($i+1)*2] $Waypoints[($i+1)*2+1] 1.0
        foreach ($cell in (Get-HexLine $a[0] $a[1] $b[0] $b[1])) {
            $cx = $cell[0]; $cy = $cell[1]
            if ($cx -ge 0 -and $cx -lt $W -and $cy -ge 0 -and $cy -lt $H) {
                $hexes.Add($cy * $W + $cx) | Out-Null
            }
        }
    }
    return ,$hexes
}

function Make-Tile {
    param(
        [string]$Name, [string]$Type, [string]$Filter,
        [byte]$MP, [int16]$Dmg, [string]$Season = "Summer",
        [string]$Owner = "", [string]$City = "",
        [bool]$VP = $false, [bool]$Primary = $false, [bool]$Bridge = $false
    )
    $t = New-Object Tile
    $t.Name = $Name
    $t.Type = $Type
    $t.FilterType = $Filter
    $t.Season = $Season
    $t.MPCost = $MP
    $t.DamageModificator = $Dmg
    $t.OwnerName = $Owner
    $t.CityName = $City
    $t.IsVictoryPoint = $VP
    $t.PrimaryObjective = $Primary
    $t.Bridge = $Bridge
    $t.Capturable = ($VP -or $City -ne "")
    return $t
}

# ===== COMPUTE TERRAIN =====
Write-Output "Computing terrain for $W x $H = $($W * $H) hexes..."

# Pre-trace rivers and roads
$riverSet = New-Object System.Collections.Generic.HashSet[int]
foreach ($hv in (Trace-Path -Waypoints $riverSouthFork)) { $riverSet.Add($hv) | Out-Null }
foreach ($hv in (Trace-Path -Waypoints $riverNorthFork)) { $riverSet.Add($hv) | Out-Null }
foreach ($hv in (Trace-Path -Waypoints $riverMainShen))  { $riverSet.Add($hv) | Out-Null }
foreach ($hv in (Trace-Path -Waypoints $riverPotomac))   { $riverSet.Add($hv) | Out-Null }
foreach ($hv in (Trace-Path -Waypoints $riverSouth))     { $riverSet.Add($hv) | Out-Null }
$roadSet = Trace-Path -Waypoints $valleyPike

# Town lookup
$townMap = @{}
foreach ($t in $towns) { $townMap["$($t.Y)_$($t.X)"] = $t }

# Terrain codes: 0=offmap, 1=mountain, 2=hill, 3=forest, 4=plain, 5=river, 6=road, 7=town
$terrain = New-Object int[] ($W * $H)

for ($y = 0; $y -lt $H; $y++) {
    for ($x = 0; $x -lt $W; $x++) {
        $idx = $y * $W + $x
        $key = "${y}_${x}"
        # Terrain zones are judged in frame miles at this hex's true centre (even columns +0.5 mi north).
        $ctr = Get-HexCenter $x $y 1.0
        $xm = $ctr[0]; $ym = $ctr[1]
        $brx = Interp-Ridge $blueRidge $ym
        $nmx = Interp-Ridge $northMtn $ym
        $alx = Interp-Ridge $allegheny $ym
        $msx = Interp-Ridge $massanutten $ym

        # Priority: town > river > road > terrain zone
        if ($townMap.ContainsKey($key)) { $terrain[$idx] = 7; continue }
        if ($riverSet.Contains($idx)) { $terrain[$idx] = 5; continue }
        if ($roadSet.Contains($idx)) { $terrain[$idx] = 6; continue }

        # Allegheny check
        if ($alx -ne $null) {
            $d = $xm - $alx
            if ($d -lt -4) { $terrain[$idx] = 0; continue }
            if ($d -lt 3) { $terrain[$idx] = 1; continue }
        } elseif ($xm -lt 6) { $terrain[$idx] = 0; continue }

        # Blue Ridge check
        if ($brx -ne $null) {
            $d = $xm - $brx
            if ($d -gt 5) { $terrain[$idx] = 0; continue }
            if ($d -gt -2) { $terrain[$idx] = 1; continue }
        } elseif ($xm -gt ($Wmi - 6)) { $terrain[$idx] = 0; continue }

        # Massanutten check
        if ($msx -ne $null) {
            $d = [Math]::Abs($xm - $msx)
            if ($d -lt 3) { $terrain[$idx] = 1; continue }
        }

        # Valley floor detection
        $isValley = $false
        if ($msx -ne $null) {
            # Two forks
            if ($xm -lt $msx -and $alx -ne $null -and $xm -gt ($alx + 4)) {
                # West fork (Valley Pike side)
                if ($nmx -ne $null -and $xm -gt ($nmx + 2)) { $isValley = $true }
                elseif ($nmx -eq $null) { $isValley = $true }
            }
            if ($xm -gt $msx -and $brx -ne $null -and $xm -lt ($brx - 2)) {
                # East fork (Luray/Page Valley)
                $isValley = $true
            }
        } else {
            # No Massanutten - open valley
            $westEdge = if ($nmx -ne $null) { $nmx + 2 } elseif ($alx -ne $null) { $alx + 4 } else { 10 }
            $eastEdge = if ($brx -ne $null) { $brx - 2 } else { $Wmi - 10 }
            if ($xm -gt $westEdge -and $xm -lt $eastEdge) { $isValley = $true }
        }

        if ($isValley) { $terrain[$idx] = 4; continue }

        # Hill near mountain ridges
        $isHill = $false
        if ($brx -ne $null -and [Math]::Abs($xm - $brx) -lt 5) { $isHill = $true }
        if ($nmx -ne $null -and [Math]::Abs($xm - $nmx) -lt 4) { $isHill = $true }
        if ($msx -ne $null -and [Math]::Abs($xm - $msx) -lt 5) { $isHill = $true }
        if ($alx -ne $null -and ($xm - $alx) -ge 3 -and ($xm - $alx) -lt 7) { $isHill = $true }

        if ($isHill) { $terrain[$idx] = 2; continue }

        # Default: forest
        $terrain[$idx] = 3
    }
}

# Count terrain types
$counts = @{}
for ($i = 0; $i -lt $terrain.Length; $i++) {
    $t = $terrain[$i]
    if ($counts.ContainsKey($t)) { $counts[$t]++ } else { $counts[$t] = 1 }
}
$typeNames = @("Offmap", "Mountain", "Hill", "Forest", "Plain", "River", "Road", "Town")
Write-Output "Terrain distribution:"
foreach ($k in ($counts.Keys | Sort-Object)) {
    Write-Output "  $($typeNames[$k]): $($counts[$k]) hexes"
}

# ===== LOAD TEMPLATE =====
Write-Output "`nLoading template map..."
$compressed = [System.IO.File]::ReadAllBytes($templateMap)
$ms = New-Object System.IO.MemoryStream(,$compressed)
$ds = New-Object System.IO.Compression.DeflateStream($ms, [System.IO.Compression.CompressionMode]::Decompress)
$outMs = New-Object System.IO.MemoryStream
$ds.CopyTo($outMs)
$rawBytes = $outMs.ToArray()
$ds.Close(); $ms.Close(); $outMs.Close()

$memStream = New-Object System.IO.MemoryStream(,$rawBytes)
$bf = New-Object System.Runtime.Serialization.Formatters.Binary.BinaryFormatter
$gameData = $bf.Deserialize($memStream)
$memStream.Close()

Write-Output "Template loaded: $($gameData.map.SizeX) x $($gameData.map.SizeY)"

# ===== BUILD MAP =====
Write-Output "Building $W x $H Valley map..."

$map = $gameData.map

# Create new TilesTable
$tilesTable = [System.Array]::CreateInstance([Tile], $W, $H)

# Forest type rotation for variety
$forestTypes = @(
    @("ThinForest",  "ThinForest",  "FilterForest", 2, 25),
    @("ThinForest2", "ThinForest",  "FilterForest", 2, 25),
    @("ThinForest3", "ThinForest",  "FilterForest", 2, 25),
    @("ThickForest", "ThickForest", "FilterForest", 3, 50),
    @("ThickForest2","ThickForest", "FilterForest", 3, 50),
    @("ThickForest3","ThickForest", "FilterForest", 3, 50)
)

$tilesCreated = 0
for ($y = 0; $y -lt $H; $y++) {
    for ($x = 0; $x -lt $W; $x++) {
        $idx = $y * $W + $x
        $t = $terrain[$idx]
        $key = "${y}_${x}"

        switch ($t) {
            0 { # Offmap - impassable mountain
                $tilesTable[$x, $y] = Make-Tile "Mountain" "Mountain" "FilterTerrain" 3 60
            }
            1 { # Mountain
                $tilesTable[$x, $y] = Make-Tile "Mountain" "Mountain" "FilterTerrain" 3 60
            }
            2 { # Hill
                if (($x + $y) % 3 -eq 0) {
                    $tilesTable[$x, $y] = Make-Tile "Hill" "Hill" "FilterTerrain" 3 30
                } else {
                    $tilesTable[$x, $y] = Make-Tile "HillForest" "Hill" "FilterTerrain" 3 50
                }
            }
            3 { # Forest
                $fi = ($x * 7 + $y * 13) % $forestTypes.Count
                $ft = $forestTypes[$fi]
                $tilesTable[$x, $y] = Make-Tile $ft[0] $ft[1] $ft[2] $ft[3] $ft[4]
            }
            4 { # Valley floor / Plain
                $tilesTable[$x, $y] = Make-Tile "Plain" "Plain" "FilterAll" 2 0
            }
            5 { # River - use River1 as placeholder (directional assignment later)
                $tilesTable[$x, $y] = Make-Tile "River1" "River" "FilterRiver" 1 0
            }
            6 { # Road - use Road1 as placeholder
                $tilesTable[$x, $y] = Make-Tile "Road1" "Road" "FilterRoad" 1 0
            }
            7 { # Town
                $town = $townMap[$key]
                if ($town) {
                    $tileName = if ($town.O -eq "Union") { "Village Union" } else { "Village Confederacy" }
                    $tilesTable[$x, $y] = Make-Tile $tileName "City" "FilterVP" 1 40 -Owner $town.O -City $town.N -VP $town.VP -Primary ($town.VP -and $town.S -eq 2)
                } else {
                    $tilesTable[$x, $y] = Make-Tile "Plain" "Plain" "FilterAll" 2 0
                }
            }
        }
        $tilesCreated++
    }
}

Write-Output "$tilesCreated tiles created"

# Set map properties
$map.SizeX = $W
$map.SizeY = $H
$map.TilesTable = $tilesTable
$map.ScenarioName = "The Valley Campaign of 1862"
$map.ScenarioDescription = "Jackson's legendary Shenandoah Valley Campaign, March-June 1862. Command Confederate forces in a campaign of maneuver against superior Union numbers."
$map.FileName = "Valley Campaign 1862"
$map.Date = [DateTime]::new(1862, 3, 23)  # Battle of Kernstown
$map.NumberOfDaysThatGoesByPerTurn = 1
$map.NumberOfTurnsToWin = 100  # ~3 months of campaign
$map.IsCampaign = $true
$map.IsWinter = $false
$map.CircularMap = $false
$map.turnCount = 0
$map.AllowSnowInWinter = $false
$map.DisableWeather = $false

# Configure players
$players = $gameData.listOfPlayers
# Clear existing players and add new ones
$players.Clear()

$csaPlayer = New-Object Player("Confederacy")
$csaPlayer.Country = "Confederacy"
$csaPlayer.Faction = "Confederacy"
$csaPlayer.MoneyAmount = 500
$csaPlayer.ScenarioDescription = "Command Stonewall Jackson's forces in the Shenandoah Valley. Use speed, deception, and the terrain to defeat the scattered Union armies."
$players.Add($csaPlayer)

$usaPlayer = New-Object Player("Union")
$usaPlayer.Country = "Union"
$usaPlayer.Faction = "Union"
$usaPlayer.MoneyAmount = 800
$usaPlayer.ScenarioDescription = "Defend the Shenandoah Valley and threaten Jackson's flanks. Coordinate Banks, Fremont, and Shields to trap the elusive Confederates."
$players.Add($usaPlayer)

# Game settings
$gs = $gameData.gameSettings
$gs.fogOfWarON = $true
$gs.moraleON = $true
$gs.weatherON = $true
$gs.overrunON = $true

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

# Ensure output directory exists
$outDir = Split-Path $OutputFile -Parent
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

[System.IO.File]::WriteAllBytes($OutputFile, $finalBytes)
Write-Output "`n=== SUCCESS ==="
Write-Output "Valley Campaign map saved to: $OutputFile"
Write-Output "Map: $W x $H ($($W * $H) hexes)"
Write-Output "Date: March 23, 1862 (Kernstown)"
Write-Output "Players: Confederacy, Union"
