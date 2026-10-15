# Valley Campaign Map Builder v4 — Merged best of v2 + Grok v3
# 125x130 hex map, bridges, railroad flags, direction variants at build time
# River reroutes, mountain protection, crossing audit

param(
    [string]$OutputFile = "Valley Campaign 1862 - candidate.sav",
    [string]$TemplateMap = "",
    [switch]$AllowUnverifiedCrossings,
    [switch]$AllowOverwriteCandidate
)

$ErrorActionPreference = "Stop"
$gameDir = "C:\Program Files (x86)\Steam\steamapps\common\Hex of Steel"
$managedDir = "$gameDir\Hex of Steel_Data\Managed"
# Explicit template: do not read from or publish into a subscribed Workshop mod.
if ([string]::IsNullOrWhiteSpace($TemplateMap)) {
    throw "Specify -TemplateMap pointing at a trusted COPY of your own working HoS save."
}
$templateMap = (Resolve-Path -LiteralPath $TemplateMap -ErrorAction Stop).Path
$dest = [System.IO.Path]::GetFullPath($OutputFile)
if ([string]::Equals($dest, $templateMap, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "OutputFile must not overwrite the template save."
}
if ((Test-Path -LiteralPath $dest) -and -not $AllowOverwriteCandidate) {
    throw "Candidate already exists: $dest. Use a fresh output name or -AllowOverwriteCandidate (creates a backup)."
}
if ((Test-Path -LiteralPath $dest) -and $AllowOverwriteCandidate) {
    $backup = "$dest.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item -LiteralPath $dest -Destination $backup -ErrorAction Stop
    Write-Output "Saved pre-modification backup: $backup"
}
Write-Warning "Experimental candidate ONLY; not game load/save verified and not safe for Workshop publishing."

Write-Output "Loading game assemblies..."
[System.Reflection.Assembly]::LoadFrom("$managedDir\UnityEngine.CoreModule.dll") | Out-Null
[System.Reflection.Assembly]::LoadFrom("$managedDir\UnityEngine.dll") | Out-Null
[System.Reflection.Assembly]::LoadFrom("$managedDir\Assembly-CSharp.dll") | Out-Null

$mapW = 125; $mapH = 130

# =====================================================================
# TOWNS
# =====================================================================
$towns = @(
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
    @{N="Culpeper C.H.";X=89;Y=44;S=2;VP=$true;O="Union"}
    @{N="Orange C.H.";X=83;Y=29;S=1;VP=$false;O="Confederacy"}
    @{N="Gordonsville";X=79;Y=22;S=2;VP=$true;O="Confederacy"}
    @{N="Charlottesville";X=63;Y=14;S=2;VP=$true;O="Confederacy"}
    @{N="Mechum's River";X=50;Y=16;S=1;VP=$false;O="Confederacy"}
    @{N="Warrenton";X=100;Y=61;S=2;VP=$true;O="Union"}
    @{N="Sperryville";X=76;Y=57;S=1;VP=$false;O="Confederacy"}
    @{N="Madison C.H.";X=75;Y=38;S=1;VP=$false;O="Confederacy"}
    @{N="Stanardsville";X=65;Y=33;S=1;VP=$false;O="Confederacy"}
    # --- Polish pass: strategic locations & gap labels ---

    @{N="Conrad's Store";X=51;Y=37;S=1;VP=$false;O="Confederacy"}

    @{N="Cedarville";X=76;Y=77;S=1;VP=$false;O="Confederacy"}
    @{N="Berryville";X=87;Y=90;S=1;VP=$false;O="Union"}

)

# =====================================================================
# MOUNTAIN RIDGES
# =====================================================================
$blueRidge  = @(37,0, 40,9, 43,16, 48,26, 54,36, 59,43, 70,53, 75,60, 83,71, 89,78, 94,88, 100,98, 102,105, 106,129)
$massanutten= @(50,40, 52,43, 54,47, 57,50, 59,53, 60,57, 62,60, 64,64, 67,67, 69,71, 71,74, 73,76)
$northMtn   = @(20,0, 22,12, 24,22, 30,33, 35,43, 40,53, 46,64, 54,74, 59,85, 65,95, 67,105, 70,129)
$allegheny  = @(2,0, 3,9, 5,19, 5,33, 8,47, 14,60, 16,74, 19,88, 22,102, 24,116, 26,129)

$brHW = 2; $msHW = 2; $nmHW = 2; $alHW = 3

# =====================================================================
# MOUNTAIN GAPS
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
    @{X=103;Y=103;R=4}  # Harpers Ferry water gap
)
$massanuttenGaps = @(
    @{X=60;Y=57;R=3}   # New Market Gap
)
$northMtnGaps = @(
    @{X=25;Y=26;R=4}   # Buffalo Gap / Staunton-to-McDowell corridor
)
$alleghenyGaps = @(
    @{X=5;Y=40;R=4},   # Monterey approach
    @{X=8;Y=35;R=3}    # Westward McDowell route
)

