# Hex of Steel native flat-top EVEN-Q hex math. A line-for-line port of src/hex_utils.py.
# Source of truth: the game's MapGO.cs:452-459 (tile placement) and Utils.GetAllTilesNeighbours.
#   - Columns run west -> east. Rows increase NORTH (Unity +y). (col,row) == game Tile (PosX,PosY).
#   - EVEN columns sit half a row NORTH: game position x = col*4.42, y = row*5.1 (+2.55 if col even).
#   - Ports: 0=N 1=NE 2=SE 3=S 4=SW 5=NW, opposite = (p+3)%6.
# Dot-source it:  . (Join-Path $PSScriptRoot 'HexEvenQ.ps1')
# Checked against hex_utils by tests/test_powershell_even_q.py (pwsh run + formula parse).

$script:HexGameColPitch   = 4.42
$script:HexGameRowPitch   = 5.1
$script:HexGameEvenShift  = 2.55
$script:HexColPitchRatio  = $script:HexGameColPitch / $script:HexGameRowPitch   # 0.8667

# Offset deltas (dc,dr) per port N,NE,SE,S,SW,NW, from Utils.GetAllTilesNeighbours.
$script:HexEvenColDeltas = @( 0,1,   1,1,   1,0,   0,-1,  -1,0,   -1,1 )
$script:HexOddColDeltas  = @( 0,1,   1,0,   1,-1,  0,-1,  -1,-1,  -1,0 )

function Test-HexShiftedNorth([int]$col) { return ($col % 2 -eq 0) }

function Get-HexNeighbor([int]$col, [int]$row, [int]$port) {
    $d = if (Test-HexShiftedNorth $col) { $script:HexEvenColDeltas } else { $script:HexOddColDeltas }
    return @(($col + $d[$port * 2]), ($row + $d[$port * 2 + 1]))
}

function Get-HexOppositePort([int]$port) { return ($port + 3) % 6 }

# Even-q offset -> axial (q, r).  r = row - (col + (col & 1)) // 2   (floor division, as Python)
function ConvertTo-HexAxial([int]$col, [int]$row) {
    return @($col, ($row - [int][Math]::Floor(($col + ($col -band 1)) / 2.0)))
}
function ConvertFrom-HexAxial([int]$q, [int]$r) {
    return @($q, ($r + [int][Math]::Floor(($q + ($q -band 1)) / 2.0)))
}

function Get-HexDistance([int]$c1, [int]$r1, [int]$c2, [int]$r2) {
    $a = ConvertTo-HexAxial $c1 $r1; $b = ConvertTo-HexAxial $c2 $r2
    $dq = $a[0] - $b[0]; $dr = $a[1] - $b[1]
    return [Math]::Max([Math]::Max([Math]::Abs($dq), [Math]::Abs($dr)), [Math]::Abs($dq + $dr))
}

# Exact MapGO world position.
function Get-HexGamePosition([int]$col, [int]$row) {
    $y = $row * $script:HexGameRowPitch
    $y += if (Test-HexShiftedNorth $col) { $script:HexGameEvenShift } else { 0.0 }
    return @(($col * $script:HexGameColPitch), $y)
}

# Centre (x east, y north) scaled so the N-S neighbour spacing equals $spacing (hex_utils.hex_center).
function Get-HexCenter([int]$col, [int]$row, [double]$spacing = 1.0) {
    $g = Get-HexGamePosition $col $row
    $k = $spacing / $script:HexGameRowPitch
    return @(($g[0] * $k), ($g[1] * $k))
}

# Nearest tile centre to (x, y) (hex_utils.point_to_offset; same candidate order and tie rule).
function Get-HexFromXY([double]$x, [double]$y, [double]$spacing = 1.0) {
    $c0 = [int][Math]::Round($x / ($spacing * $script:HexColPitchRatio))   # ToEven, like Python round()
    $best = $null; $bc = 0; $br = 0
    foreach ($c in @(($c0 - 1), $c0, ($c0 + 1))) {
        $shift = if (Test-HexShiftedNorth $c) { 0.5 } else { 0.0 }
        $r0 = [int][Math]::Round($y / $spacing - $shift)
        foreach ($r in @(($r0 - 1), $r0, ($r0 + 1))) {
            $cc = Get-HexCenter $c $r $spacing
            $d = ($cc[0] - $x) * ($cc[0] - $x) + ($cc[1] - $y) * ($cc[1] - $y)
            if ($null -eq $best -or $d -lt $best) { $best = $d; $bc = $c; $br = $r }
        }
    }
    return @($bc, $br)
}

# Chain of adjacent hexes from a to b inclusive (hex_utils.hex_line).
function Get-HexLine([int]$c1, [int]$r1, [int]$c2, [int]$r2) {
    $n = Get-HexDistance $c1 $r1 $c2 $r2
    $a = Get-HexCenter $c1 $r1; $b = Get-HexCenter $c2 $r2
    $out = New-Object System.Collections.Generic.List[int[]]
    for ($i = 0; $i -le $n; $i++) {
        $t = if ($n -eq 0) { 0.0 } else { $i / [double]$n }
        $x = $a[0] + ($b[0] - $a[0]) * $t + 1e-6
        $y = $a[1] + ($b[1] - $a[1]) * $t + 2e-6
        $out.Add([int[]](Get-HexFromXY $x $y)) | Out-Null
    }
    return ,$out
}
