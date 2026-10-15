# Map Reader/Writer Tool for Hex of Steel
# Loads game assemblies and can deserialize/serialize .sav map files

param(
    [string]$Action = "info",
    [string]$MapFile,
    [string]$OutputFile
)

$gameDir = "C:\Program Files (x86)\Steam\steamapps\common\Hex of Steel"
$managedDir = "$gameDir\Hex of Steel_Data\Managed"

# Load required game assemblies
$assembliesToLoad = @(
    "UnityEngine.CoreModule.dll",
    "UnityEngine.dll",
    "Assembly-CSharp.dll"
)

foreach ($asm in $assembliesToLoad) {
    $path = Join-Path $managedDir $asm
    if (Test-Path $path) {
        try {
            [System.Reflection.Assembly]::LoadFrom($path) | Out-Null
        } catch {
            Write-Warning "Could not load $asm : $_"
        }
    }
}

function Decompress-SaveFile {
    param([string]$FilePath)
    $bytes = [System.IO.File]::ReadAllBytes($FilePath)
    $ms = New-Object System.IO.MemoryStream(,$bytes)
    $ds = New-Object System.IO.Compression.DeflateStream($ms, [System.IO.Compression.CompressionMode]::Decompress)
    $outMs = New-Object System.IO.MemoryStream
    $ds.CopyTo($outMs)
    $ds.Close()
    $ms.Close()
    return $outMs.ToArray()
}

function Compress-SaveData {
    param([byte[]]$Data)
    $outMs = New-Object System.IO.MemoryStream
    $ds = New-Object System.IO.Compression.DeflateStream($outMs, [System.IO.Compression.CompressionLevel]::Optimal)
    $ds.Write($Data, 0, $Data.Length)
    $ds.Close()
    return $outMs.ToArray()
}

function Deserialize-GameData {
    param([byte[]]$Data)
    $ms = New-Object System.IO.MemoryStream(,$Data)
    $formatter = New-Object System.Runtime.Serialization.Formatters.Binary.BinaryFormatter
    try {
        $obj = $formatter.Deserialize($ms)
        return $obj
    } catch {
        Write-Error "Deserialization failed: $_"
        return $null
    } finally {
        $ms.Close()
    }
}

function Serialize-GameData {
    param($GameData)
    $ms = New-Object System.IO.MemoryStream
    $formatter = New-Object System.Runtime.Serialization.Formatters.Binary.BinaryFormatter
    $formatter.Serialize($ms, $GameData)
    return $ms.ToArray()
}

function Get-MapInfo {
    param($GameData)
    $map = $GameData.map
    $info = @{
        SizeX = $map.SizeX
        SizeY = $map.SizeY
        ScenarioName = $map.ScenarioName
        FileName = $map.FileName
        Date = $map.Date
        TurnCount = $map.turnCount
        DaysPerTurn = $map.NumberOfDaysThatGoesByPerTurn
        IsCampaign = $map.IsCampaign
        IsWinter = $map.IsWinter
        CircularMap = $map.CircularMap
        NumberOfTurnsToWin = $map.NumberOfTurnsToWin
    }

    $tiles = $map.TilesTable
    $tileTypes = @{}
    for ($x = 0; $x -lt $map.SizeX; $x++) {
        for ($y = 0; $y -lt $map.SizeY; $y++) {
            $tile = $tiles[$x, $y]
            if ($tile) {
                $name = $tile.Name
                if ($tileTypes.ContainsKey($name)) {
                    $tileTypes[$name]++
                } else {
                    $tileTypes[$name] = 1
                }
            }
        }
    }
    $info.TileTypeCounts = $tileTypes
    $info.TotalTiles = $map.SizeX * $map.SizeY

    return $info
}

# Main execution
if (-not $MapFile) {
    Write-Output "Usage: .\map_reader.ps1 -Action <info|dump|test> -MapFile <path.sav>"
    Write-Output ""
    Write-Output "Actions:"
    Write-Output "  info  - Display map dimensions, scenario info, and tile type counts"
    Write-Output "  dump  - Dump full tile grid to CSV"
    Write-Output "  test  - Create a small test map to verify serialization works"
    exit
}

Write-Output "Loading assemblies..."

switch ($Action) {
    "info" {
        Write-Output "Decompressing $MapFile ..."
        $data = Decompress-SaveFile -FilePath $MapFile
        Write-Output "Decompressed: $($data.Length) bytes"

        Write-Output "Deserializing..."
        $gameData = Deserialize-GameData -Data $data

        if ($gameData) {
            $info = Get-MapInfo -GameData $gameData
            Write-Output ""
            Write-Output "=== MAP INFO ==="
            Write-Output "Scenario: $($info.ScenarioName)"
            Write-Output "Dimensions: $($info.SizeX) x $($info.SizeY) ($($info.TotalTiles) hexes)"
            Write-Output "Date: $($info.Date)"
            Write-Output "Days per turn: $($info.DaysPerTurn)"
            Write-Output "Max turns: $($info.NumberOfTurnsToWin)"
            Write-Output "Campaign: $($info.IsCampaign)"
            Write-Output ""
            Write-Output "=== TILE TYPES ==="
            $info.TileTypeCounts.GetEnumerator() | Sort-Object Value -Descending | Format-Table Name, Value -AutoSize
        }
    }

    "test" {
        Write-Output "Creating test map..."
        # This will test if we can create a new map from scratch
        # First deserialize an existing map to get a template
        $data = Decompress-SaveFile -FilePath $MapFile
        $gameData = Deserialize-GameData -Data $data

        if ($gameData) {
            # Re-serialize and compress
            Write-Output "Re-serializing..."
            $serialized = Serialize-GameData -GameData $gameData
            Write-Output "Serialized: $($serialized.Length) bytes"

            $compressed = Compress-SaveData -Data $serialized
            Write-Output "Compressed: $($compressed.Length) bytes"

            if ($OutputFile) {
                [System.IO.File]::WriteAllBytes($OutputFile, $compressed)
                Write-Output "Saved to: $OutputFile"
            }
            Write-Output "Round-trip test complete!"
        }
    }
}
