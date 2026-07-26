[CmdletBinding()]
param(
    [string]$RepoPath = "$HOME\Downloads\cyber-evaluation-platform-design",
    [string]$ZipPath = "$HOME\Downloads\phase6-agent-integration.zip",
    [switch]$RunLiveModel,
    [string]$Model = "gpt-5.6-sol"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-Checked {
    param(
        [Parameter(Mandatory)]
        [scriptblock]$Command,
        [Parameter(Mandatory)]
        [string]$Message
    )
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Message (exit code $LASTEXITCODE)"
    }
}

function Write-Utf8Lf {
    param(
        [Parameter(Mandatory)]
        [string]$Path,
        [Parameter(Mandatory)]
        [string]$Content
    )
    $normalized = $Content.Replace("`r`n", "`n").Replace("`r", "`n")
    [System.IO.File]::WriteAllText(
        [System.IO.Path]::GetFullPath($Path),
        $normalized,
        [System.Text.UTF8Encoding]::new($false)
    )
}

function Ensure-GitIgnoreEntry {
    param(
        [Parameter(Mandatory)]
        [string]$Entry
    )
    $path = Join-Path $RepoPath ".gitignore"
    $content = if (Test-Path $path) {
        [System.IO.File]::ReadAllText($path)
    }
    else {
        ""
    }
    $lines = @(
        $content.Replace("`r`n", "`n").Replace("`r", "`n") -split "`n" |
            ForEach-Object { $_.TrimEnd() } |
            Where-Object { $_ -and $_ -ne $Entry }
    )
    $lines += $Entry
    Write-Utf8Lf -Path $path -Content (($lines -join "`n").TrimEnd() + "`n")
}

function Get-StatusPaths {
    $paths = [System.Collections.Generic.List[string]]::new()
    foreach ($line in @(git status --porcelain=v1)) {
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to inspect repository status."
        }
        if ($line.Length -lt 4) {
            continue
        }
        $value = $line.Substring(3).Replace("\", "/")
        foreach ($part in $value -split " -> ") {
            $paths.Add($part.Trim('"'))
        }
    }
    return $paths
}

function Assert-ResumableStatus {
    param(
        [Parameter(Mandatory)]
        [System.Collections.Generic.HashSet[string]]$AllowedPaths
    )
    $unknown = @(
        Get-StatusPaths |
            Where-Object { -not $AllowedPaths.Contains($_) } |
            Sort-Object -Unique
    )
    if ($unknown.Count -ne 0) {
        throw (
            "The repository contains changes outside the Phase 6 overlay: " +
            ($unknown -join ", ")
        )
    }
}

function Remove-PackageMetadata {
    Remove-Item "src\cyber_eval_skeleton.egg-info" `
        -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Directory -Filter "*.egg-info" |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

$RepoPath = [System.IO.Path]::GetFullPath($RepoPath)
$ZipPath = [System.IO.Path]::GetFullPath($ZipPath)

if (-not (Test-Path (Join-Path $RepoPath ".git"))) {
    throw "RepoPath is not a Git repository: $RepoPath"
}
if (-not (Test-Path $ZipPath)) {
    throw "Phase 6 overlay ZIP was not found: $ZipPath"
}

$temp = Join-Path $env:TEMP "phase6-agent-integration"
Remove-Item $temp -Recurse -Force -ErrorAction SilentlyContinue
Expand-Archive -Path $ZipPath -DestinationPath $temp -Force
$overlay = Join-Path $temp "phase6-agent-integration"
if (-not (Test-Path $overlay)) {
    throw "The Phase 6 overlay root is missing from the ZIP."
}

$allowedPaths = [System.Collections.Generic.HashSet[string]]::new(
    [System.StringComparer]::OrdinalIgnoreCase
)
Get-ChildItem $overlay -Recurse -File | ForEach-Object {
    $relative = [System.IO.Path]::GetRelativePath($overlay, $_.FullName)
    [void]$allowedPaths.Add($relative.Replace("\", "/"))
}
@(
    "docs/exec-plans/completed/README.md",
    "docs/exec-plans/completed/phase-06-agent-integration.md",
    "src/cyber_eval_skeleton.egg-info/PKG-INFO",
    "src/cyber_eval_skeleton.egg-info/SOURCES.txt",
    "src/cyber_eval_skeleton.egg-info/dependency_links.txt",
    "src/cyber_eval_skeleton.egg-info/requires.txt",
    "src/cyber_eval_skeleton.egg-info/top_level.txt"
) | ForEach-Object { [void]$allowedPaths.Add($_) }

Set-Location $RepoPath
$statusPaths = @(Get-StatusPaths)
if ($statusPaths.Count -eq 0) {
    Invoke-Checked -Command { git fetch origin } -Message "Git fetch failed"
    Invoke-Checked -Command { git pull --ff-only origin main } `
        -Message "Fast-forward update failed"
}
else {
    Assert-ResumableStatus -AllowedPaths $allowedPaths
    Write-Host "Resuming a partially applied Phase 6 overlay."
}

