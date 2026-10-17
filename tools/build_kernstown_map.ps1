# First Kernstown map builder — BinaryFormatter via Hex of Steel assemblies
# Reads data/layers/kernstown_game.json + kernstown_units.json; paints custom SV_K tiles
# onto a trusted template .sav and places brigade/battery counters.
# SAFETY: BinaryFormatter can execute code — deserialize only a personally trusted local .sav.
# Does NOT install to Workshop by default.
# OOB cross-referenced against CivilWar1 historical_data (SRC001/SRC007).
# v0.4.2: (col,row) in kernstown_game.json IS the game's (PosX, PosY) - flat-top, rows north, EVEN columns raised
# (MapGO.cs:452-459; scripts/hex_grid.py; docs/decisions.md). No conversion is applied to the map.

param(
    [string]$LayersJson = "",
    [string]$OutputFile = "",
    [string]$TemplateMap = "",
    [string]$GameDir = "C:\Program Files (x86)\Steam\steamapps\common\Hex of Steel",
    [string]$Season = "Summer",
    [string]$UnitsJson = "",
    [string]$UnitSourceMap = "",
    [switch]$NoUnits,
    [switch]$GeometryOnly
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($LayersJson)) { $LayersJson = Join-Path $Root "data\layers\kernstown_game.json" }
if ([string]::IsNullOrWhiteSpace($OutputFile)) { $OutputFile = Join-Path $Root "mod\Maps\First Kernstown 1862.sav" }
$gameDir = $GameDir
$managedDir = "$gameDir\Hex of Steel_Data\Managed"
if ([string]::IsNullOrWhiteSpace($TemplateMap)) {
    $TemplateMap = Join-Path $Root "templates\ACW_sample_102x60.sav"
    if (-not (Test-Path $TemplateMap)) { $TemplateMap = Join-Path $Root "..\CivilWar1\maps\An American Civil War.sav" }
    if (-not (Test-Path $TemplateMap)) {
        $TemplateMap = "C:\Program Files (x86)\Steam\steamapps\workshop\content\1240630\3773041458\Maps\An American Civil War.sav"
    }
}

if ([string]::IsNullOrWhiteSpace($UnitsJson)) { $UnitsJson = Join-Path $Root "data\layers\kernstown_units.json" }
if ([string]::IsNullOrWhiteSpace($UnitSourceMap)) { $UnitSourceMap = $TemplateMap }
if (-not (Test-Path $LayersJson)) { throw "Layer file not found: $LayersJson" }
$layers = Get-Content -Raw -Path $LayersJson | ConvertFrom-Json
# NB: PowerShell variables are case-insensitive - $GridW/$GridH must not be $W/$H, or the per-hex $h loops overwrite them
$GridW = [int]$layers.cols
$GridH = [int]$layers.rows
Write-Output "Kernstown layers: ${GridW}x${GridH} ($($layers.hexes.Count) hexes) from $LayersJson"

# Rules required by the scenario (applied again here so they hold even if the JSON is edited)
# (game-native hexes; legacy v0.4.1 ids were 14_23,15_23,16_23,17_23,18_23,19_22,20_23 / 42_41 / 30_19)
$WallHexes = @("14_22","15_23","16_22","17_23","18_22","19_22","20_22")
$PrimaryVP = "42_40"
$SecondaryVP = @{ "27_20" = "Kernstown"; "30_18" = "Opequon Church" }

