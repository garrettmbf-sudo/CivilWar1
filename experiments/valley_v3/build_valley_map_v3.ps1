# Valley Campaign Map Builder v3 — layered geography, guarded deployment, audits
# 125 x 130 working grid; approximate rather than surveyed 1 mile/hex.
# Inputs are hand-digitized schematic waypoints, NOT authoritative GIS or DEM.
# SAFETY: deserialize BinaryFormatter data only from a personally trusted map.
# SAFETY: the builder never installs or overwrites Steam Workshop content by default.

param(
    [string]$OutputFile = "C:\Users\garre\ValleyCampaign\maps\Valley Campaign 1862 v3.sav",
    [string]$TemplateMap = "",
    [string]$ManifestFile = "",
    [switch]$GeometryOnly,
    [switch]$InstallToWorkshop,
    [switch]$ForceWorkshopOverwrite,
    [ValidateSet("Road", "Railroad")][string]$RailTileMode = "Railroad"
)

$ErrorActionPreference = "Stop"
$gameDir = "C:\Program Files (x86)\Steam\steamapps\common\Hex of Steel"
$managedDir = "$gameDir\Hex of Steel_Data\Managed"
$workshopDir = "C:\Program Files (x86)\Steam\steamapps\workshop\content\1240630\3773041458"
if ([string]::IsNullOrWhiteSpace($TemplateMap)) {
    $TemplateMap = "$workshopDir\Maps\An American Civil War.sav"
}
if ([string]::IsNullOrWhiteSpace($ManifestFile)) {
    $ManifestFile = [System.IO.Path]::ChangeExtension($OutputFile, ".geometry.json")
}
if ($InstallToWorkshop -and $GeometryOnly) {
    throw "-InstallToWorkshop and -GeometryOnly cannot be used together."
}

$W = 125; $H = 130

# =====================================================================
# TOWNS — hand-positioned from approximate geographic reference (not surveyed GIS)
# =====================================================================
$towns = @(
    # Valley
    @{N="Staunton";X=31;Y=22;S=2;VP=$true;O="Confederacy"}
    @{N="Waynesboro";X=41;Y=17;S=1;VP=$false;O="Confederacy"}
    @{N="McDowell";X=9;Y=33;S=1;VP=$true;O="Confederacy"}
    @{N="Port Republic";X=46;Y=33;S=1;VP=$true;O="Confederacy"}
    @{N="Cross Keys";X=45;Y=41;S=1;VP=$true;O="Confederacy"}
    @{N="Harrisonburg";X=42;Y=43;S=2;VP=$true;O="Confederacy"}
    @{N="New Market";X=53;Y=57;S=2;VP=$true;O="Confederacy"}
    @{N="Luray";X=64;Y=58;S=1;VP=$true;O="Confederacy"}
    @{N="Mt. Jackson";X=54;Y=63;S=1;VP=$false;O="Confederacy"}
    @{N="Edinburg";X=58;Y=69;S=1;VP=$false;O="Confederacy"}
    @{N="Woodstock";X=62;Y=73;S=1;VP=$false;O="Confederacy"}
    @{N="Strasburg";X=70;Y=80;S=2;VP=$true;O="Confederacy"}
    @{N="Front Royal";X=78;Y=75;S=2;VP=$true;O="Confederacy"}
    @{N="Middletown";X=74;Y=83;S=1;VP=$false;O="Confederacy"}
    @{N="Newtown";X=76;Y=87;S=1;VP=$false;O="Confederacy"}
    @{N="Kernstown";X=79;Y=91;S=1;VP=$true;O="Union"}
    @{N="Winchester";X=80;Y=94;S=2;VP=$true;O="Union"}
    @{N="Charles Town";X=96;Y=101;S=1;VP=$false;O="Union"}
    @{N="Martinsburg";X=91;Y=113;S=2;VP=$true;O="Union"}
    @{N="Harpers Ferry";X=103;Y=103;S=2;VP=$true;O="Union"}
    @{N="Moorefield";X=37;Y=85;S=1;VP=$false;O="Confederacy"}
    @{N="Franklin";X=17;Y=56;S=1;VP=$false;O="Confederacy"}
    @{N="Monterey";X=4;Y=41;S=1;VP=$false;O="Confederacy"}
    @{N="Toms Brook";X=65;Y=77;S=1;VP=$false;O="Confederacy"}
    # Piedmont
    @{N="Culpeper C.H.";X=89;Y=44;S=2;VP=$true;O="Union"}
    @{N="Orange C.H.";X=83;Y=29;S=1;VP=$false;O="Confederacy"}
    @{N="Gordonsville";X=79;Y=22;S=2;VP=$true;O="Confederacy"}
    @{N="Charlottesville";X=63;Y=14;S=2;VP=$true;O="Confederacy"}
    @{N="Mechum's River";X=50;Y=16;S=1;VP=$false;O="Confederacy"}
    @{N="Warrenton";X=100;Y=61;S=2;VP=$true;O="Union"}
    @{N="Sperryville";X=76;Y=57;S=1;VP=$false;O="Confederacy"}
    @{N="Madison C.H.";X=75;Y=38;S=1;VP=$false;O="Confederacy"}
    @{N="Stanardsville";X=65;Y=33;S=1;VP=$false;O="Confederacy"}
)

# =====================================================================
# MOUNTAIN RIDGES — flat arrays [x0,y0, x1,y1, ...] ascending Y
# Extended to map edges for full coverage
# =====================================================================
$blueRidge  = @(37,0, 40,9, 43,16, 48,26, 54,36, 59,43, 70,53, 75,60, 83,71, 89,78, 94,88, 100,98, 102,105, 106,129)
$massanutten= @(50,40, 52,43, 54,47, 57,50, 59,53, 60,57, 62,60, 64,64, 67,67, 69,71, 71,74, 73,76)
$northMtn   = @(20,0, 22,12, 24,22, 30,33, 35,43, 40,53, 46,64, 54,74, 59,85, 65,95, 67,105, 70,129)
$allegheny  = @(2,0, 3,9, 5,19, 5,33, 8,47, 14,60, 16,74, 19,88, 22,102, 24,116, 26,129)

