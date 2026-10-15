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

# ===== MAP DIMENSIONS =====
$W = 105  # columns (east-west)
$H = 125  # rows (north-south)

# ===== GEOGRAPHIC DATA =====
# All coordinates are hex [x, y] where x=column(E-W), y=row(N-S from south)

# Mountain ridge waypoints as flat arrays [x0,y0, x1,y1, ...]
$blueRidge = @(40,3, 43,10, 48,21, 54,31, 59,38, 70,48, 75,55, 83,66, 89,72, 94,83, 100,93, 102,100)
$massanutten = @(50,34, 52,38, 54,41, 57,45, 59,48, 61,52, 63,55, 65,59, 67,62, 69,66, 71,69, 73,71)
$northMtn = @(22,7, 24,17, 30,28, 35,38, 40,48, 46,59, 54,69, 59,79, 65,90, 67,100)
$allegheny = @(3,3, 5,14, 5,28, 8,41, 13,55, 16,69, 19,83, 22,97, 24,110)

# River waypoints as flat arrays
$riverSouthFork = @(46,28, 48,31, 50,34, 54,40, 59,45, 63,48, 66,52, 68,55, 71,59, 74,62, 76,66, 78,69, 79,70)
$riverNorthFork = @(40,36, 43,41, 46,45, 48,48, 50,52, 52,57, 54,61, 58,66, 61,69, 65,72, 68,75, 73,74, 75,72, 78,70)
$riverMainShen = @(79,70, 83,75, 89,79, 91,83, 94,86, 97,90, 100,93, 102,97, 103,99)
$riverPotomac = @(35,117, 51,114, 67,110, 83,107, 91,105, 100,102, 103,99)
$riverSouth = @(41,12, 43,15, 44,19, 45,23, 46,28)
$allRivers = @($riverSouthFork, $riverNorthFork, $riverMainShen, $riverPotomac, $riverSouth)

# Valley Pike waypoints as flat array
$valleyPike = @(31,17, 37,24, 40,31, 42,38, 45,45, 47,52, 53,52, 54,59, 58,64, 61,68, 65,72, 69,75, 74,78, 76,82, 79,86, 80,89, 86,97, 90,104, 91,108)

# Town definitions: Name, HexX, HexY, Size (1=village, 2=city), VP, Owner
$towns = @(
    @{N="Staunton";       X=31; Y=17; S=2; VP=$true;  O="Confederacy"}
    @{N="Waynesboro";     X=41; Y=12; S=1; VP=$false; O="Confederacy"}
    @{N="McDowell";       X=9;  Y=28; S=1; VP=$true;  O="Confederacy"}
    @{N="Port Republic";  X=46; Y=28; S=1; VP=$true;  O="Confederacy"}
    @{N="Cross Keys";     X=45; Y=36; S=1; VP=$true;  O="Confederacy"}
    @{N="Harrisonburg";   X=42; Y=38; S=2; VP=$true;  O="Confederacy"}
    @{N="New Market";     X=53; Y=52; S=2; VP=$true;  O="Confederacy"}
    @{N="Luray";          X=64; Y=53; S=1; VP=$false; O="Confederacy"}
    @{N="Mt. Jackson";    X=54; Y=59; S=1; VP=$false; O="Confederacy"}
    @{N="Edinburg";       X=58; Y=64; S=1; VP=$false; O="Confederacy"}
    @{N="Woodstock";      X=61; Y=68; S=1; VP=$false; O="Confederacy"}
    @{N="Strasburg";      X=69; Y=75; S=2; VP=$true;  O="Confederacy"}
    @{N="Front Royal";    X=79; Y=70; S=2; VP=$true;  O="Confederacy"}
    @{N="Middletown";     X=74; Y=78; S=1; VP=$false; O="Confederacy"}
    @{N="Newtown";        X=76; Y=82; S=1; VP=$false; O="Confederacy"}
    @{N="Kernstown";      X=79; Y=86; S=1; VP=$true;  O="Union"}
    @{N="Winchester";     X=80; Y=89; S=2; VP=$true;  O="Union"}
    @{N="Charles Town";   X=96; Y=96; S=1; VP=$false; O="Union"}
    @{N="Martinsburg";    X=91; Y=107;S=2; VP=$true;  O="Union"}
    @{N="Harpers Ferry";  X=103;Y=98; S=2; VP=$true;  O="Union"}
    @{N="Moorefield";     X=37; Y=80; S=1; VP=$false; O="Confederacy"}
    @{N="Franklin";       X=17; Y=51; S=1; VP=$false; O="Confederacy"}
)

# ===== HELPER FUNCTIONS =====