if ($GeometryOnly) {
    $missing = 0
    foreach ($h in $layers.hexes) {
        $png = Join-Path $Root ("mod\Graphics\Tiles\$Season\" + $h.tile_name + ".png")
        if (-not (Test-Path $png)) { $missing++ }
    }
    Write-Output "GeometryOnly - no .sav written. Missing tile PNGs: $missing"
    exit 0
}

if (-not (Test-Path $managedDir)) { throw "Hex of Steel not found at $gameDir. Run again with -GameDir ""<your Hex of Steel folder>""" }
if (-not (Test-Path $TemplateMap)) { throw "Template map not found: $TemplateMap. Run again with -TemplateMap ""<path to a .sav you trust>""" }
foreach ($asm in @("UnityEngine.CoreModule.dll","UnityEngine.dll","Assembly-CSharp.dll")) {
    $dll = Join-Path $managedDir $asm
    if (-not (Test-Path $dll)) { throw "Missing $dll" }
    [System.Reflection.Assembly]::LoadFrom($dll) | Out-Null
}

# Load template (HoS saves: raw-deflate BinaryFormatter; fall back to plain BinaryFormatter)
$bf = New-Object System.Runtime.Serialization.Formatters.Binary.BinaryFormatter
function Read-Sav([string]$Path) {
    $b = [System.IO.File]::ReadAllBytes($Path)
    try {
        $msIn = New-Object System.IO.MemoryStream(,$b)
        $def = New-Object System.IO.Compression.DeflateStream($msIn, [System.IO.Compression.CompressionMode]::Decompress)
        $msRaw = New-Object System.IO.MemoryStream
        $def.CopyTo($msRaw); $def.Close(); $msRaw.Position = 0
        return @{ Data = $bf.Deserialize($msRaw); Compressed = $true }
    } catch {
        return @{ Data = $bf.Deserialize((New-Object System.IO.MemoryStream(,$b))); Compressed = $false }
    }
}
$loaded = Read-Sav $TemplateMap
$gameData = $loaded.Data
$compressed = $loaded.Compressed
$map = $gameData.map
if ($null -eq $map) { $map = $gameData }

function Set-IfProp($obj, [string]$name, $value) {
    if ($obj.PSObject.Properties[$name]) { $obj.$name = $value }
}

function Make-Tile {
    param([string]$Name,[string]$Type,[string]$Filter,[byte]$MP,[int16]$Dmg,
          [string]$Owner="",[string]$City="",[bool]$VP=$false,[bool]$Primary=$false,[bool]$Secondary=$false,
          [bool]$Railroad=$false)
    $t = New-Object Tile
    $t.Name=$Name; $t.Type=$Type; $t.FilterType=$Filter
    $t.Season=$Season; $t.MPCost=$MP; $t.DamageModificator=$Dmg
    $t.OwnerName=$Owner; $t.CityName=$City
    $t.IsVictoryPoint=$VP; $t.PrimaryObjective=$Primary
    Set-IfProp $t "SecondaryObjective" $Secondary
    Set-IfProp $t "Bridge" $false; Set-IfProp $t "IsBridgeDestroyed" $false
    $t.Railroad=$Railroad
    Set-IfProp $t "Capturable" ($VP -or $City -ne "")
    return $t
}

$tilesTable = [System.Array]::CreateInstance([Tile], $GridW, $GridH)
$index = @{}
foreach ($h in $layers.hexes) { $index["$($h.col)_$($h.row)"] = $h }
$placed = 0
for ($y=0; $y -lt $GridH; $y++) {
    for ($x=0; $x -lt $GridW; $x++) {
        $k = "${x}_${y}"; $h = $index[$k]
        if ($null -eq $h) { throw "No layer entry for hex $k" }
        $mp = [int]$h.mp; $dmg = [int]$h.dmg
        $type = [string]$h.type; $filt = [string]$h.filter
        $city = [string]$h.city; $owner = [string]$h.owner
        $vp = [bool]$h.vp; $pri = [bool]$h.primary; $sec = [bool]$h.secondary
        if ($WallHexes -contains $k) { $dmg = 35 }
        if ($k -eq $PrimaryVP) { $vp = $true; $pri = $true; $sec = $false; $type = "City"; $filt = "FilterVP"; if ($city -eq "") { $city = "Winchester (Courthouse)" } }
        if ($SecondaryVP.ContainsKey($k)) { $vp = $true; $pri = $false; $sec = $true; if ($city -eq "") { $city = $SecondaryVP[$k] } }
        $tilesTable[$x,$y] = Make-Tile ([string]$h.tile_name) $type $filt ([byte]$mp) ([int16]$dmg) -Owner $owner -City $city -VP $vp -Primary $pri -Secondary $sec -Railroad ([bool]$h.railroad)
        $placed++
    }
}
Write-Output "Placed $placed tiles"
$map.SizeX = $GridW; $map.SizeY = $GridH
$map.TilesTable = $tilesTable
$map.ScenarioName = "First Kernstown $([char]0x2014) 23 March 1862"   # `u{...} is PS7-only; PS 5.1 printed a literal "u2014"
$map.FileName = "First Kernstown 1862"
Set-IfProp $map "ScenarioDescription" "Jackson attacks Kimball's division south of Winchester. CSA ~3,800 vs USA ~8,500. Sandy Ridge stone wall hexes give +35 defence."
$map.Date = [DateTime]::new(1862, 3, 23)
Set-IfProp $map "NumberOfDaysThatGoesByPerTurn" 1
$map.NumberOfTurnsToWin = 20
Set-IfProp $map "IsCampaign" $false
Set-IfProp $map "turnCount" 0
Set-IfProp $map "IsWinter" $false
Set-IfProp $map "CircularMap" $false
Set-IfProp $map "AllowSnowInWinter" $false
Set-IfProp $map "DisableWeather" $false
foreach ($n in @("NextMap","NextMap2","NextMapDefeat","NextMap2Defeat")) {
    if ($map.PSObject.Properties[$n]) { $map.$n = "" }
}

# Configure players (required for scenario to appear in Play > Custom scenario)
$players = $gameData.listOfPlayers
if ($null -ne $players) {
    $players.Clear()
    $csaPlayer = New-Object Player("Confederacy")
    $csaPlayer.Country = "Confederacy"
    Set-IfProp $csaPlayer "Faction" "Confederacy"
    Set-IfProp $csaPlayer "MoneyAmount" 0
    Set-IfProp $csaPlayer "ScenarioDescription" "Command Jackson's small Valley force against Kimball's division on Sandy Ridge."
    $players.Add($csaPlayer)
    $usaPlayer = New-Object Player("Union")
    $usaPlayer.Country = "Union"
    Set-IfProp $usaPlayer "Faction" "Union"
    Set-IfProp $usaPlayer "MoneyAmount" 0
    Set-IfProp $usaPlayer "ScenarioDescription" "Defend the Valley Pike approach to Winchester with Kimball's division."
    $players.Add($usaPlayer)
    Write-Output "Players: Confederacy, Union"
}

# Game settings
$gs = $gameData.gameSettings
if ($null -ne $gs) {
    Set-IfProp $gs "fogOfWarON" $true
    Set-IfProp $gs "moraleON" $true
    Set-IfProp $gs "weatherON" $false
    Set-IfProp $gs "overrunON" $true
}

# Clear units/events so template OOB does not pollute
foreach ($bag in @($map, $gameData)) {
    foreach ($listName in @("ListOfUnits","Events","EventIDs","listOfUnitsThatNeedToBeKilled","listOfVPThatNeedsToBeHeld","PurchasedUnits")) {
        if ($bag.PSObject.Properties[$listName] -and $null -ne $bag.$listName) {
            try { $bag.$listName.Clear() } catch {}
        }
    }
}

# ---- Units: clone unit templates (Name + Country) from the ACW unit-source .sav and drop them on tiles ----
function Get-CountryName($u) {
    $c = $u.Country
    if ($null -eq $c) { return [string]$u.OwnerName }
    if ($c -is [string]) { return $c }
    if ($c.PSObject.Properties["Name"]) { return [string]$c.Name }
    return [string]$c
}
function Clone-Obj($o) {
    $ms = New-Object System.IO.MemoryStream
    $bf.Serialize($ms, $o); $ms.Position = 0
    return $bf.Deserialize($ms)
}
if (-not $NoUnits -and (Test-Path $UnitsJson)) {
    $unitsSpec = Get-Content -Raw -Path $UnitsJson | ConvertFrom-Json
    if (-not (Test-Path $UnitSourceMap)) { throw "Unit source map not found: $UnitSourceMap. Run again with -UnitSourceMap ""<path to the ACW .sav with units>""" }
    $src = (Read-Sav $UnitSourceMap).Data
    $srcMap = $src.map; if ($null -eq $srcMap) { $srcMap = $src }
    $templates = @{}
    foreach ($t in $srcMap.TilesTable) {
        if ($null -eq $t) { continue }
        $gu = $t.GroundUnit
        if ($null -ne $gu) {
            $key = "$($gu.Name)|$(Get-CountryName $gu)"
            if (-not $templates.ContainsKey($key)) { $templates[$key] = $gu }
        }
    }
    Write-Output ("Unit templates found in source: " + (($templates.Keys | Sort-Object) -join ", "))
    if (-not ($unitsSpec.PSObject.Properties["grid_convention"] -and [string]$unitsSpec.grid_convention -eq "game-native")) {
        throw "kernstown_units.json must have `grid_convention: game-native` (see docs/kernstown_unit_coord_change.md)"
    }
    $nU = 0
    foreach ($u0 in $unitsSpec.units) {
        $u = $u0 | Select-Object *
        $key = "$($u.template_name)|$($u.country)"
        if (-not $templates.ContainsKey($key)) { Write-Warning "No template unit '$key' in $UnitSourceMap - skipped $($u.custom_name)"; continue }
        if ([int]$u.col -lt 0 -or [int]$u.col -ge $GridW -or [int]$u.row -lt 0 -or [int]$u.row -ge $GridH) {
            Write-Warning "Unit '$($u.custom_name)' at ($($u.col),$($u.row)) is outside grid ${GridW}x${GridH} - skipped"
            continue
        }
        $newUnit = Clone-Obj $templates[$key]
        Set-IfProp $newUnit "PosX" ([int]$u.col); Set-IfProp $newUnit "PosY" ([int]$u.row)
        Set-IfProp $newUnit "CustomName" ([string]$u.custom_name); Set-IfProp $newUnit "ForcedCustomName" $true
        Set-IfProp $newUnit "EntrenchmentLevelOnStart" ([int]$u.entrenchment_on_start)
        Set-IfProp $newUnit "EntrenchmentLevel" ([int]$u.entrenchment_on_start)
        Set-IfProp $newUnit "CurrHP" $newUnit.MaxHP; Set-IfProp $newUnit "CurrMP" $newUnit.MaxMP; Set-IfProp $newUnit "CurrAmmo" $newUnit.MaxAmmo
        $tile = $tilesTable[[int]$u.col, [int]$u.row]
        $tile.GroundUnit = $newUnit
        $nU++
        Write-Output ("  unit {0,-12} {1,-45} at {2},{3} entrench {4}" -f $u.country, $u.custom_name, $u.col, $u.row, $u.entrenchment_on_start)
    }
    Write-Output "Placed $nU units"
}

$serMs = New-Object System.IO.MemoryStream
$bf2 = New-Object System.Runtime.Serialization.Formatters.Binary.BinaryFormatter
$bf2.Serialize($serMs, $gameData)
$raw = $serMs.ToArray()
$outMs = New-Object System.IO.MemoryStream
if ($compressed) {
    $defOut = New-Object System.IO.Compression.DeflateStream($outMs, [System.IO.Compression.CompressionLevel]::Optimal)
    $defOut.Write($raw, 0, $raw.Length); $defOut.Close()
} else { $outMs.Write($raw, 0, $raw.Length) }
$dir = Split-Path -Parent $OutputFile
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
$outBytes = $outMs.ToArray()
[System.IO.File]::WriteAllBytes($OutputFile, $outBytes)
Write-Output "Wrote $OutputFile ($($outBytes.Length) bytes on disk, $($raw.Length) raw)"
Write-Output "Activate the Kernstown mod in the MODS menu before loading."