# =====================================================================
# RIVERS — rerouted Potomac north, North Fork shifted to avoid Valley Pike
# =====================================================================
$riverSouthFork   = @(46,33, 48,36, 50,40, 54,45, 59,50, 63,53, 66,57, 68,60, 71,64, 74,67, 76,71, 78,74, 78,75)
$riverNorthFork   = @(37,41, 39,47, 43,50, 45,53, 48,57, 51,62, 54,66, 58,71, 61,74, 65,78, 68,80, 73,79, 75,78, 78,76)
$riverMainShen    = @(78,76, 83,80, 89,85, 91,88, 94,91, 97,95, 100,98, 102,102, 103,103)
$riverPotomac     = @(35,125, 51,125, 67,124, 83,121, 91,118, 97,113, 100,109, 103,103)
$riverSouth       = @(41,17, 43,20, 45,24, 46,28, 46,33)
$riverRapidan     = @(59,38, 64,37, 69,36, 74,35, 79,32, 83,29, 87,28, 92,27, 97,26, 102,25, 107,24, 112,23)
$riverRappahannock= @(73,60, 78,58, 82,56, 86,54, 90,52, 94,50, 98,49, 103,48, 108,47, 113,46, 118,45)
$riverRobinson    = @(73,50, 75,45, 76,40, 78,36, 79,33)
$riverRivanna     = @(51,19, 55,17, 59,16, 63,15, 67,13, 71,11, 75,9, 79,7)
$riverCedarCreek  = @(59,80, 61,79, 63,79, 65,78, 67,78)

# =====================================================================
# ROADS
# =====================================================================
$valleyPike = @(31,22, 33,26, 35,30, 37,34, 39,38, 41,41, 42,43, 44,47, 46,50, 49,53, 51,55, 53,57, 54,60, 54,63, 56,66, 58,69, 60,71, 62,73, 64,75, 65,77, 67,78, 69,79, 70,80, 72,81, 74,83, 75,85, 76,87, 77,89, 79,91, 80,93, 80,94, 83,98, 85,101, 88,105, 89,109, 91,113)
$rdStauntonMcD  = @(31,22, 27,25, 23,27, 19,29, 15,31, 11,32, 9,33)
$rdMcDMonterey  = @(9,33, 8,35, 7,37, 6,39, 5,40, 4,41)
$rdHburgPR      = @(42,43, 43,41, 44,39, 45,37, 46,35, 46,33)
$rdNMktLuray    = @(53,57, 56,57, 59,57, 61,57, 64,58)
$rdFRStrasburg  = @(78,75, 76,77, 74,78, 72,79, 70,80)
$rdWinchFR      = @(80,94, 80,91, 79,88, 79,85, 79,82, 79,79, 78,77, 78,75)
$rdWinchHF      = @(80,94, 83,96, 86,98, 89,100, 92,101, 96,101, 99,102, 103,103)
$rdRockfish     = @(41,17, 42,16, 43,15, 45,14, 50,14, 55,14, 60,14, 63,14)
$rdBrowns       = @(46,33, 47,31, 48,29, 49,28, 49,25, 50,22, 50,19, 50,16)
$rdSwiftRun     = @(48,38, 50,37, 52,37, 54,36, 57,35, 60,34, 63,33, 65,33)
$rdThornton     = @(64,58, 67,57, 70,56, 72,56, 74,57, 76,57)
$rdChester      = @(79,72, 81,70, 82,69, 84,67, 86,65)
$rdManassasGap  = @(78,75, 80,74, 83,73, 85,73, 88,72, 92,70)
$rdAshbys       = @(87,84, 89,83, 92,83, 95,82, 98,81, 101,80)
$rdSnickers     = @(90,89, 92,89, 94,88, 97,87, 100,86, 103,85)
$rdBRFoot       = @(63,14, 63,18, 63,22, 64,26, 65,30, 65,33, 67,35, 70,36, 73,37, 75,38, 75,41, 75,44, 75,47, 76,50, 76,53, 76,57)
$rdCulpGordon   = @(89,44, 87,40, 86,37, 85,34, 84,31, 83,29, 82,27, 81,25, 80,23, 79,22)
$rdCulpSperry   = @(89,44, 87,46, 85,48, 83,50, 81,52, 79,54, 78,56, 76,57)
$rdCulpWarren   = @(89,44, 91,47, 93,50, 95,53, 97,56, 99,59, 100,61)
$rdCvilleGordon = @(63,14, 66,15, 69,17, 72,19, 75,20, 79,22)
$rdWarrenEast   = @(100,61, 103,63, 106,65, 109,67, 112,69, 115,71)
# --- Polish pass: new roads ---
$rdLurayFR      = @(64,58, 66,60, 68,63, 70,66, 72,69, 74,72, 76,74, 78,75)
$rdCedarMid     = @(76,77, 75,79, 75,81, 74,83)
$rdHFMartinsburg= @(103,103, 100,107, 97,110, 94,112, 91,113)
$rdBerryville   = @(80,94, 83,93, 85,91, 87,90, 90,89)