$brHW = 2; $msHW = 2; $nmHW = 2; $alHW = 3

# =====================================================================
# MOUNTAIN GAPS — positions on the ridge where passage is allowed
# =====================================================================
$blueRidgeGaps = @(
    @{X=42;Y=14;R=3},  # Rockfish Gap
    @{X=49;Y=28;R=4},  # Brown's Gap
    @{X=54;Y=36;R=2},  # Swift Run Gap
    @{X=72;Y=56;R=3},  # Thornton's Gap
    @{X=82;Y=69;R=2},  # Chester Gap
    @{X=85;Y=73;R=2},  # Manassas Gap
    @{X=92;Y=83;R=2},  # Ashby's Gap
    @{X=94;Y=88;R=2},  # Snicker's Gap
    @{X=103;Y=103;R=4} # Harpers Ferry water gap
)
$massanuttenGaps = @(
    @{X=60;Y=57;R=3}   # New Market Gap
)
# Buffalo Gap road crosses North Mountain west of Staunton. The western
# Monterey access corridor is schematic and requires historical map review.
$northMtnGaps = @(
    @{X=25;Y=26;R=4}   # Buffalo Gap / Staunton-to-McDowell road corridor
)
$alleghenyGaps = @(
    @{X=5;Y=40;R=4},   # Monterey approach; review against historical pass
    @{X=8;Y=35;R=3}    # Westward McDowell route (schematic)
)

# =====================================================================
# RIVERS — flat waypoint arrays
# =====================================================================
$riverSouthFork   = @(46,33, 48,36, 50,40, 54,45, 59,50, 63,53, 66,57, 68,60, 71,64, 74,67, 76,71, 78,74, 78,75)
$riverNorthFork   = @(37,41, 39,47, 43,50, 45,53, 48,57, 51,62, 54,66, 58,71, 61,74, 65,78, 68,80, 73,79, 75,78, 78,76)
$riverMainShen    = @(78,76, 83,80, 89,85, 91,88, 94,91, 97,95, 100,98, 102,102, 103,104)
$riverPotomac     = @(35,125, 51,125, 67,124, 83,121, 91,118, 97,113, 100,109, 103,104)
$riverSouth       = @(41,17, 43,20, 45,24, 46,28, 46,33)
$riverRapidan     = @(59,38, 64,37, 69,36, 74,35, 79,32, 83,29, 87,28, 92,27, 97,26, 102,25, 107,24, 112,23)
$riverRappahannock= @(73,60, 78,58, 82,56, 86,54, 90,52, 94,50, 98,49, 103,48, 108,47, 113,46, 118,45)
$riverRobinson    = @(73,50, 75,45, 76,40, 78,36, 79,33)
$riverRivanna     = @(51,19, 55,17, 59,16, 63,15, 67,13, 71,11, 75,9, 79,7)

# =====================================================================
# ROADS — flat waypoint arrays
# =====================================================================
# Valley Pike
$valleyPike = @(31,22, 33,26, 35,30, 37,34, 39,38, 41,41, 42,43, 44,47, 46,50, 49,53, 51,55, 53,57, 54,60, 54,63, 56,66, 58,69, 60,71, 62,73, 64,75, 65,77, 67,78, 69,79, 70,80, 72,81, 74,83, 75,85, 76,87, 77,89, 79,91, 80,93, 80,94, 83,98, 85,101, 88,105, 89,109, 91,113)
# Valley secondary
$rdStauntonMcD  = @(31,22, 27,25, 23,27, 19,29, 15,31, 11,32, 9,33)
$rdMcDMonterey   = @(9,33, 8,35, 7,37, 6,39, 5,40, 4,41)
$rdHburgPR      = @(42,43, 43,41, 44,39, 45,37, 46,35, 46,33)
$rdNMktLuray    = @(53,57, 56,57, 59,57, 61,57, 64,58)
$rdFRStrasburg  = @(78,75, 76,77, 74,78, 72,79, 70,80)
$rdWinchFR      = @(80,94, 80,91, 79,88, 79,85, 79,82, 79,79, 78,77, 78,75)
$rdWinchHF      = @(80,94, 83,96, 86,98, 89,100, 92,101, 96,101, 99,102, 103,103)
# Gap roads (through Blue Ridge)
$rdRockfish     = @(41,17, 42,16, 43,15, 45,14, 50,14, 55,14, 60,14, 63,14)
$rdBrowns       = @(46,33, 47,31, 48,29, 49,28, 49,25, 50,22, 50,19, 50,16)
$rdSwiftRun     = @(48,38, 50,37, 52,37, 54,36, 57,35, 60,34, 63,33, 65,33)
$rdThornton     = @(64,58, 67,57, 70,56, 72,56, 74,57, 76,57)
$rdChester      = @(79,72, 81,70, 82,69, 84,67, 86,65)
$rdManassasGap  = @(78,75, 80,74, 83,73, 85,73, 88,72, 92,70)
$rdAshbys       = @(87,84, 89,83, 92,83, 95,82, 98,81, 101,80)
$rdSnickers     = @(90,89, 92,89, 94,88, 97,87, 100,86, 103,85)
# Piedmont roads
$rdBRFoot       = @(63,14, 63,18, 63,22, 64,26, 65,30, 65,33, 67,35, 70,36, 73,37, 75,38, 75,41, 75,44, 75,47, 76,50, 76,53, 76,57)
$rdCulpGordon   = @(89,44, 87,40, 86,37, 85,34, 84,31, 83,29, 82,27, 81,25, 80,23, 79,22)
$rdCulpSperry   = @(89,44, 87,46, 85,48, 83,50, 81,52, 79,54, 78,56, 76,57)
$rdCulpWarren   = @(89,44, 91,47, 93,50, 95,53, 97,56, 99,59, 100,61)
$rdCvilleGordon = @(63,14, 66,15, 69,17, 72,19, 75,20, 79,22)
$rdWarrenEast   = @(100,61, 103,63, 106,65, 109,67, 112,69, 115,71)