Get-ChildItem $overlay -Force | ForEach-Object {
    Copy-Item $_.FullName $RepoPath -Recurse -Force
}

Remove-PackageMetadata
Ensure-GitIgnoreEntry -Entry "*.egg-info/"

$attributesPath = Join-Path $RepoPath ".gitattributes"
$attributes = if (Test-Path $attributesPath) {
    [System.IO.File]::ReadAllText($attributesPath)
}
else {
    ""
}
$rules = @(
    "* text=auto",
    "*.py text eol=lf",
    "*.ps1 text eol=lf",
    "*.md text eol=lf",
    "*.txt text eol=lf",
    "*.json text eol=lf",
    "*.yaml text eol=lf",
    "*.yml text eol=lf",
    "*.toml text eol=lf",
    ".gitignore text eol=lf",
    ".gitattributes text eol=lf"
)
$attributeLines = @(
    $attributes.Replace("`r`n", "`n").Replace("`r", "`n") -split "`n" |
        ForEach-Object { $_.TrimEnd() } |
        Where-Object { $_ }
)
foreach ($rule in $rules) {
    if ($rule -notin $attributeLines) {
        $attributeLines += $rule
    }
}
Write-Utf8Lf -Path $attributesPath -Content (($attributeLines -join "`n") + "`n")

Invoke-Checked -Command { python -m pip install -e ".[dev]" } `
    -Message "Pinned development dependency installation failed"
Remove-PackageMetadata

Invoke-Checked -Command { python -m ruff format . } -Message "Ruff formatting failed"
Invoke-Checked -Command { python -m ruff check . --fix } -Message "Ruff lint repair failed"
Invoke-Checked -Command { python -m ruff format --check . } `
    -Message "Ruff format check failed"
Invoke-Checked -Command { python -m ruff check . } -Message "Ruff lint failed"
Invoke-Checked -Command { python -m mypy src } -Message "mypy strict validation failed"
Invoke-Checked -Command { python -m pytest } -Message "Complete pytest validation failed"
Invoke-Checked -Command { python -m compileall -q src scripts tests } `
    -Message "Python compilation failed"
Invoke-Checked -Command { git diff --check } -Message "Git whitespace validation failed"

if ($RunLiveModel) {
    if (-not $env:OPENAI_API_KEY) {
        throw "OPENAI_API_KEY is required only when -RunLiveModel is selected."
    }
    Invoke-Checked -Command { python scripts/live_agent_smoke.py --model $Model } `
        -Message "Live proposal-only Agent smoke failed"
}

Invoke-Checked -Command { python scripts/finalize_phase6.py } `
    -Message "Phase 6 finalization failed"
Invoke-Checked -Command { python -m ruff format . } `
    -Message "Final Ruff formatting failed"
Invoke-Checked -Command { python -m ruff check . --fix } `
    -Message "Final Ruff lint repair failed"
Invoke-Checked -Command { python -m ruff format --check . } `
    -Message "Final Ruff format check failed"
Invoke-Checked -Command { python -m ruff check . } -Message "Final Ruff lint failed"
Invoke-Checked -Command { python -m mypy src } -Message "Final mypy validation failed"
Invoke-Checked -Command { python -m pytest } -Message "Final pytest validation failed"
Invoke-Checked -Command { python -m compileall -q src scripts tests } `
    -Message "Final Python compilation failed"
Invoke-Checked -Command { git diff --check } `
    -Message "Final Git whitespace validation failed"

Invoke-Checked -Command { git add --all } -Message "Git staging failed"
Invoke-Checked -Command { git diff --cached --check } `
    -Message "Staged Git whitespace validation failed"
Invoke-Checked -Command { git commit -m "Complete phase 06 agent integration" } `
    -Message "Phase 6 commit failed"
Invoke-Checked -Command { git fetch origin } -Message "Final Git fetch failed"
Invoke-Checked -Command { git rebase origin/main } `
    -Message "Rebase onto the current origin/main failed"
Invoke-Checked -Command { git push origin main } -Message "Phase 6 push failed"

$remaining = @(git status --porcelain)
if ($LASTEXITCODE -ne 0 -or $remaining.Count -ne 0) {
    throw "Phase 6 push completed, but the repository is not clean."
}
Write-Host "Phase 6 completed and pushed to origin/main."
