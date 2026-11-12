<#
.SYNOPSIS
    Checks that the tools, configuration, model endpoint and intake folder required by the pipeline are present.
.DESCRIPTION
    Read-only. A passing result shows that the environment is complete. It does not run an
    extraction and does not measure extraction accuracy.
#>
[CmdletBinding()]
param([Parameter(Mandatory = $true)][string]$EngineRoot)
$ErrorActionPreference = 'Stop'

foreach ($name in @('python.exe', 'pdfinfo.exe', 'pdftotext.exe', 'pdftoppm.exe')) {
    Get-Command $name -ErrorAction Stop | Select-Object Name, Source
}
python --version
if ($LASTEXITCODE -ne 0) { throw 'Python version query failed.' }

$config = Get-Content -LiteralPath (Join-Path $EngineRoot 'config\engine_config.json') -Raw | ConvertFrom-Json
$models = Invoke-RestMethod -Method Get -Uri ($config.lm_studio_base_url.TrimEnd('/') + '/models') -TimeoutSec 30
$models.data | Select-Object id, object, owned_by
if ($config.model -notin @($models.data.id)) { throw 'The configured model is not visible through the API.' }

$supervisor = Get-Content -LiteralPath (Join-Path $EngineRoot 'config\supervisor_config.json') -Raw | ConvertFrom-Json
$incoming = if ($supervisor.intake_directory) { $supervisor.intake_directory }
            else { Join-Path $env:OneDriveCommercial 'InvoiceIntake\Incoming' }
if (-not (Test-Path -LiteralPath $incoming -PathType Container)) { throw "Missing intake folder: $incoming" }
Write-Host 'Environment checks passed. This result does not measure extraction accuracy.'
