param(
    [Parameter(Mandatory = $false)]
    [string]$OidcEvidencePath,
    [Parameter(Mandatory = $false)]
    [string]$SpireEvidencePath,
    [Parameter(Mandatory = $false)]
    [string]$ApiCoverageEvidencePath
)

$ErrorActionPreference = "Stop"

python -m ruff format --check .
python -m ruff check .
python -m mypy src
python -m compileall -q src scripts tests
python -m pytest
python scripts/verify_phase5_catalog.py

git diff --check

$missing = @()
foreach ($entry in @(
    @{ Name = "OIDC staging"; Path = $OidcEvidencePath },
    @{ Name = "SPIRE staging"; Path = $SpireEvidencePath },
    @{ Name = "state-changing API coverage"; Path = $ApiCoverageEvidencePath }
)) {
    if ([string]::IsNullOrWhiteSpace($entry.Path) -or -not (Test-Path -LiteralPath $entry.Path)) {
        $missing += $entry.Name
    }
}

if ($missing.Count -gt 0) {
    Write-Error ("Phase 08 remains ACTIVE / NO-GO. Missing live evidence: " + ($missing -join ", "))
}

Write-Output "Phase 08 automated checks and live evidence-path checks succeeded. Independent review is still required before moving the plan to completed."