# =====================================================================
# RAILROADS — flat waypoint arrays
# =====================================================================
$rrVirginiaCentral = @(31,22, 35,21, 38,19, 41,17, 43,16, 46,16, 50,16, 53,15, 56,14, 59,14, 63,14, 66,15, 69,17, 72,19, 75,20, 79,22, 83,22, 87,22, 91,22, 95,22)
$rrManassasGap    = @(70,80, 73,79, 76,77, 78,75, 80,74, 83,73, 85,73, 88,72, 92,70, 96,68, 100,66, 104,64, 108,62, 112,60, 116,58)
$rrOandA          = @(79,22, 80,24, 81,26, 83,29, 84,32, 85,35, 86,38, 87,41, 89,44, 90,47, 92,50, 94,53, 96,56, 98,59, 100,61, 103,64, 106,67, 110,70)

# CROSSINGS — review-required historical approximations, NOT universal auto-bridges.
# Listed sites only authorize a road or railroad to overlay a river at their
# actual intersecting hex. Other road/river intersections remain visible river
# and are recorded as unresolved in the geometry manifest.
$crossingSites = @(
    @{Name="Port Republic bridge area";X=46;Y=33;R=3;Kind="Bridge"},
    @{Name="Front Royal confluence crossings";X=78;Y=75;R=3;Kind="Bridge"},
    @{Name="Strasburg North Fork crossings";X=70;Y=80;R=3;Kind="Bridge"},
    @{Name="Valley Pike North Fork crossing - verify";X=64;Y=76;R=1;Kind="Bridge"},
    @{Name="Harpers Ferry crossing area";X=103;Y=103;R=3;Kind="Bridge"},
    @{Name="South River at Waynesboro";X=41;Y=17;R=2;Kind="Bridge"}
)

# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

function Interp-Ridge {
    param([int[]]$Ridge, [int]$Y)
    $count = $Ridge.Count / 2
    if ($Y -lt $Ridge[1] -or $Y -gt $Ridge[($count-1)*2+1]) { return $null }
    for ($i = 0; $i -lt $count - 1; $i++) {
        $x1 = $Ridge[$i*2]; $y1 = $Ridge[$i*2+1]
        $x2 = $Ridge[($i+1)*2]; $y2 = $Ridge[($i+1)*2+1]
        if ($Y -ge $y1 -and $Y -le $y2) {
            if ($y2 -eq $y1) { return $x1 }
            return [int]($x1 + ($Y - $y1) / [double]($y2 - $y1) * ($x2 - $x1))
        }
    }
    return $null
}

function Hex-Line {
    param([int]$x1, [int]$y1, [int]$x2, [int]$y2)
    $q1=$x1; $r1=$y1-[Math]::Floor(($x1+1)/2.0); $s1=-$q1-$r1
    $q2=$x2; $r2=$y2-[Math]::Floor(($x2+1)/2.0); $s2=-$q2-$r2
    $N=[Math]::Max([Math]::Max([Math]::Abs($q2-$q1),[Math]::Abs($r2-$r1)),[Math]::Abs($s2-$s1))
    if ($N -eq 0) { return ,@($x1,$y1) }
    $res=[System.Collections.Generic.List[int]]::new()
    $prev=-1
    for ($i=0;$i -le $N;$i++) {
        $t=[double]$i/$N
        $fq=$q1+($q2-$q1)*$t; $fr=$r1+($r2-$r1)*$t; $fs=$s1+($s2-$s1)*$t
        $rq=[Math]::Round($fq); $rr=[Math]::Round($fr); $rs=[Math]::Round($fs)
        $dq=[Math]::Abs($rq-$fq); $dr=[Math]::Abs($rr-$fr); $ds=[Math]::Abs($rs-$fs)
        if ($dq -gt $dr -and $dq -gt $ds) { $rq=-$rr-$rs }
        elseif ($dr -gt $ds) { $rr=-$rq-$rs }
        $ox=[int]$rq; $oy=[int]($rr+[Math]::Floor(($rq+1)/2.0))
        $k=$oy*10000+$ox
        if ($k -ne $prev) { $res.Add($ox); $res.Add($oy); $prev=$k }
    }
    return ,$res.ToArray()
}

function Trace-Path {
    param([int[]]$WP)
    $hexes = New-Object System.Collections.Generic.HashSet[int]
    $count = $WP.Count / 2
    for ($i = 0; $i -lt $count - 1; $i++) {
        $line = Hex-Line $WP[$i*2] $WP[$i*2+1] $WP[($i+1)*2] $WP[($i+1)*2+1]
        for ($j = 0; $j -lt $line.Count; $j += 2) {
            $lx=$line[$j]; $ly=$line[$j+1]
            if ($lx -ge 0 -and $lx -lt $W -and $ly -ge 0 -and $ly -lt $H) {
                $hexes.Add($ly * $W + $lx) | Out-Null
            }
        }
    }
    return $hexes
}

function In-Gap {
    param([int]$X,[int]$Y,[array]$Gaps)
    foreach ($g in $Gaps) {
        if ([Math]::Abs($X-$g.X) -le $g.R -and [Math]::Abs($Y-$g.Y) -le $g.R) { return $true }
    }
    return $false
}

function Get-CrossingSite {
    param([int]$X,[int]$Y)
    foreach ($site in $crossingSites) {
        if ([Math]::Abs($X-$site.X) -le $site.R -and
            [Math]::Abs($Y-$site.Y) -le $site.R) { return $site }
    }
    return $null
}

