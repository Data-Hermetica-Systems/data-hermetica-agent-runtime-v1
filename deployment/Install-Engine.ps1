[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$EngineRoot)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'Verify-Release.ps1')
$releaseRoot = Split-Path -Parent $PSScriptRoot
if (-not [IO.Path]::IsPathRooted($EngineRoot)) { throw 'EngineRoot must be an absolute local path.' }
if (Test-Path -LiteralPath $EngineRoot) { throw 'Fresh installation only: target already exists. Do not overwrite a live engine with this installer.' }
if ([string]::IsNullOrWhiteSpace($env:OneDriveCommercial)) { throw 'Sign in to work OneDrive and reopen PowerShell.' }
foreach ($program in @('python.exe','pdfinfo.exe','pdftotext.exe','pdftoppm.exe')) { Get-Command $program -ErrorAction Stop | Out-Null }
foreach ($relative in @('app','config','tests','logs','state','backup','quarantine','work\prepared','work\requests','work\responses','work\output_staging')) {
    New-Item -ItemType Directory -Path (Join-Path $EngineRoot $relative) -Force | Out-Null
}
foreach ($folder in @('app','config','tests')) {
    Copy-Item -Path (Join-Path $releaseRoot "$folder\*") -Destination (Join-Path $EngineRoot $folder) -Recurse -Force
}
foreach ($relative in @('InvoiceIntake\Incoming','InvoiceResults\Completed','InvoiceResults\ReviewRequired')) {
    New-Item -ItemType Directory -Path (Join-Path $env:OneDriveCommercial $relative) -Force | Out-Null
}
[Environment]::SetEnvironmentVariable('DATA_HERMETICA_INVOICE_ENGINE_ROOT', $EngineRoot, 'User')
$env:DATA_HERMETICA_INVOICE_ENGINE_ROOT = $EngineRoot
$sourceFiles = Get-ChildItem -LiteralPath (Join-Path $EngineRoot 'app'),(Join-Path $EngineRoot 'config') -File
$sourceFiles | Get-FileHash -Algorithm SHA256 | Export-Csv -LiteralPath (Join-Path $EngineRoot 'logs\installed-file-hashes.csv') -NoTypeInformation
Write-Host "Installed: $EngineRoot. Configure and test before registering the task."