# =====================================================================
# RAILROADS
# =====================================================================
$rrVirginiaCentral = @(31,22, 35,21, 38,19, 41,17, 43,16, 46,16, 50,16, 53,15, 56,14, 59,14, 63,14, 66,15, 69,17, 72,19, 75,20, 79,22, 83,22, 87,22, 91,22, 95,22)
$rrManassasGap    = @(70,80, 73,79, 76,77, 78,75, 80,74, 83,73, 85,73, 88,72, 92,70, 96,68, 100,66, 104,64, 108,62, 112,60, 116,58)
$rrOandA          = @(79,22, 80,24, 81,26, 83,29, 84,32, 85,35, 86,38, 87,41, 89,44, 90,47, 92,50, 94,53, 96,56, 98,59, 100,61, 103,64, 106,67, 110,70)
# --- Polish pass: critical missing railroads ---
$rrWinchPotomac   = @(80,94, 83,96, 86,98, 89,100, 92,101, 96,101, 99,102, 103,103)
$rrBandO          = @(103,103, 100,107, 97,110, 94,112, 91,113, 87,116, 83,119)

# =====================================================================
# CROSSING SITES — named locations where bridges are authorized
# =====================================================================
$crossingSites = @(
    @{Name="Port Republic";X=46;Y=33;R=3;Kind="Bridge"},
    @{Name="Front Royal";X=78;Y=75;R=3;Kind="Bridge"},
    @{Name="Strasburg";X=70;Y=80;R=3;Kind="Bridge"},
    @{Name="Harpers Ferry";X=103;Y=103;R=4;Kind="Bridge"},
    @{Name="Waynesboro";X=41;Y=17;R=3;Kind="Bridge"},
    @{Name="Charlottesville";X=63;Y=14;R=3;Kind="Bridge"},
    @{Name="Orange CH";X=83;Y=29;R=4;Kind="Bridge"},
    @{Name="Woodstock";X=64;Y=76;R=3;Kind="Bridge"},
    @{Name="Rivanna Bridge";X=64;Y=14;R=2;Kind="Bridge"},
    @{Name="Cross Keys";X=69;Y=36;R=2;Kind="Bridge"},
    @{Name="Bridgewater";X=49;Y=38;R=2;Kind="Bridge"},
    @{Name="Robinson River";X=75;Y=44;R=3;Kind="Bridge"},
    @{Name="Rappahannock Ford";X=93;Y=50;R=3;Kind="Bridge"},
    @{Name="Luray";X=66;Y=57;R=2;Kind="Bridge"},
    @{Name="Tom's Brook";X=77;Y=77;R=2;Kind="Bridge"},
    @{Name="Cedar Creek";X=73;Y=79;R=2;Kind="Bridge"},
    @{Name="Opequon Creek";X=88;Y=83;R=2;Kind="Bridge"},
    @{Name="Berryville";X=92;Y=89;R=2;Kind="Bridge"},
    @{Name="Rivanna Railroad";X=64;Y=14;R=1;Kind="Bridge"},
    @{Name="Port Republic South";X=46;Y=34;R=1;Kind="Bridge"},
    @{Name="Robinson River South";X=75;Y=46;R=2;Kind="Bridge"},
    @{Name="Rappahannock East";X=94;Y=50;R=2;Kind="Bridge"},
    @{Name="Tom's Brook East";X=76;Y=77;R=1;Kind="Bridge"},
    @{Name="Tumbling Run";X=72;Y=79;R=2;Kind="Bridge"},
    @{Name="Strasburg North";X=71;Y=80;R=1;Kind="Bridge"},
    @{Name="Port Republic North";X=46;Y=32;R=1;Kind="Bridge"},
    @{Name="Robinson River Mid";X=75;Y=43;R=1;Kind="Bridge"},
    @{Name="Front Royal South";X=78;Y=76;R=1;Kind="Bridge"},
    @{Name="Cedar Creek East";X=74;Y=78;R=2;Kind="Bridge"},
    @{Name="Robinson River Ford";X=75;Y=45;R=1;Kind="Bridge"},
    @{Name="Cedar Creek West";X=75;Y=78;R=1;Kind="Bridge"},
    # --- Polish pass: new crossing sites ---
    @{Name="Cedar Creek Pike";X=67;Y=78;R=2;Kind="Bridge"},
    @{Name="B&O Potomac";X=102;Y=105;R=3;Kind="Bridge"},
    @{Name="Berryville Bridge";X=87;Y=90;R=2;Kind="Bridge"}
)