function Interp-Ridge {
    param([int[]]$Ridge, [int]$Y)
    $count = $Ridge.Count / 2
    if ($Y -lt $Ridge[1] -or $Y -gt $Ridge[($count-1)*2+1]) { return $null }
    for ($i = 0; $i -lt $count - 1; $i++) {
        $x1 = $Ridge[$i*2]; $y1 = $Ridge[$i*2+1]
        $x2 = $Ridge[($i+1)*2]; $y2 = $Ridge[($i+1)*2+1]
        if ($Y -ge $y1 -and $Y -le $y2) {
            if ($y2 -eq $y1) { return $x1 }
            $t = ($Y - $y1) / ($y2 - $y1)
            return [int]($x1 + $t * ($x2 - $x1))
        }
    }
    return $null
}

function Trace-Path {
    param([int[]]$Waypoints)
    $hexes = New-Object System.Collections.Generic.HashSet[int]
    $count = $Waypoints.Count / 2
    for ($i = 0; $i -lt $count - 1; $i++) {
        $x1 = $Waypoints[$i*2]; $y1 = $Waypoints[$i*2+1]
        $x2 = $Waypoints[($i+1)*2]; $y2 = $Waypoints[($i+1)*2+1]
        $dx = [Math]::Abs($x2 - $x1); $dy = [Math]::Abs($y2 - $y1)
        $sx = if ($x1 -lt $x2) { 1 } else { -1 }
        $sy = if ($y1 -lt $y2) { 1 } else { -1 }
        $err = $dx - $dy
        $cx = $x1; $cy = $y1
        for ($j = 0; $j -lt 500; $j++) {
            if ($cx -ge 0 -and $cx -lt $W -and $cy -ge 0 -and $cy -lt $H) {
                $hexes.Add($cy * $W + $cx) | Out-Null
            }
            if ($cx -eq $x2 -and $cy -eq $y2) { break }
            $e2 = 2 * $err
            if ($e2 -gt -$dy) { $err -= $dy; $cx += $sx }
            if ($e2 -lt $dx) { $err += $dx; $cy += $sy }
        }
    }
    return $hexes
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
    $brx = Interp-Ridge $blueRidge $y
    $nmx = Interp-Ridge $northMtn $y
    $alx = Interp-Ridge $allegheny $y
    $msx = Interp-Ridge $massanutten $y

    for ($x = 0; $x -lt $W; $x++) {
        $idx = $y * $W + $x
        $key = "${y}_${x}"

        # Priority: town > river > road > terrain zone
        if ($townMap.ContainsKey($key)) { $terrain[$idx] = 7; continue }
        if ($riverSet.Contains($idx)) { $terrain[$idx] = 5; continue }
        if ($roadSet.Contains($idx)) { $terrain[$idx] = 6; continue }

        # Allegheny check
        if ($alx -ne $null) {
            $d = $x - $alx
            if ($d -lt -4) { $terrain[$idx] = 0; continue }
            if ($d -lt 3) { $terrain[$idx] = 1; continue }
        } elseif ($x -lt 6) { $terrain[$idx] = 0; continue }

        # Blue Ridge check
        if ($brx -ne $null) {
            $d = $x - $brx
            if ($d -gt 5) { $terrain[$idx] = 0; continue }
            if ($d -gt -2) { $terrain[$idx] = 1; continue }
        } elseif ($x -gt ($W - 6)) { $terrain[$idx] = 0; continue }

        # Massanutten check
        if ($msx -ne $null) {
            $d = [Math]::Abs($x - $msx)
            if ($d -lt 3) { $terrain[$idx] = 1; continue }
        }

        # Valley floor detection
        $isValley = $false
        if ($msx -ne $null) {
            # Two forks
            if ($x -lt $msx -and $alx -ne $null -and $x -gt ($alx + 4)) {
                # West fork (Valley Pike side)
                if ($nmx -ne $null -and $x -gt ($nmx + 2)) { $isValley = $true }
                elseif ($nmx -eq $null) { $isValley = $true }
            }
            if ($x -gt $msx -and $brx -ne $null -and $x -lt ($brx - 2)) {
                # East fork (Luray/Page Valley)
                $isValley = $true
            }
        } else {
            # No Massanutten - open valley
            $westEdge = if ($nmx -ne $null) { $nmx + 2 } elseif ($alx -ne $null) { $alx + 4 } else { 10 }
            $eastEdge = if ($brx -ne $null) { $brx - 2 } else { $W - 10 }
            if ($x -gt $westEdge -and $x -lt $eastEdge) { $isValley = $true }
        }

        if ($isValley) { $terrain[$idx] = 4; continue }

        # Hill near mountain ridges
        $isHill = $false
        if ($brx -ne $null -and [Math]::Abs($x - $brx) -lt 5) { $isHill = $true }
        if ($nmx -ne $null -and [Math]::Abs($x - $nmx) -lt 4) { $isHill = $true }
        if ($msx -ne $null -and [Math]::Abs($x - $msx) -lt 5) { $isHill = $true }
        if ($alx -ne $null -and ($x - $alx) -ge 3 -and ($x - $alx) -lt 7) { $isHill = $true }

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
