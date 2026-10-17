# First Kernstown 1862 - one-click installer for Hex of Steel (Windows PowerShell 5.1+)
# Usage (paste into Windows PowerShell):
#   irm https://raw.githubusercontent.com/garrettmbf-sudo/CivilWar1/kernstown-map/install.ps1 | iex
# Optional environment overrides (set before running): KERNSTOWN_GAMEDIR, KERNSTOWN_MODSDIR, KERNSTOWN_DRYRUN=1

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'   # IWR progress bar is extremely slow in PS 5.1

function Wait-Key { if ($Host.Name -eq 'ConsoleHost' -and -not $env:KERNSTOWN_NOPAUSE) { Write-Host ''; Read-Host 'Press Enter to close' | Out-Null } }
function Say([string]$m, [string]$c = 'Gray') { Write-Host $m -ForegroundColor $c }

function Install-Kernstown {
    $Repo    = 'garrettmbf-sudo/CivilWar1'
    $Branch  = 'kernstown-map'
    $Tag     = 'kernstown-v0.4.2'
    $NTiles  = 3348      # 62 x 54 game-native hexes (v0.4.2)
    $ModName = 'First Kernstown 1862'
    $NeedGB  = 14
    $DryRun  = ($env:KERNSTOWN_DRYRUN -eq '1')

    try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch {}
    Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem

    Say "=== First Kernstown 1862 installer ===" Cyan

    # ---- 1. Release assets ----
    Say "Looking up the download files on GitHub..."
    $rel = Invoke-RestMethod -UseBasicParsing -Uri "https://api.github.com/repos/$Repo/releases/tags/$Tag" -Headers @{ 'User-Agent' = 'Kernstown-installer' }
    $assets = @($rel.assets | Where-Object { $_.name -like 'Kernstown_*.zip' } | Sort-Object name)
    if (-not ($assets | Where-Object { $_.name -eq 'Kernstown_mod_base.zip' })) { throw "Kernstown_mod_base.zip missing from release $Tag" }
    if (@($assets | Where-Object { $_.name -like 'Kernstown_tiles_part*of4*.zip' }).Count -ne 4) { throw "Expected 4 tile parts in release $Tag" }
    $total = 0; foreach ($a in $assets) { $total += [int64]$a.size }
    foreach ($a in $assets) { Say ("  {0}  ({1:N0} MB)" -f $a.name, ($a.size / 1MB)) }

    # ---- 2. Folders ----
    $Temp = Join-Path $env:TEMP 'Kernstown1862_install'
    $modsCandidates = @()
    if ($env:KERNSTOWN_MODSDIR) { $modsCandidates += $env:KERNSTOWN_MODSDIR }
    $ll = Join-Path $env:USERPROFILE 'AppData\LocalLow'
    $modsCandidates += (Join-Path $ll "Valentin's studios\Hex of Steel\MODS")
    $modsCandidates += (Join-Path $ll "War Frogs Studio\Hex of Steel\MODS")
    $ModsDir = $null
    foreach ($c in $modsCandidates) { if (Test-Path -LiteralPath $c) { $ModsDir = $c; break } }
    if (-not $ModsDir) {
        foreach ($c in $modsCandidates) { $p = Split-Path $c -Parent; if (Test-Path -LiteralPath $p) { $ModsDir = $c; break } }
    }
    if (-not $ModsDir) {
        $ModsDir = Join-Path $ll "Valentin's studios\Hex of Steel\MODS"
        Say "WARNING: Hex of Steel's MODS folder was not found. Creating it at:" Yellow
        Say "  $ModsDir" Yellow
        Say "  (Start Hex of Steel once before installing if the mod does not show up.)" Yellow
    }
    $ModDir = Join-Path $ModsDir $ModName
    Say "Mod will be installed to: $ModDir"

    # Game folder (needed by the map builder)
    $gameCandidates = @()
    if ($env:KERNSTOWN_GAMEDIR) { $gameCandidates += $env:KERNSTOWN_GAMEDIR }
    $steamRoots = @()
    foreach ($k in 'HKCU:\Software\Valve\Steam', 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam', 'HKLM:\SOFTWARE\Valve\Steam') {
        try { $v = Get-ItemProperty -Path $k -ErrorAction Stop; if ($v.SteamPath) { $steamRoots += $v.SteamPath }; if ($v.InstallPath) { $steamRoots += $v.InstallPath } } catch {}
    }
    $steamRoots += "${env:ProgramFiles(x86)}\Steam"
    $libs = @()
    foreach ($s in $steamRoots) {
        $s = $s -replace '/', '\'
        $libs += $s
        $vdf = Join-Path $s 'steamapps\libraryfolders.vdf'
        if (Test-Path -LiteralPath $vdf) {
            foreach ($m in [regex]::Matches((Get-Content -Raw -LiteralPath $vdf), '"path"\s+"([^"]+)"')) { $libs += ($m.Groups[1].Value -replace '\\\\', '\') }
        }
    }
    foreach ($l in ($libs | Select-Object -Unique)) { $gameCandidates += (Join-Path $l 'steamapps\common\Hex of Steel') }
    $GameDir = $null
    foreach ($g in $gameCandidates) { if (Test-Path -LiteralPath (Join-Path $g 'Hex of Steel_Data\Managed')) { $GameDir = $g; break } }
    if ($GameDir) { Say "Hex of Steel found: $GameDir" } else { Say "WARNING: Hex of Steel game folder not found - the scenario file cannot be built automatically." Yellow }

    if ($DryRun) { Say "DRY RUN: stopping before downloads." Yellow; return }

    # ---- 3. Disk space ----
    New-Item -ItemType Directory -Force -Path $Temp | Out-Null
    $have = 0; foreach ($a in $assets) { $f = Join-Path $Temp $a.name; if (Test-Path -LiteralPath $f) { $have += (Get-Item -LiteralPath $f).Length } }
    $needBytes = [math]::Max(0, ($total - $have)) + $total + 1GB
    foreach ($root in @(([IO.Path]::GetPathRoot($Temp)), ([IO.Path]::GetPathRoot($ModsDir))) | Select-Object -Unique) {
        $free = (New-Object IO.DriveInfo($root)).AvailableFreeSpace
        $req = if (([IO.Path]::GetPathRoot($Temp)) -eq ([IO.Path]::GetPathRoot($ModsDir))) { $needBytes } else { $total + 1GB }
        if ($free -lt $req) { throw ("Not enough free space on {0}: {1:N1} GB free, about {2:N1} GB needed (~{3} GB in total)." -f $root, ($free / 1GB), ($req / 1GB), $NeedGB) }
        Say ("Free space on {0}: {1:N1} GB - OK" -f $root, ($free / 1GB))
    }

    # ---- 4. Download (resume / skip) ----
    $i = 0
    foreach ($a in $assets) {
        $i++
        $dest = Join-Path $Temp $a.name
        $size = [int64]$a.size
        if ((Test-Path -LiteralPath $dest) -and (Get-Item -LiteralPath $dest).Length -eq $size) { Say "[$i/$($assets.Count)] $($a.name) already downloaded - skipping" Green; continue }
        if ((Test-Path -LiteralPath $dest) -and (Get-Item -LiteralPath $dest).Length -gt $size) { Remove-Item -LiteralPath $dest -Force }
        Say ("[{0}/{1}] Downloading {2} ({3:N0} MB) - this can take a while..." -f $i, $assets.Count, $a.name, ($size / 1MB)) Cyan
        $ok = $false
        if ($size -gt 10MB -and (Get-Command Start-BitsTransfer -ErrorAction SilentlyContinue) -and -not (Test-Path -LiteralPath $dest)) {
            try {
                $ProgressPreference = 'Continue'
                Start-BitsTransfer -Source $a.browser_download_url -Destination $dest -DisplayName $a.name -Description 'First Kernstown 1862' -ErrorAction Stop
                $ok = $true
            } catch { Say "  BITS download failed ($($_.Exception.Message)); trying direct download with resume..." Yellow }
            finally { $ProgressPreference = 'SilentlyContinue' }
        }
        if (-not $ok) { Get-WithResume $a.browser_download_url $dest $size }
        $len = (Get-Item -LiteralPath $dest).Length
        if ($len -ne $size) { throw "Download of $($a.name) is incomplete ($len of $size bytes). Run the installer again to resume." }
    }

    # ---- 5. Extract (strip leading 'mod/' so files land in MODS\First Kernstown 1862) ----
    New-Item -ItemType Directory -Force -Path $ModDir | Out-Null
    # v0.4.2 re-indexed the grid to the game's convention: tiles from an older install would sit in the wrong hexes
    $oldTiles = Join-Path $ModDir 'Graphics\Tiles\Summer'
    if (Test-Path -LiteralPath $oldTiles) {
        $stale = @(Get-ChildItem -LiteralPath $oldTiles -Filter 'SV_K_*.png' -ErrorAction SilentlyContinue)
        if ($stale.Count) { Say "Removing $($stale.Count) tiles from a previous version..." Yellow; $stale | Remove-Item -Force }
    }
    $modFull = [IO.Path]::GetFullPath($ModDir).TrimEnd('\') + '\'
    foreach ($a in $assets) {
        Say "Extracting $($a.name)..." Cyan
        $zip = [IO.Compression.ZipFile]::OpenRead((Join-Path $Temp $a.name))
        try {
            $n = 0
            foreach ($e in $zip.Entries) {
                $rel = $e.FullName -replace '\\', '/'
                if ($rel -like 'mod/*') { $rel = $rel.Substring(4) }
                if ([string]::IsNullOrEmpty($rel)) { continue }
                $target = [IO.Path]::GetFullPath((Join-Path $ModDir ($rel -replace '/', '\')))
                if (-not $target.StartsWith($modFull, [StringComparison]::OrdinalIgnoreCase)) { continue }  # zip-slip guard
                if ($rel.EndsWith('/')) { New-Item -ItemType Directory -Force -Path $target | Out-Null; continue }
                $dir = Split-Path $target -Parent
                if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
                [IO.Compression.ZipFileExtensions]::ExtractToFile($e, $target, $true)
                $n++
                if ($n % 200 -eq 0) { Write-Host "  $n files..." }
            }
            Say "  $n files extracted"
        } finally { $zip.Dispose() }
    }
    $tiles = @(Get-ChildItem -LiteralPath (Join-Path $ModDir 'Graphics\Tiles\Summer') -Filter 'SV_K_*.png' -ErrorAction SilentlyContinue).Count
    Say "Tiles installed: $tiles (expected $NTiles)" $(if ($tiles -ge $NTiles) { 'Green' } else { 'Yellow' })

    # ---- 6. Build the scenario (.sav) ----
    $built = $false
    if ($GameDir) {
        Say "Downloading the map builder and data..." Cyan
        $src = Join-Path $Temp 'src'
        $raw = "https://raw.githubusercontent.com/$Repo/$Tag"     # builder + data pinned to the release (was: branch head)
        foreach ($p in 'tools/build_kernstown_map.ps1', 'data/layers/kernstown_game.json', 'data/layers/kernstown_units.json', 'templates/ACW_sample_102x60.sav') {
            $d = Join-Path $src ($p -replace '/', '\')
            New-Item -ItemType Directory -Force -Path (Split-Path $d -Parent) | Out-Null
            Invoke-WebRequest -UseBasicParsing -Uri "$raw/$p" -OutFile $d
        }
        $mapsDir = Join-Path $ModDir 'Maps'
        New-Item -ItemType Directory -Force -Path $mapsDir | Out-Null
        $out = Join-Path $mapsDir "$ModName.sav"
        Say "Building the scenario file (Hex of Steel must be closed)..." Cyan
        $psExe = Join-Path $PSHOME 'powershell.exe'; if (-not (Test-Path $psExe)) { $psExe = 'powershell.exe' }
        & $psExe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $src 'tools\build_kernstown_map.ps1') -GameDir $GameDir -OutputFile $out
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $out)) { Say "WARNING: the map builder reported a problem (see messages above)." Yellow } else { $built = $true; Say "Scenario written: $out" Green }
    }

    # ---- 7. Clean up ----
    if ($built -and $tiles -ge $NTiles) { Remove-Item -LiteralPath $Temp -Recurse -Force -ErrorAction SilentlyContinue; Say "Temporary files removed." }
    else { Say "Downloads kept in $Temp so you can re-run the installer without downloading again." Yellow }

    Say ""
    Say "=== Done! ===" Green
    if (-not $built -and (Test-Path -LiteralPath (Join-Path $ModDir "Maps\$ModName.sav"))) {
        Say "Using the pre-built scenario from the release (built against Hex of Steel 8.4.14). If it does not load, set KERNSTOWN_GAMEDIR and re-run to build it locally." Yellow
    } elseif (-not $built) {
        Say "The scenario file was NOT built. Find your Hex of Steel folder (Steam > right-click Hex of Steel > Manage > Browse local files)," Yellow
        Say "then run in PowerShell:  `$env:KERNSTOWN_GAMEDIR='<that folder>'  and paste the install line again." Yellow
    }
    Say "Next steps:"
    Say "  1. Start Hex of Steel > MODS > tick 'Shenandoah Valley 1862 - First Kernstown' > Apply changes (the game may restart)."
    Say "  2. Play > Custom scenario (or Map editor) > choose 'First Kernstown 1862'."
}

function Get-WithResume([string]$Url, [string]$Dest, [int64]$Size) {
    for ($try = 1; $try -le 5; $try++) {
        $start = if (Test-Path -LiteralPath $Dest) { (Get-Item -LiteralPath $Dest).Length } else { 0 }
        if ($start -ge $Size) { return }
        try {
            $req = [Net.HttpWebRequest]::Create($Url)
            $req.UserAgent = 'Kernstown-installer'; $req.AllowAutoRedirect = $true; $req.Timeout = 60000; $req.ReadWriteTimeout = 120000
            if ($start -gt 0) { $req.AddRange([int64]$start) }
            $resp = $req.GetResponse()
            if ($start -gt 0 -and [int]$resp.StatusCode -ne 206) { $start = 0 }   # server ignored range: restart
            $in = $resp.GetResponseStream()
            $mode = if ($start -gt 0) { [IO.FileMode]::Append } else { [IO.FileMode]::Create }
            $fs = New-Object IO.FileStream($Dest, $mode, [IO.FileAccess]::Write)
            try {
                $buf = New-Object byte[] (1MB); $done = $start; $last = [DateTime]::Now
                while (($r = $in.Read($buf, 0, $buf.Length)) -gt 0) {
                    $fs.Write($buf, 0, $r); $done += $r
                    if (([DateTime]::Now - $last).TotalSeconds -ge 3) { Write-Host ("  {0:N0} / {1:N0} MB ({2:N0}%)" -f ($done / 1MB), ($Size / 1MB), (100 * $done / $Size)); $last = [DateTime]::Now }
                }
            } finally { $fs.Close(); $in.Close(); $resp.Close() }
            if ((Get-Item -LiteralPath $Dest).Length -ge $Size) { return }
        } catch { Say "  Connection problem (attempt $try of 5): $($_.Exception.Message)" Yellow; Start-Sleep -Seconds (5 * $try) }
    }
}

try {
    Install-Kernstown
} catch {
    Write-Host ''
    Write-Host 'Sorry - the installation did not finish.' -ForegroundColor Red
    Write-Host ("Reason: " + $_.Exception.Message) -ForegroundColor Red
    Write-Host 'You can simply run the same install line again; finished downloads are kept and reused.' -ForegroundColor Yellow
    Write-Host 'If it keeps failing, follow the manual steps in README_INSTALL.md.' -ForegroundColor Yellow
}
Wait-Key
