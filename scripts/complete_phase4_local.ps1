[CmdletBinding(DefaultParameterSetName = "ExistingImage")]
param(
    [Parameter(Mandatory = $true, ParameterSetName = "ExistingImage")]
    [string]$RunnerImageRef,

    [Parameter(Mandatory = $true, ParameterSetName = "BuildImage")]
    [string]$BaseImage,

    [switch]$Finalize,
    [switch]$CommitAndPush
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $HOME ".venvs\cyber-eval-phase4"

function Assert-Success([string]$Message) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Message (exit code $LASTEXITCODE)"
    }
}

function Assert-DigestReference([string]$Reference, [string]$Label) {
    if ($Reference -notmatch '^(?:[a-z0-9][a-z0-9._/-]*@)?sha256:[0-9a-f]{64}$') {
        throw "$Label must be a digest-pinned sha256 reference."
    }
}

Set-Location $repo
if (-not (Test-Path $venv)) {
    py -3 -m venv $venv
    Assert-Success "Virtual environment creation failed"
}

$python = Join-Path $venv "Scripts\python.exe"
& $python -m pip install --disable-pip-version-check -e ".[dev]"
Assert-Success "Development dependency installation failed"

# Apply deterministic formatter and safe import/lint fixes, then enforce clean quality gates.
& $python -m ruff format .
Assert-Success "Ruff formatting failed"
& $python -m ruff check . --fix
Assert-Success "Ruff automatic lint fixes failed"
& $python -m ruff format .
Assert-Success "Ruff formatting after lint fixes failed"
& $python -m ruff format --check .
Assert-Success "Ruff format check failed"
& $python -m ruff check .
Assert-Success "Ruff lint failed"
& $python -m mypy src
Assert-Success "mypy failed"
& $python -m pytest -o addopts=""
Assert-Success "pytest failed"
& $python -m compileall -q src scripts tests
Assert-Success "Python bytecode compilation failed"

$rootless = podman info --format "{{.Host.Security.Rootless}}"
Assert-Success "Podman preflight failed"
if ($rootless.Trim().ToLowerInvariant() -ne "true") {
    throw "Podman is not operating in rootless mode."
}

if ($PSCmdlet.ParameterSetName -eq "BuildImage") {
    Assert-DigestReference $BaseImage "BaseImage"
    $buildOutput = & "$repo\scripts\build_phase4_runner_image.ps1" -BaseImage $BaseImage
    Assert-Success "Offline Runner image build failed"
    $RunnerImageRef = ($buildOutput | Select-Object -Last 1).ToString().Trim()
}

Assert-DigestReference $RunnerImageRef "RunnerImageRef"
podman image exists $RunnerImageRef
Assert-Success "The digest-pinned Runner image is not present locally"

& $python scripts/live_runner_smoke.py --image-ref $RunnerImageRef
Assert-Success "Live isolated Runner smoke test failed"

if ($Finalize) {
    & $python scripts/finalize_phase4.py --runner-image-ref $RunnerImageRef
    Assert-Success "Phase 4 completion-record update failed"

    & $python -m ruff format .
    Assert-Success "Post-finalization Ruff formatting failed"
    & $python -m ruff check . --fix
    Assert-Success "Post-finalization Ruff lint fixes failed"
    & $python -m ruff format --check .
    Assert-Success "Post-finalization Ruff format check failed"
    & $python -m ruff check .
    Assert-Success "Post-finalization Ruff lint failed"
    & $python -m mypy src
    Assert-Success "Post-finalization mypy failed"
    & $python -m pytest -o addopts=""
    Assert-Success "Post-finalization pytest failed"
}

git diff --check
Assert-Success "Git whitespace validation failed"

if ($CommitAndPush) {
    if (-not $Finalize) {
        throw "CommitAndPush requires Finalize so the live gate is recorded before publication."
    }
    git add -A
    Assert-Success "git add failed"
    git diff --cached --check
    Assert-Success "Staged Git whitespace validation failed"
    git diff --cached --quiet
    if ($LASTEXITCODE -eq 1) {
        git commit -m "Complete phase 04 isolated runner MVP"
        Assert-Success "Phase 4 commit failed"
    } elseif ($LASTEXITCODE -ne 0) {
        throw "Could not inspect staged changes."
    }
    git push origin main
    Assert-Success "Phase 4 push failed"
}

Write-Host "Phase 4 local quality and live isolation gates passed."
Write-Host "Runner image reference: $RunnerImageRef"
Write-Output $RunnerImageRef