# =====================================================================
# HELPER FUNCTIONS
# =====================================================================
$script:EvenOff = @(0,-1, 1,0, 1,1, 0,1, -1,1, -1,0)
$script:OddOff  = @(0,-1, 1,-1, 1,0, 0,1, -1,0, -1,-1)
$script:DirLookup = @{
    "0,3"=1; "1,4"=2; "2,5"=3
    "1,5"=4; "2,4"=5; "0,4"=6; "0,2"=7; "1,3"=8; "3,5"=9
}
# Sprite orientation is NOT shared between rivers and rails.
# Verified from actual images in civilhex.zip (edges run clockwise from top).
$script:RailDirLookup = @{
    "0,3"=1; "1,4"=2; "2,5"=3; "1,5"=4; "2,4"=5
    "0,2"=6; "1,3"=7; "3,5"=8; "0,4"=9
}
$script:RiverJunctionLookup = @{
    "1,3,5"=10; "0,2,4"=11; "0,1,3"=12
}

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
            if ($lx -ge 0 -and $lx -lt $mapW -and $ly -ge 0 -and $ly -lt $mapH) {
                $hexes.Add($ly * $mapW + $lx) | Out-Null
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

function Test-IsMountain {
    param([int]$X,[int]$Y,$BR,$MS,$NM,$AL)
    if ($null -ne $AL -and [Math]::Abs($X-$AL) -le $alHW -and -not (In-Gap $X $Y $alleghenyGaps)) { return $true }
    if ($null -ne $NM -and [Math]::Abs($X-$NM) -le $nmHW -and -not (In-Gap $X $Y $northMtnGaps)) { return $true }
    if ($null -ne $BR -and [Math]::Abs($X-$BR) -le $brHW -and -not (In-Gap $X $Y $blueRidgeGaps)) { return $true }
    if ($null -ne $MS -and [Math]::Abs($X-$MS) -le $msHW -and -not (In-Gap $X $Y $massanuttenGaps)) { return $true }
    return $false
}

function Get-CrossingSite {
    param([int]$X,[int]$Y)
    $best = $null; $bestDist = 9999
    foreach ($site in $crossingSites) {
        if ([Math]::Abs($X-$site.X) -le $site.R -and [Math]::Abs($Y-$site.Y) -le $site.R) {
            $dist = [Math]::Max([Math]::Abs($X-$site.X),[Math]::Abs($Y-$site.Y))
            if ($dist -lt $bestDist) { $best = $site; $bestDist = $dist }
        }
    }
    return $best
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
        if ($nx -lt 0 -or $nx -ge $mapW -or $ny -lt 0 -or $ny -ge $mapH) { continue }
        if ($Set.Contains($ny * $mapW + $nx)) { $edges.Add($dir) }
    }
    return $edges
}

function Get-LinkVariant {
    param($Edges, [ValidateSet("River","Road","Railroad")][string]$Kind="River")
    $use = @($Edges | Sort-Object -Unique)
    if ($use.Count -lt 2) { return $null } # no made-up extra edge for endpoints
    $key = $use -join ","
    if ($Kind -eq "Railroad") {
        if ($script:RailDirLookup.ContainsKey($key)) { return $script:RailDirLookup[$key] }
        return $null
    }
    if ($Kind -eq "River" -and $script:RiverJunctionLookup.ContainsKey($key)) {
        return $script:RiverJunctionLookup[$key]
    }
    # Native Road sprite atlas still needs independent verification.
    if ($script:DirLookup.ContainsKey($key)) { return $script:DirLookup[$key] }
    return $null  # no approximations that visibly terminate at the wrong edge
}