# Even-q flat-top. Edge 0 is decreasing Y, then clockwise.
# Variant numbers are the stock tile suffixes already in a Hex of Steel save
# (Road1-9, River1-9). Bridge art that save actually contains is only
# River6Bridge and River10Bridge, so every permanent crossing uses one of those.
$script:EvenOff = @(0,-1, 1,0, 1,1, 0,1, -1,1, -1,0)
$script:OddOff  = @(0,-1, 1,-1, 1,0, 0,1, -1,0, -1,-1)
$script:DirLookup = @{
    "0,3"=1; "1,4"=2; "2,5"=3
    "1,5"=4; "2,4"=5; "0,4"=6; "0,2"=7; "1,3"=8; "3,5"=9
}
$script:SharpFallback = @{
    "0,1"=4; "1,2"=7; "2,3"=5; "3,4"=5; "4,5"=6; "0,5"=4
}

function Get-NeighborXY {
    param([int]$X,[int]$Y,[int]$Dir)
    $off = if ($X % 2 -eq 0) { $script:EvenOff } else { $script:OddOff }
    return @(($X + $off[$Dir * 2]), ($Y + $off[$Dir * 2 + 1]))
}

function Get-ConnEdges {
    param([int]$X,[int]$Y,$Set)
    $edges = New-Object System.Collections.Generic.List[int]
    for ($dir = 0; $dir -lt 6; $dir++) {
        $nb = Get-NeighborXY $X $Y $dir
        $nx = $nb[0]; $ny = $nb[1]
        if ($nx -lt 0 -or $nx -ge $W -or $ny -lt 0 -or $ny -ge $H) { continue }
        if ($Set.Contains($ny * $W + $nx)) { $edges.Add($dir) }
    }
    return $edges
}

function Get-LinkVariant {
    param($Edges)
    if ($Edges.Count -lt 1) { return 1 }
    $use = @($Edges)
    if ($use.Count -eq 1) { $use += (($use[0] + 3) % 6) }
    if ($use.Count -ge 3) {
        $best = $null; $bestDist = -1
        for ($i = 0; $i -lt $use.Count; $i++) {
            for ($j = $i + 1; $j -lt $use.Count; $j++) {
                $dist = [Math]::Min([Math]::Abs($use[$i] - $use[$j]), 6 - [Math]::Abs($use[$i] - $use[$j]))
                if ($dist -gt $bestDist) { $bestDist = $dist; $best = @($use[$i], $use[$j]) }
            }
        }
        $use = $best
    }
    $key = (($use | Sort-Object) -join ",")
    if ($script:DirLookup.ContainsKey($key)) { return $script:DirLookup[$key] }
    if ($script:SharpFallback.ContainsKey($key)) { return $script:SharpFallback[$key] }
    return 1
}

# Stock names confirmed in a serialized Hex of Steel map. Do not invent others:
# a destroyed/repaired tile is redrawn by Name + Season, and an unknown name
# becomes an empty black hex.
function Get-BridgeName {
    param($RiverEdges)
    if ($RiverEdges.Count -ge 3) { return "River10Bridge" }
    return "River6Bridge"
}

function Get-RailName {
    param([int]$Variant,[bool]$AlsoRoad)
    if ($AlsoRoad) { return "RailroadCross6" }
    if ($Variant -eq 6) { return "Railroad6" }
    if ($Variant -eq 9) { return "Railroad9" }
    return "Railroad1"
}

# Roads and rails are stored independently from rivers and base terrain.
# A crossing is legitimate only where a named crossing site authorizes it.
# Unknown collisions remain river hexes, not magically traversable bridges.
function Test-IsMountain {
    param([int]$X,[int]$Y,$BR,$MS,$NM,$AL)
    if ($null -ne $AL -and [Math]::Abs($X-$AL) -le $alHW -and
        -not (In-Gap $X $Y $alleghenyGaps)) { return $true }
    if ($null -ne $NM -and [Math]::Abs($X-$NM) -le $nmHW -and
        -not (In-Gap $X $Y $northMtnGaps)) { return $true }
    if ($null -ne $BR -and [Math]::Abs($X-$BR) -le $brHW -and
        -not (In-Gap $X $Y $blueRidgeGaps)) { return $true }
    if ($null -ne $MS -and [Math]::Abs($X-$MS) -le $msHW -and
        -not (In-Gap $X $Y $massanuttenGaps)) { return $true }
    return $false
}

function Make-Tile {
    param([string]$Name,[string]$Type,[string]$Filter,
          [byte]$MP,[int16]$Dmg,[string]$Owner="",[string]$City="",
          [bool]$VP=$false,[bool]$Primary=$false)
    $t = New-Object Tile
    $t.Name=$Name; $t.Type=$Type; $t.FilterType=$Filter
    $t.Season="Summer"; $t.MPCost=$MP; $t.DamageModificator=$Dmg
    $t.OwnerName=$Owner; $t.CityName=$City
    $t.IsVictoryPoint=$VP; $t.PrimaryObjective=$Primary
    $t.SecondaryObjective=$false
    $t.Bridge=$false; $t.IsBridgeDestroyed=$false; $t.Railroad=$false
    $t.Capturable=($VP -or $City -ne "")
    return $t
}

# =====================================================================
# PRE-TRACE ALL FEATURES
# =====================================================================
Write-Output "Tracing geographic features..."

$riverSet = New-Object System.Collections.Generic.HashSet[int]
foreach ($h in (Trace-Path $riverSouthFork))    { $riverSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $riverNorthFork))    { $riverSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $riverMainShen))     { $riverSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $riverPotomac))      { $riverSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $riverSouth))        { $riverSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $riverRapidan))      { $riverSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $riverRappahannock)) { $riverSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $riverRobinson))     { $riverSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $riverRivanna))      { $riverSet.Add($h) | Out-Null }

