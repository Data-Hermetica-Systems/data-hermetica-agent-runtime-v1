[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$EngineRoot)
$ErrorActionPreference = 'Stop'
$PSVersionTable
foreach ($name in @('python.exe','pdfinfo.exe','pdftotext.exe','pdftoppm.exe')) {
    Get-Command $name -ErrorAction Stop | Select-Object Name, Source
}
python --version
if ($LASTEXITCODE -ne 0) { throw 'Python version query failed.' }
$config = Get-Content -LiteralPath (Join-Path $EngineRoot 'config\engine_config.json') -Raw | ConvertFrom-Json
$config | Format-List *
$models = Invoke-RestMethod -Method Get -Uri ($config.lm_studio_base_url.TrimEnd('/') + '/models') -TimeoutSec 30
$models.data | Select-Object id, object, owned_by
if ($config.model -notin @($models.data.id)) { throw 'Configured model is not visible through API.' }
$incoming = Join-Path $env:OneDriveCommercial 'InvoiceIntake\Incoming'
if (-not (Test-Path -LiteralPath $incoming -PathType Container)) { throw "Missing intake: $incoming" }
Write-Host 'Environment checks passed. This does not prove inference or extraction accuracy.'
