<#
  EnvKit installer (Windows) — https://github.com/Env-Kit/envkit-releases

  EnvKit is a desktop app (Electron). This downloads the latest signed installer
  (EnvKit-Setup-<ver>.exe), removes the Mark-of-the-Web, and runs it elevated
  (perMachine install needs admin via UAC).

  Usage:
    Install / update:
      irm https://raw.githubusercontent.com/Env-Kit/envkit-releases/main/install.ps1 | iex

    Uninstall (pass args by recreating the script block):
      & ([scriptblock]::Create((irm https://raw.githubusercontent.com/Env-Kit/envkit-releases/main/install.ps1))) -Uninstall

  Publish: this file lives in the PUBLIC Env-Kit/envkit-releases repo so the raw
  URL above resolves. The private source copy is envkit/install.ps1.
#>
[CmdletBinding()]
param(
    [switch]$Uninstall,
    [switch]$Silent = $true,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'
$Repo = if ($env:ENVKIT_REPO) { $env:ENVKIT_REPO } else { 'Env-Kit/envkit-releases' }

# ── Output helpers ───────────────────────────────────────────────────────────
function Write-Info    { param($m) Write-Host "  --> $m" -ForegroundColor Cyan }
function Write-Ok      { param($m) Write-Host "  [OK] $m" -ForegroundColor Green }
function Write-Warn    { param($m) Write-Host "  [!]  $m" -ForegroundColor Yellow }
function Write-ErrLine { param($m) Write-Host "  [x]  $m" -ForegroundColor Red }
function Write-Header  { param($m) Write-Host "`n$m" -ForegroundColor White }
function Die           { param($m) Write-ErrLine $m; exit 1 }

# ── Latest version via the releases/latest redirect (no API key, not rate-limited) ──
function Get-LatestVersion {
    $url = "https://github.com/$Repo/releases/latest"
    try {
        $resp = Invoke-WebRequest -Uri $url -MaximumRedirection 0 -UseBasicParsing `
            -Headers @{ 'User-Agent' = 'envkit-installer' } -ErrorAction SilentlyContinue
        $loc = $resp.Headers.Location
    } catch {
        # PS 5.1 throws on a 3xx with MaximumRedirection 0 — pull Location from the exception.
        $loc = $_.Exception.Response.Headers.Location.ToString()
    }
    if (-not $loc) { return '' }
    if ($loc -match '/releases/tag/v?([^/\s]+)') { return $Matches[1].Trim() }
    return ''
}

# ── Installed version from the Uninstall registry (DisplayName "EnvKit") ──────
function Get-InstalledVersion {
    $roots = @(
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*'
    )
    foreach ($r in $roots) {
        $e = Get-ItemProperty $r -ErrorAction SilentlyContinue |
            Where-Object { $_.DisplayName -like 'EnvKit*' } | Select-Object -First 1
        if ($e -and $e.DisplayVersion) { return [string]$e.DisplayVersion }
    }
    return ''
}

# ── Install / update ─────────────────────────────────────────────────────────
function Invoke-Install {
    Write-Header 'Installing EnvKit'

    if ([System.Environment]::OSVersion.Platform -ne 'Win32NT') {
        Die "This installer is for Windows. On macOS, run the install.sh one-liner instead."
    }

    $version = Get-LatestVersion
    if (-not $version) { Die "Could not resolve the latest release at https://github.com/$Repo/releases/latest" }

    $current = Get-InstalledVersion
    if ($current -and $current -eq $version) {
        Write-Ok "EnvKit v$version is already installed and up to date."
        return
    }
    if ($current) { Write-Info "Updating EnvKit v$current -> v$version" }

    $asset = "EnvKit-Setup-$version.exe"
    $url = "https://github.com/$Repo/releases/download/v$version/$asset"
    $dest = Join-Path ([System.IO.Path]::GetTempPath()) $asset

    Write-Info "Downloading $asset ..."
    try {
        # curl.exe (bundled on Win10+) gives a progress bar; fall back to Invoke-WebRequest.
        if (Get-Command curl.exe -ErrorAction SilentlyContinue) {
            & curl.exe -fSL --retry 3 --retry-all-errors -o $dest $url
            if ($LASTEXITCODE -ne 0) { throw "curl exited $LASTEXITCODE" }
        } else {
            $ProgressPreference = 'SilentlyContinue'
            Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
        }
    } catch {
        Die "Download failed: $url`n  $($_.Exception.Message)"
    }
    if (-not (Test-Path $dest) -or (Get-Item $dest).Length -lt 1MB) {
        Die "Downloaded installer looks incomplete: $dest"
    }

    # Strip the Mark-of-the-Web so SmartScreen doesn't block the elevated launch.
    try { Unblock-File -Path $dest -ErrorAction SilentlyContinue } catch {}

    Write-Info "Running the installer (a UAC prompt will appear) ..."
    # perMachine install needs elevation; -Verb RunAs triggers UAC. /S = silent NSIS.
    $args = if ($Silent) { '/S' } else { '' }
    $proc = Start-Process -FilePath $dest -ArgumentList $args -Verb RunAs -PassThru -Wait
    if ($proc.ExitCode -ne 0) {
        Die "Installer exited with code $($proc.ExitCode)."
    }

    Remove-Item $dest -ErrorAction SilentlyContinue
    Write-Ok "Installed EnvKit v$version"
    Write-Host "  *  A GitHub star helps others find EnvKit: https://github.com/$Repo" -ForegroundColor Cyan
}

# ── Uninstall ────────────────────────────────────────────────────────────────
function Invoke-Uninstall {
    Write-Header 'Uninstalling EnvKit'
    Get-Process EnvKit -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

    # Find the NSIS uninstaller from the Uninstall registry.
    $uninstaller = $null
    foreach ($r in @(
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*'
    )) {
        $e = Get-ItemProperty $r -ErrorAction SilentlyContinue |
            Where-Object { $_.DisplayName -like 'EnvKit*' } | Select-Object -First 1
        if ($e) {
            $uninstaller = $e.QuietUninstallString
            if (-not $uninstaller) { $uninstaller = $e.UninstallString }
            break
        }
    }
    if (-not $uninstaller) { Write-Info 'EnvKit does not appear to be installed.'; return }

    Write-Warn 'Remove EnvKit''s hosts entries / certificates from inside the app (Settings) BEFORE'
    Write-Warn 'uninstalling, or clean them up manually — this script does not touch them.'

    # QuietUninstallString already includes /S; run it elevated.
    Write-Info 'Running the uninstaller (a UAC prompt will appear) ...'
    $exe = if ($uninstaller -match '^"([^"]+)"\s*(.*)$') { $Matches[1] } else { ($uninstaller -split '\s+')[0] }
    $rest = if ($uninstaller -match '^"[^"]+"\s*(.*)$') { $Matches[1] } else { ($uninstaller -split '\s+', 2)[1] }
    if (-not ($rest -match '/S')) { $rest = "/S $rest" }
    Start-Process -FilePath $exe -ArgumentList $rest.Trim() -Verb RunAs -Wait
    Write-Ok 'EnvKit uninstalled.'
}

# ── Entry point ──────────────────────────────────────────────────────────────
Write-Host ''
Write-Host '  EnvKit — local web-dev stack for Windows' -ForegroundColor White
Write-Host "  https://github.com/$Repo`n"

if ($Help) {
    Write-Host 'Usage: install.ps1 [-Uninstall] [-Silent:$false]'
    Write-Host '  (no args)        Install or update EnvKit (latest release)'
    Write-Host '  -Uninstall       Remove EnvKit (keeps your data)'
    Write-Host '  -Silent:$false   Show the installer wizard instead of a silent install'
    return
}

if ($Uninstall) { Invoke-Uninstall } else { Invoke-Install }