$roadSet = New-Object System.Collections.Generic.HashSet[int]
foreach ($h in (Trace-Path $valleyPike))    { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdStauntonMcD)) { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdMcDMonterey)) { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdHburgPR))     { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdNMktLuray))   { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdFRStrasburg)) { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdWinchFR))     { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdWinchHF))     { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdRockfish))    { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdBrowns))      { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdSwiftRun))    { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdThornton))    { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdChester))     { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdManassasGap)) { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdAshbys))      { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdSnickers))    { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdBRFoot))      { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdCulpGordon))  { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdCulpSperry))  { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdCulpWarren))  { $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdCvilleGordon)){ $roadSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rdWarrenEast))  { $roadSet.Add($h) | Out-Null }

$rrSet = New-Object System.Collections.Generic.HashSet[int]
foreach ($h in (Trace-Path $rrVirginiaCentral)) { $rrSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rrManassasGap))     { $rrSet.Add($h) | Out-Null }
foreach ($h in (Trace-Path $rrOandA))           { $rrSet.Add($h) | Out-Null }

# One blowable bridge per named site. Hex of Steel will not let a non-engineer
# step on FilterRiver; FilterRoadBridge is the permanent crossing. Any other
# road/rail overlap stays a river, so blowing the one bridge reseals it.
$approvedCrossings = @{}; $unresolvedCrossings = @{}
$siteGroups = @{}
foreach ($idx in $riverSet) {
    if (-not ($roadSet.Contains($idx) -or $rrSet.Contains($idx))) { continue }
    $x = [int]($idx % $W); $y = [int][Math]::Floor($idx / $W)
    $site = Get-CrossingSite $x $y
    if ($null -eq $site) { $unresolvedCrossings[$idx] = @{X=$x;Y=$y}; continue }
    if (-not $siteGroups.ContainsKey($site.Name)) { $siteGroups[$site.Name] = New-Object System.Collections.Generic.List[object] }
    $dist = [Math]::Max([Math]::Abs($x - $site.X), [Math]::Abs($y - $site.Y))
    $siteGroups[$site.Name].Add(@{Idx=$idx; Dist=$dist; Site=$site})
}
$claimed = @{}
foreach ($name in @($siteGroups.Keys)) {
    $best = $null
    foreach ($item in $siteGroups[$name]) {
        if ($claimed.ContainsKey($item.Idx)) { continue }
        if ($null -eq $best -or $item.Dist -lt $best.Dist) { $best = $item }
    }
    if ($null -ne $best) {
        $approvedCrossings[$best.Idx] = $best.Site
        $claimed[$best.Idx] = $true
    }
}
foreach ($name in @($siteGroups.Keys)) {
    foreach ($item in $siteGroups[$name]) {
        if ($approvedCrossings.ContainsKey($item.Idx)) { continue }
        $ux = [int]($item.Idx % $W); $uy = [int][Math]::Floor($item.Idx / $W)
        $unresolvedCrossings[$item.Idx] = @{X=$ux;Y=$uy}
    }
}
$blockedPassages = New-Object System.Collections.Generic.HashSet[int]

$townMap = @{}
foreach ($t in $towns) { $townMap["$($t.Y)_$($t.X)"] = $t }

Write-Output "  Rivers: $($riverSet.Count) hexes"
Write-Output "  Roads: $($roadSet.Count) hexes"
Write-Output "  Railroads: $($rrSet.Count) hexes"
Write-Output "  Towns: $($townMap.Count)"

# =====================================================================
# TERRAIN COMPUTATION
# Codes: 0=offmap, 1=mountain, 2=hill, 3=forest, 4=valley_plain,
#        5=river (FilterRiver, blocks non-engineers), 6=road, 7=town,
#        8=railroad (FilterRailroad + Railroad flag), 9=piedmont_mixed,
#        10=piedmont_open, 11=permanent bridge (FilterRoadBridge)
# =====================================================================
Write-Output "Computing terrain for $W x $H = $($W*$H) hexes..."
$terrain = New-Object int[] ($W * $H)