function Get-BridgeName {
    param([int]$Variant, [bool]$IsRailroad=$false)
    if ($IsRailroad) {
        if ($Variant -ge 1 -and $Variant -le 14) { return "River${Variant}BridgeRailroad" }
        throw "No supported railroad bridge tile for River$Variant"
    } else {
        if ($Variant -ge 2 -and $Variant -le 15) { return "River${Variant}Bridge" }
        throw "No supported road bridge tile for River$Variant"
    }
}

function Get-RailName {
    param([int]$Variant,[bool]$AlsoRoad)
    if ($AlsoRoad) {
        if ($Variant -ge 1 -and $Variant -le 16) { return "RailroadCross$Variant" }
        return "RailroadCross6"
    }
    if ($Variant -ge 1 -and $Variant -le 9) { return "Railroad$Variant" }
    throw "Unsupported railroad variant $Variant"
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
# PRE-TRACE ALL FEATURES (using $hk to avoid $h/$H collision)
# =====================================================================
Write-Output "Tracing geographic features..."

$riverSet = New-Object System.Collections.Generic.HashSet[int]
foreach ($hk in (Trace-Path $riverSouthFork))    { $riverSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $riverNorthFork))    { $riverSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $riverMainShen))     { $riverSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $riverPotomac))      { $riverSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $riverSouth))        { $riverSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $riverRapidan))      { $riverSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $riverRappahannock)) { $riverSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $riverRobinson))     { $riverSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $riverRivanna))      { $riverSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $riverCedarCreek))   { $riverSet.Add($hk) | Out-Null }

$roadSet = New-Object System.Collections.Generic.HashSet[int]
foreach ($hk in (Trace-Path $valleyPike))    { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdStauntonMcD)) { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdMcDMonterey)) { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdHburgPR))     { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdNMktLuray))   { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdFRStrasburg)) { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdWinchFR))     { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdWinchHF))     { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdRockfish))    { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdBrowns))      { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdSwiftRun))    { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdThornton))    { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdChester))     { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdManassasGap)) { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdAshbys))      { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdSnickers))    { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdBRFoot))      { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdCulpGordon))  { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdCulpSperry))  { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdCulpWarren))  { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdCvilleGordon)){ $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdWarrenEast))  { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdLurayFR))         { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdCedarMid))        { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdHFMartinsburg))   { $roadSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rdBerryville))      { $roadSet.Add($hk) | Out-Null }

$rrSet = New-Object System.Collections.Generic.HashSet[int]
foreach ($hk in (Trace-Path $rrVirginiaCentral)) { $rrSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rrManassasGap))     { $rrSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rrOandA))           { $rrSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rrWinchPotomac))    { $rrSet.Add($hk) | Out-Null }
foreach ($hk in (Trace-Path $rrBandO))           { $rrSet.Add($hk) | Out-Null }

# =====================================================================
# CROSSING RESOLUTION — find bridge hexes at named sites
# =====================================================================
$approvedCrossings = @{}
$unresolvedCrossings = @{}
foreach ($idx in $riverSet) {
    if (-not ($roadSet.Contains($idx) -or $rrSet.Contains($idx))) { continue }
    $cx = [int]($idx % $mapW); $cy = [int][Math]::Floor($idx / $mapW)
    # A nearby named place is NOT evidence of an intact bridge or ford in 1862.
    if (-not $AllowUnverifiedCrossings) {
        $unresolvedCrossings[$idx] = @{X=$cx;Y=$cy}
        continue
    }
    $site = Get-CrossingSite $cx $cy
    if ($null -eq $site) { $unresolvedCrossings[$idx] = @{X=$cx;Y=$cy}; continue }
    if (-not $approvedCrossings.ContainsKey($site.Name)) {
        $approvedCrossings[$site.Name] = $idx
    } else {
        $existIdx = $approvedCrossings[$site.Name]
        $exX = [int]($existIdx % $mapW); $exY = [int][Math]::Floor($existIdx / $mapW)
        $existDist = [Math]::Max([Math]::Abs($exX-$site.X),[Math]::Abs($exY-$site.Y))
        $newDist = [Math]::Max([Math]::Abs($cx-$site.X),[Math]::Abs($cy-$site.Y))
        if ($newDist -lt $existDist) {
            $unresolvedCrossings[$existIdx] = @{X=$exX;Y=$exY}
            $approvedCrossings[$site.Name] = $idx
        } else {
            $unresolvedCrossings[$idx] = @{X=$cx;Y=$cy}
        }
    }
}
$bridgeIdxSet = New-Object System.Collections.Generic.HashSet[int]
foreach ($idx in $approvedCrossings.Values) { $bridgeIdxSet.Add($idx) | Out-Null }