for ($y = 0; $y -lt $H; $y++) {
    $brx = Interp-Ridge $blueRidge $y
    $msx = Interp-Ridge $massanutten $y
    $nmx = Interp-Ridge $northMtn $y
    $alx = Interp-Ridge $allegheny $y

    for ($x = 0; $x -lt $W; $x++) {
        $idx = $y * $W + $x
        $key = "${y}_${x}"

        # Boundary first. No feature punches a hole through the map edge.
        if ($x -lt 2 -or $x -ge ($W-2) -or $y -lt 2 -or $y -ge ($H-2)) {
            $terrain[$idx] = 0; continue
        }

        # Ridges are physical barriers. Roads/rails cannot silently erase them.
        $isMtn = Test-IsMountain $x $y $brx $msx $nmx $alx
        if ($isMtn -and ($roadSet.Contains($idx) -or $rrSet.Contains($idx))) {
            $blockedPassages.Add($idx) | Out-Null
        }

        # Keep named towns at riverbanks and mark approved crossings separately.
        if ($townMap.ContainsKey($key) -and -not $isMtn) {
            $terrain[$idx] = 7; continue
        }

        # Preserve river courses at natural water gaps; roads must use named
        # crossings, and remain interrupted at unresolved collisions.
        if ($riverSet.Contains($idx)) {
            if ($approvedCrossings.ContainsKey($idx) -and -not $isMtn) { $terrain[$idx] = 11 }
            else { $terrain[$idx] = 5 }
            continue
        }
        if ($isMtn) { $terrain[$idx] = 1; continue }

        if ($rrSet.Contains($idx)) { $terrain[$idx] = 8; continue }
        if ($roadSet.Contains($idx)) { $terrain[$idx] = 6; continue }

        # Priority 7: Terrain zones
        # West of Allegheny → offmap
        if ($alx -ne $null -and $x -lt ($alx - $alHW)) { $terrain[$idx] = 0; continue }
        if ($alx -eq $null -and $x -lt 5) { $terrain[$idx] = 0; continue }

        # Between Allegheny and North Mountain → forest
        if ($alx -ne $null -and $nmx -ne $null -and $x -gt ($alx+$alHW) -and $x -lt ($nmx-$nmHW)) {
            $terrain[$idx] = 3; continue
        }

        # Valley floor detection
        $isValley = $false
        if ($msx -ne $null) {
            $wV = ($nmx -ne $null -and $x -gt ($nmx+$nmHW) -and $x -lt ($msx-$msHW))
            $eV = ($brx -ne $null -and $x -gt ($msx+$msHW) -and $x -lt ($brx-$brHW))
            if ($wV -or $eV) { $isValley = $true }
        } else {
            $wE = if ($nmx -ne $null) { $nmx+$nmHW } elseif ($alx -ne $null) { $alx+$alHW } else { 5 }
            $eE = if ($brx -ne $null) { $brx-$brHW } else { $W-5 }
            if ($x -gt $wE -and $x -lt $eE) { $isValley = $true }
        }
        if ($isValley) { $terrain[$idx] = 4; continue }

        # East of Blue Ridge → Piedmont
        if ($brx -ne $null -and $x -gt ($brx+$brHW)) {
            $dist = $x - ($brx+$brHW)
            if ($dist -le 4)     { $terrain[$idx] = 2 }
            elseif ($dist -le 8) { $terrain[$idx] = 9 }
            else                 { $terrain[$idx] = 10 }
            continue
        }

        # Near any ridge → Hill
        $nearR = $false
        if ($brx -ne $null -and [Math]::Abs($x-$brx) -le ($brHW+2)) { $nearR=$true }
        if ($nmx -ne $null -and [Math]::Abs($x-$nmx) -le ($nmHW+2)) { $nearR=$true }
        if ($msx -ne $null -and [Math]::Abs($x-$msx) -le ($msHW+2)) { $nearR=$true }
        if ($alx -ne $null -and [Math]::Abs($x-$alx) -le ($alHW+2)) { $nearR=$true }
        if ($nearR) { $terrain[$idx] = 2; continue }

        # Default: forest
        $terrain[$idx] = 3
    }
}

$codeNames = @("Offmap","Mountain","Hill","Forest","Valley","River","Road","Town","Railroad","PiedmontMix","PiedmontOpen","Bridge")
$counts = @{}
for ($i=0;$i -lt $terrain.Length;$i++) {
    $c=$terrain[$i]; if ($counts.ContainsKey($c)){$counts[$c]++}else{$counts[$c]=1}
}
Write-Output "Terrain distribution:"
foreach ($k in ($counts.Keys | Sort-Object)) {
    $nm = if ($k -lt $codeNames.Count) { $codeNames[$k] } else { "Code$k" }
    Write-Output ("  {0}: {1}" -f $nm, $counts[$k])
}

# =====================================================================
# GEOMETRY MANIFEST — can be generated WITHOUT Hex of Steel or .NET DLLs
# =====================================================================
$approvedDetails = @(
    foreach ($idx in ($approvedCrossings.Keys | Sort-Object)) {
        $v = $approvedCrossings[$idx]
        @{X=[int]($idx % $W);Y=[int][Math]::Floor($idx/$W);Name=$v.Name;Kind=$v.Kind}
    }
)
$unresolvedDetails = @(
    foreach ($idx in ($unresolvedCrossings.Keys | Sort-Object)) {
        $unresolvedCrossings[$idx]
    }
)
$blockedDetails = @(
    foreach ($idx in $blockedPassages) {
        @{X=[int]($idx % $W);Y=[int][Math]::Floor($idx/$W)}
    }
)
$metadata = @{
    version = 3; width = $W; height = $H; date = '1862-03-23'
    note = 'Engine tiles: FilterRiver blocks non-engineers; one FilterRoadBridge (River6Bridge or River10Bridge) per named crossing; rails are FilterRailroad with Railroad=true. Names limited to tiles found in a real Hex of Steel save.'
    terrain = @($terrain)
    towns = @($towns)
    approved_crossings = $approvedDetails
    unresolved_crossings = $unresolvedDetails
    blocked_ridge_paths = $blockedDetails
    counts = @{rivers=$riverSet.Count;roads=$roadSet.Count;rails=$rrSet.Count;towns=$towns.Count}
}
$manifestDir = Split-Path -Parent $ManifestFile
if ($manifestDir -and -not (Test-Path $manifestDir)) {
    New-Item -ItemType Directory -Path $manifestDir -Force | Out-Null
}
$metadata | ConvertTo-Json -Depth 12 -Compress | Set-Content -Path $ManifestFile -Encoding UTF8
Write-Output "Geometry manifest: $ManifestFile"
Write-Output "Approved bridge tiles: $($approvedDetails.Count)"
Write-Warning "Unresolved road/rail–river collisions: $($unresolvedDetails.Count); left as rivers."
Write-Warning "Road/rail tiles through impassable ridges: $($blockedDetails.Count); left as mountain."
if ($GeometryOnly) {
    Write-Output "Geometry-only mode complete. No game files loaded or changed."
    return
}

# =====================================================================
# LOAD GAME ASSEMBLIES / TEMPLATE — trusted sources only
# =====================================================================
if (-not (Test-Path -LiteralPath $TemplateMap)) {
    throw "Trusted template map not found: $TemplateMap"
}
Write-Output "Loading game assemblies..."
foreach ($asm in @("UnityEngine.CoreModule.dll", "UnityEngine.dll", "Assembly-CSharp.dll")) {
    $dll = Join-Path $managedDir $asm
    if (-not (Test-Path -LiteralPath $dll)) { throw "Game DLL not found: $dll" }
    [System.Reflection.Assembly]::LoadFrom($dll) | Out-Null
}

# =====================================================================
# LOAD TEMPLATE AND BUILD TILES
# =====================================================================
if ([System.IO.Path]::GetFullPath($OutputFile) -eq [System.IO.Path]::GetFullPath($TemplateMap)) {
    throw "OutputFile must differ from TemplateMap; refusing to overwrite the trusted input."
}
Write-Output "`nLoading template map..."
$compressed = [System.IO.File]::ReadAllBytes($templateMap)
$ms = New-Object System.IO.MemoryStream(,$compressed)
$ds = New-Object System.IO.Compression.DeflateStream($ms,[System.IO.Compression.CompressionMode]::Decompress)
$outMs = New-Object System.IO.MemoryStream
$ds.CopyTo($outMs); $ds.Close(); $ms.Close()
$memStr = New-Object System.IO.MemoryStream(,$outMs.ToArray()); $outMs.Close()
$bf = New-Object System.Runtime.Serialization.Formatters.Binary.BinaryFormatter
$gameData = $bf.Deserialize($memStr); $memStr.Close()

Write-Output "Building $W x $H tiles..."
$map = $gameData.map
$tilesTable = [System.Array]::CreateInstance([Tile], $W, $H)

$forestTypes = @(
    @("ThinForest","ThinForest","FilterForest",3,25),
    @("ThinForest2","ThinForest","FilterForest",3,25),
    @("ThinForest3","ThinForest","FilterForest",3,25),
    @("ThickForest","ThickForest","FilterForest",3,50),
    @("ThickForest2","ThickForest","FilterForest",3,50),
    @("ThickForest3","ThickForest","FilterForest",3,50)
)
$thinNames = @("ThinForest","ThinForest2","ThinForest3")

for ($y=0; $y -lt $H; $y++) {
    for ($x=0; $x -lt $W; $x++) {
        $idx = $y*$W+$x
        $tc = $terrain[$idx]
        $key = "${y}_${x}"
        $hash = ($x*31 + $y*97 + $x*$y*13) % 100

        switch ($tc) {
            0 { $tilesTable[$x,$y] = Make-Tile "Mountain" "Mountain" "FilterTerrain" 3 60 }
            1 { $tilesTable[$x,$y] = Make-Tile "Mountain" "Mountain" "FilterTerrain" 3 60 }
            2 { # Manual: hills give a 15 damage modifier. MP 3.
                if ($hash -lt 40) { $tilesTable[$x,$y] = Make-Tile "Hill" "Hill" "FilterTerrain" 3 15 }
                else { $tilesTable[$x,$y] = Make-Tile "HillForest" "Hill" "FilterTerrain" 3 15 }
            }
            3 { # Manual: a forest costs 3.
                $fi = ($x*7+$y*13) % $forestTypes.Count
                $ft = $forestTypes[$fi]
                $tilesTable[$x,$y] = Make-Tile $ft[0] $ft[1] $ft[2] $ft[3] $ft[4]
            }
            4 {
                if ($hash -lt 12) {
                    $tilesTable[$x,$y] = Make-Tile $thinNames[$hash%3] "ThinForest" "FilterForest" 3 25
                } else {
                    $tilesTable[$x,$y] = Make-Tile "Plain" "Plain" "FilterAll" 2 0
                }
            }
            5 { # FilterRiver: impassable except engineers. Not a movement highway.
                $rv = Get-LinkVariant (Get-ConnEdges $x $y $riverSet)
                $tilesTable[$x,$y] = Make-Tile "River$rv" "River" "FilterRiver" 2 0
            }
            6 { # Manual: a road costs 1.
                $rv = Get-LinkVariant (Get-ConnEdges $x $y $roadSet)
                $tilesTable[$x,$y] = Make-Tile "Road$rv" "Road" "FilterRoad" 1 0
            }
            7 {
                $town = $townMap[$key]
                if ($town) {
                    $tn = if ($town.O -eq "Union") {"Village Union"} else {"Village Confederacy"}
                    $tilesTable[$x,$y] = Make-Tile $tn "City" "FilterVP" 1 40 -Owner $town.O -City $town.N -VP $town.VP -Primary ($town.VP -and $town.S -eq 2)
                } else {
                    $tilesTable[$x,$y] = Make-Tile "Plain" "Plain" "FilterAll" 2 0
                }
            }
            8 {
                # Real save tiles: Railroad1/6/9 and RailroadCross6, Type Plain,
                # FilterRailroad, plus the Tile.Railroad flag trains actually check.
                if ($RailTileMode -eq "Railroad") {
                    $rv = Get-LinkVariant (Get-ConnEdges $x $y $rrSet)
                    $rn = Get-RailName $rv ($roadSet.Contains($idx))
                    $tilesTable[$x,$y] = Make-Tile $rn "Plain" "FilterRailroad" 2 0
                    $tilesTable[$x,$y].Railroad = $true
                } else {
                    $rv = Get-LinkVariant (Get-ConnEdges $x $y $roadSet)
                    $tilesTable[$x,$y] = Make-Tile "Road$rv" "Road" "FilterRoad" 1 0
                }
            }
            9 {
                if ($hash -lt 30) { $tilesTable[$x,$y] = Make-Tile $thinNames[$hash%3] "ThinForest" "FilterForest" 3 25 }
                elseif ($hash -lt 50) { $tilesTable[$x,$y] = Make-Tile "Hill" "Hill" "FilterTerrain" 3 15 }
                else { $tilesTable[$x,$y] = Make-Tile "Plain" "Plain" "FilterAll" 2 0 }
            }
            10 {
                if ($hash -lt 15) { $tilesTable[$x,$y] = Make-Tile $thinNames[$hash%3] "ThinForest" "FilterForest" 3 25 }
                elseif ($hash -lt 25) { $tilesTable[$x,$y] = Make-Tile "Hill" "Hill" "FilterTerrain" 3 15 }
                else { $tilesTable[$x,$y] = Make-Tile "Plain" "Plain" "FilterAll" 2 0 }
            }
            11 { # Proven bridge tiles only. Type Plain + FilterRoadBridge, not a road painted over water.
                $re = Get-ConnEdges $x $y $riverSet
                $bn = Get-BridgeName $re
                $tilesTable[$x,$y] = Make-Tile $bn "Plain" "FilterRoadBridge" 1 0
                $tilesTable[$x,$y].Bridge = $true
                $tilesTable[$x,$y].IsBridgeDestroyed = $false
                $tilesTable[$x,$y].Railroad = $false
            }
        }
    }
}
Write-Output "Tiles created: $($W*$H)"