$townMap = @{}
foreach ($t in $towns) { $townMap["$($t.Y)_$($t.X)"] = $t }

Write-Output "  Rivers: $($riverSet.Count) hexes"
Write-Output "  Roads: $($roadSet.Count) hexes"
Write-Output "  Railroads: $($rrSet.Count) hexes"
Write-Output "  Towns: $($townMap.Count)"
Write-Output "  Approved bridges: $($bridgeIdxSet.Count)"
Write-Output "  Unresolved crossings: $($unresolvedCrossings.Count) (left as river)"
# Refuse to ship a map where a supposed road/rail crossing silently becomes water.
if ($unresolvedCrossings.Count -gt 0) {
    throw "Unresolved road/rail river intersections: $($unresolvedCrossings.Count). Survey bridges/fords and reroute before building a playable .sav."
}


# =====================================================================
# TERRAIN COMPUTATION
# =====================================================================
Write-Output "Computing terrain for $mapW x $mapH = $($mapW*$mapH) hexes..."
$terrain = New-Object int[] ($mapW * $mapH)

for ($y = 0; $y -lt $mapH; $y++) {
    $brx = Interp-Ridge $blueRidge $y
    $msx = Interp-Ridge $massanutten $y
    $nmx = Interp-Ridge $northMtn $y
    $alx = Interp-Ridge $allegheny $y

    for ($x = 0; $x -lt $mapW; $x++) {
        $idx = $y * $mapW + $x
        $key = "${y}_${x}"

        if ($x -lt 2 -or $x -ge ($mapW-2) -or $y -lt 2 -or $y -ge ($mapH-2)) {
            $terrain[$idx] = 0; continue
        }

        $isMtn = Test-IsMountain $x $y $brx $msx $nmx $alx

        if ($townMap.ContainsKey($key) -and -not $isMtn) { $terrain[$idx] = 7; continue }

        if ($riverSet.Contains($idx)) {
            if ($bridgeIdxSet.Contains($idx) -and -not $isMtn) { $terrain[$idx] = 11 }
            else { $terrain[$idx] = 5 }
            continue
        }

        if ($isMtn) { $terrain[$idx] = 1; continue }
        if ($rrSet.Contains($idx)) { $terrain[$idx] = 8; continue }
        if ($roadSet.Contains($idx)) { $terrain[$idx] = 6; continue }

        if ($alx -ne $null -and $x -lt ($alx - $alHW)) { $terrain[$idx] = 0; continue }
        if ($alx -eq $null -and $x -lt 5) { $terrain[$idx] = 0; continue }

        if ($alx -ne $null -and $nmx -ne $null -and $x -gt ($alx+$alHW) -and $x -lt ($nmx-$nmHW)) {
            $terrain[$idx] = 3; continue
        }

        $isValley = $false
        if ($msx -ne $null) {
            $wV = ($nmx -ne $null -and $x -gt ($nmx+$nmHW) -and $x -lt ($msx-$msHW))
            $eV = ($brx -ne $null -and $x -gt ($msx+$msHW) -and $x -lt ($brx-$brHW))
            if ($wV -or $eV) { $isValley = $true }
        } else {
            $wE = if ($nmx -ne $null) { $nmx+$nmHW } elseif ($alx -ne $null) { $alx+$alHW } else { 5 }
            $eE = if ($brx -ne $null) { $brx-$brHW } else { $mapW-5 }
            if ($x -gt $wE -and $x -lt $eE) { $isValley = $true }
        }
        if ($isValley) { $terrain[$idx] = 4; continue }

        if ($brx -ne $null -and $x -gt ($brx+$brHW)) {
            $dist = $x - ($brx+$brHW)
            if ($dist -le 4)     { $terrain[$idx] = 2 }
            elseif ($dist -le 8) { $terrain[$idx] = 9 }
            else                 { $terrain[$idx] = 10 }
            continue
        }

        $nearR = $false
        if ($brx -ne $null -and [Math]::Abs($x-$brx) -le ($brHW+2)) { $nearR=$true }
        if ($nmx -ne $null -and [Math]::Abs($x-$nmx) -le ($nmHW+2)) { $nearR=$true }
        if ($msx -ne $null -and [Math]::Abs($x-$msx) -le ($msHW+2)) { $nearR=$true }
        if ($alx -ne $null -and [Math]::Abs($x-$alx) -le ($alHW+2)) { $nearR=$true }
        if ($nearR) { $terrain[$idx] = 2; continue }

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
# LOAD TEMPLATE AND BUILD TILES
# =====================================================================
Write-Output "`nLoading template map..."
$compressed = [System.IO.File]::ReadAllBytes($templateMap)
$ms = New-Object System.IO.MemoryStream(,$compressed)
$ds = New-Object System.IO.Compression.DeflateStream($ms,[System.IO.Compression.CompressionMode]::Decompress)
$outMs = New-Object System.IO.MemoryStream
$ds.CopyTo($outMs); $ds.Close(); $ms.Close()
$memStr = New-Object System.IO.MemoryStream(,$outMs.ToArray()); $outMs.Close()
$bf = New-Object System.Runtime.Serialization.Formatters.Binary.BinaryFormatter
$gameData = $bf.Deserialize($memStr); $memStr.Close()

Write-Output "Building $mapW x $mapH tiles..."
$map = $gameData.map
$tilesTable = [System.Array]::CreateInstance([Tile], $mapW, $mapH)

$forestTypes = @(
    @("ThinForest","ThinForest","FilterForest",2,25),
    @("ThinForest2","ThinForest","FilterForest",2,25),
    @("ThinForest3","ThinForest","FilterForest",2,25),
    @("ThickForest","ThickForest","FilterForest",3,50),
    @("ThickForest2","ThickForest","FilterForest",3,50),
    @("ThickForest3","ThickForest","FilterForest",3,50)
)
$thinNames = @("ThinForest","ThinForest2","ThinForest3")

for ($y=0; $y -lt $mapH; $y++) {
    for ($x=0; $x -lt $mapW; $x++) {
        $idx = $y*$mapW+$x
        $tc = $terrain[$idx]
        $key = "${y}_${x}"
        $hash = ($x*31 + $y*97 + $x*$y*13) % 100

        switch ($tc) {
            0 { $tilesTable[$x,$y] = Make-Tile "Plain" "Plain" "FilterAll" 2 0 }
            1 { $tilesTable[$x,$y] = Make-Tile "Mountain" "Mountain" "FilterTerrain" 3 60 }
            2 {
                if ($hash -lt 40) { $tilesTable[$x,$y] = Make-Tile "Hill" "Hill" "FilterTerrain" 3 30 }
                else { $tilesTable[$x,$y] = Make-Tile "HillForest" "Hill" "FilterTerrain" 3 50 }
            }
            3 {
                $fi = ($x*7+$y*13) % $forestTypes.Count
                $ft = $forestTypes[$fi]
                $tilesTable[$x,$y] = Make-Tile $ft[0] $ft[1] $ft[2] $ft[3] $ft[4]
            }
            4 {
                if ($hash -lt 15) {
                    $tilesTable[$x,$y] = Make-Tile $thinNames[$hash%3] "ThinForest" "FilterForest" 2 25
                } elseif ($hash -lt 22) {
                    $tilesTable[$x,$y] = Make-Tile "Hill" "Hill" "FilterTerrain" 3 15
                } else {
                    $tilesTable[$x,$y] = Make-Tile "Plain" "Plain" "FilterAll" 2 0
                }
            }
            5 {
                $rv = Get-LinkVariant (Get-ConnEdges $x $y $riverSet) -Kind River
                if ($null -eq $rv) { throw "No river sprite with correct ports at ($x,$y). See topology preflight." }
                $tilesTable[$x,$y] = Make-Tile "River$rv" "River" "FilterRiver" 1 0
            }
            6 {
                $rv = Get-LinkVariant (Get-ConnEdges $x $y $roadSet) -Kind Road
                if ($null -eq $rv) { throw "No verified road ports at ($x,$y). Do not force a wrong bend." }
                $tilesTable[$x,$y] = Make-Tile "Road$rv" "Road" "FilterRoad" 1 0
            }
            7 {
                $town = $townMap[$key]
                if ($town) {
                    $tn = if ($town.O -eq "Union") {"Village Union"} else {"Village Confederacy"}
                    $tilesTable[$x,$y] = Make-Tile $tn "City" "FilterVP" 1 40 -Owner $town.O -City $town.N -VP $town.VP -Primary ($town.VP -and $town.S -eq 2)
                    if ($bridgeIdxSet.Contains($idx)) {
                        $tilesTable[$x,$y].Bridge = $true
                    }
                    if ($rrSet.Contains($idx)) {
                        $tilesTable[$x,$y].Railroad = $true
                    }
                } else {
                    $tilesTable[$x,$y] = Make-Tile "Plain" "Plain" "FilterAll" 2 0
                }
            }
            8 {
                $rv = Get-LinkVariant (Get-ConnEdges $x $y $rrSet) -Kind Railroad
                if ($null -eq $rv) { throw "No railroad sprite with correct ports at ($x,$y). See topology preflight." }
                # RailroadCrossN is switch/cross art, not an automatic overlay for a road.
                # Missing road+rail composite sprites MUST be repaired separately.
                $rn = Get-RailName $rv $false
                $tilesTable[$x,$y] = Make-Tile $rn "Plain" "FilterRailroad" 2 0
                $tilesTable[$x,$y].Railroad = $true
            }
            9 {
                if ($hash -lt 25) { $tilesTable[$x,$y] = Make-Tile $thinNames[$hash%3] "ThinForest" "FilterForest" 2 25 }
                elseif ($hash -lt 45) { $tilesTable[$x,$y] = Make-Tile "Hill" "Hill" "FilterTerrain" 3 30 }
                elseif ($hash -lt 55) { $tilesTable[$x,$y] = Make-Tile "HillForest" "Hill" "FilterTerrain" 3 50 }
                else { $tilesTable[$x,$y] = Make-Tile "Plain" "Plain" "FilterAll" 2 0 }
            }
            10 {
                if ($hash -lt 15) { $tilesTable[$x,$y] = Make-Tile $thinNames[$hash%3] "ThinForest" "FilterForest" 2 25 }
                elseif ($hash -lt 30) { $tilesTable[$x,$y] = Make-Tile "Hill" "Hill" "FilterTerrain" 3 15 }
                else { $tilesTable[$x,$y] = Make-Tile "Plain" "Plain" "FilterAll" 2 0 }
            }
            11 {
                $re = Get-ConnEdges $x $y $riverSet
                $rv = Get-LinkVariant $re -Kind River
                if ($null -eq $rv) { throw "River crossing sprite would disconnect at ($x,$y)." }
                $isRR = $rrSet.Contains($idx)
                $bn = Get-BridgeName $rv $isRR
                $tilesTable[$x,$y] = Make-Tile $bn "Plain" "FilterRoadBridge" 1 0
                $tilesTable[$x,$y].Bridge = $true
                $tilesTable[$x,$y].IsBridgeDestroyed = $false
                if ($isRR) { $tilesTable[$x,$y].Railroad = $true }
            }
        }
    }
}
Write-Output "Tiles created: $($mapW*$mapH)"

# =====================================================================
# MAP PROPERTIES
# =====================================================================
$map.SizeX = $mapW; $map.SizeY = $mapH
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

# Clear template sequel links
foreach ($nextName in @("NextMap","NextMap2","NextMapDefeat","NextMap2Defeat")) {
    try { $map.$nextName = "" } catch {}
}
try { $map.IsLastScenario = $true } catch {}

# Clear template events and units
foreach ($listName in @("Events","EventIDs","listOfUnitsThatNeedToBeKilled","listOfVPThatNeedsToBeHeld","PurchasedUnits")) {
    try {
        $val = $map.$listName
        if ($val -is [System.Collections.IList] -and -not $val.IsFixedSize) { $val.Clear() }
    } catch {}
    try {
        $val = $gameData.$listName
        if ($val -is [System.Collections.IList] -and -not $val.IsFixedSize) { $val.Clear() }
    } catch {}
}

$players = $gameData.listOfPlayers
$players.Clear()
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

$outDir = [System.IO.Path]::GetDirectoryName($dest)
if (-not (Test-Path -LiteralPath $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
[System.IO.File]::WriteAllBytes($dest, $finalBytes)

# Workshop publishing deliberately omitted; verify candidate in an isolated mod.

Write-Output "`n=== SUCCESS ==="
Write-Output "Map: $mapW x $mapH ($($mapW*$mapH) hexes)"
Write-Output "Towns: $($towns.Count) (Valley + Piedmont)"
Write-Output "Gaps: $($blueRidgeGaps.Count) BR + $($massanuttenGaps.Count) MS + $($northMtnGaps.Count) NM + $($alleghenyGaps.Count) AL"
Write-Output "Bridges: $($bridgeIdxSet.Count) approved crossings"
Write-Output "Railroads: Virginia Central, Manassas Gap, O&A, W&P, B&O (Railroad=true)"
Write-Output "Saved: $OutputFile"
Write-Output "NOT DEPLOYED: manually review, verify and import into an isolated test mod."