# =====================================================================
# MAP PROPERTIES
# =====================================================================
$map.SizeX = $W; $map.SizeY = $H
$map.TilesTable = $tilesTable
$map.ScenarioName = "The Valley Campaign of 1862"
$map.ScenarioDescription = "Jackson's legendary Shenandoah Valley Campaign, March-June 1862. Command Confederate forces in a campaign of maneuver against superior Union numbers."
$map.FileName = "Valley Campaign 1862"
$map.Date = [DateTime]::new(1862, 3, 23)
$map.NumberOfDaysThatGoesByPerTurn = 1
$map.NumberOfTurnsToWin = 100
$map.IsCampaign = $true
$map.IsWinter = $false
$map.CircularMap = $false
$map.turnCount = 0
$map.AllowSnowInWinter = $false
$map.DisableWeather = $false
# Standalone scenario. Do not keep the template's sequel links.
foreach ($nextName in @("NextMap","NextMap2","NextMapDefeat","NextMap2Defeat")) {
    if ($map.PSObject.Properties[$nextName]) { $map.$nextName = "" }
}
if ($map.PSObject.Properties["IsLastScenario"]) { $map.IsLastScenario = $true }

function Clear-GameList($obj, [string]$name) {
    if ($null -eq $obj) { return }
    $prop = $obj.PSObject.Properties[$name]
    if ($null -eq $prop -or $null -eq $prop.Value) { return }
    $value = $prop.Value
    if ($value -is [System.Collections.IList] -and -not $value.IsFixedSize) { $value.Clear(); return }
    if ($value -is [Array]) {
        $obj.$name = [System.Array]::CreateInstance($value.GetType().GetElementType(), 0)
    }
}
# Developer rule for reusing a scenario: delete events, remove players, clear units.
# Otherwise the template's order of battle is saved onto this resized map.
$players = $gameData.listOfPlayers
$players.Clear()
foreach ($bag in @($gameData, $map)) {
    foreach ($listName in @("ListOfUnits","Events","EventIDs","listOfUnitsThatNeedToBeKilled","listOfVPThatNeedsToBeHeld","PurchasedUnits")) {
        Clear-GameList $bag $listName
    }
}
$csa = New-Object Player("Confederacy")
$csa.Country="Confederacy"; $csa.Faction="Confederacy"; $csa.MoneyAmount=500
$csa.ScenarioDescription="Command Stonewall Jackson's forces in the Shenandoah Valley. Use speed, deception, and the terrain to defeat the scattered Union armies."
$players.Add($csa)
$usa = New-Object Player("Union")
$usa.Country="Union"; $usa.Faction="Union"; $usa.MoneyAmount=800
$usa.ScenarioDescription="Defend the Shenandoah Valley and threaten Jackson's flanks. Coordinate Banks, Fremont, and Shields to trap the elusive Confederates."
$players.Add($usa)

$gs = $gameData.gameSettings
$gs.fogOfWarON=$true; $gs.moraleON=$true; $gs.weatherON=$true; $gs.overrunON=$true

# =====================================================================
# SERIALIZE AND SAVE
# =====================================================================
Write-Output "`nSerializing..."
$serMs = New-Object System.IO.MemoryStream
$bf2 = New-Object System.Runtime.Serialization.Formatters.Binary.BinaryFormatter
$bf2.Serialize($serMs, $gameData)
$serialized = $serMs.ToArray(); $serMs.Close()
Write-Output "Serialized: $($serialized.Length) bytes"

Write-Output "Compressing..."
$compMs = New-Object System.IO.MemoryStream
$compDs = New-Object System.IO.Compression.DeflateStream($compMs,[System.IO.Compression.CompressionLevel]::Optimal)
$compDs.Write($serialized,0,$serialized.Length); $compDs.Close()
$finalBytes = $compMs.ToArray(); $compMs.Close()
Write-Output "Compressed: $($finalBytes.Length) bytes"

$outDir = Split-Path $OutputFile -Parent
if ($outDir -and -not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}
[System.IO.File]::WriteAllBytes($OutputFile, $finalBytes)

$modDest = "$workshopDir\Maps\Valley Campaign 1862 v3.sav"
if ($InstallToWorkshop) {
    if (-not (Test-Path -LiteralPath (Split-Path $modDest -Parent))) {
        throw "Workshop maps folder missing: $(Split-Path $modDest -Parent)"
    }
    if ((Test-Path -LiteralPath $modDest) -and -not $ForceWorkshopOverwrite) {
        throw "Workshop destination already exists. Use -ForceWorkshopOverwrite after backing it up: $modDest"
    }
    Copy-Item -LiteralPath $OutputFile -Destination $modDest -Force:$ForceWorkshopOverwrite
    Write-Output "Workshop copy: $modDest"
} else {
    Write-Output "Workshop installation SKIPPED (opt in with -InstallToWorkshop)."
}

Write-Output "`n=== SUCCESS ==="
Write-Output "Map: $W x $H ($($W*$H) hexes)"Write-Output "Towns: $($towns.Count) (Valley + Piedmont)"
Write-Output "Gaps: $($blueRidgeGaps.Count) Blue Ridge + $($massanuttenGaps.Count) Massanutten"
Write-Output "Railroads: Virginia Central, Manassas Gap, O&A"
Write-Output "Saved: $OutputFile"
Write-Output "Manifest: $ManifestFile"
