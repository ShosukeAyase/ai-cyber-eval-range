[CmdletBinding()]
param(
    [string]$RepoPath = "$HOME\Downloads\cyber-evaluation-platform-design",
    [string]$ZipPath = "$HOME\Downloads\cyber-evaluation-platform-design-phase5.zip"
)

$ErrorActionPreference = "Stop"

function Assert-Success([string]$Message) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Message (exit code $LASTEXITCODE)"
    }
}

function Write-Utf8LfFile {
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
        [string]$Path,
        [Parameter(Mandatory)]
        [string]$Entry
    )

    $content = ""
    if (Test-Path $Path -PathType Leaf) {
        $content = [System.IO.File]::ReadAllText((Resolve-Path $Path).Path)
    }
    $content = $content.Replace("`r`n", "`n").Replace("`r", "`n")
    $lines = @(
        $content -split "`n" |
            ForEach-Object { $_.TrimEnd() } |
            Where-Object { $_ -and $_ -ne $Entry }
    )
    $lines += $Entry
    Write-Utf8LfFile -Path $Path -Content ((($lines -join "`n").TrimEnd()) + "`n")
}

$repo = [System.IO.Path]::GetFullPath($RepoPath)
$zip = [System.IO.Path]::GetFullPath($ZipPath)

if (-not (Test-Path $repo -PathType Container)) {
    throw "Repository directory does not exist: $repo"
}
if (-not (Test-Path (Join-Path $repo ".git") -PathType Container)) {
    throw "Repository .git directory is missing: $repo"
}
if (-not (Test-Path $zip -PathType Leaf)) {
    throw "Phase 5 ZIP does not exist: $zip"
}

# Permit only the known line-ending repair from a previously interrupted run.
Push-Location $repo
try {
    Ensure-GitIgnoreEntry -Path ".gitignore" -Entry "*.egg-info/"
    Get-ChildItem -Path "src" -Directory -Filter "*.egg-info" -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    $status = & git status --porcelain
    Assert-Success "Could not inspect repository status"
    $unexpected = @($status | Where-Object {
        $_ -notmatch '^ M \.gitignore$' -and
        $_ -notmatch '^\?\? \.gitattributes$'
    })
    if ($unexpected) {
        throw "The repository contains changes other than the known line-ending repair. Review git status first.`n$($unexpected -join "`n")"
    }

    if ($status) {
        & git add .gitignore .gitattributes 2>$null
        & git commit -m "Normalize generated metadata exclusions"
        Assert-Success "Could not commit line-ending repair"
    }
}
finally {
    Pop-Location
}

& git -C $repo fetch origin
Assert-Success "git fetch failed"
& git -C $repo pull --rebase origin main
Assert-Success "The local main branch could not be rebased onto origin/main"

$tempRoot = Join-Path $env:TEMP ("cyber-eval-phase5-" + [guid]::NewGuid().ToString("N"))
try {
    Expand-Archive -Path $zip -DestinationPath $tempRoot -Force
    $source = Join-Path $tempRoot "cyber-evaluation-platform-design"
    if (-not (Test-Path $source -PathType Container)) {
        throw "The ZIP does not contain cyber-evaluation-platform-design at its root."
    }

    & robocopy $source $repo /MIR /R:1 /W:1 /NFL /NDL /NJH /NJS /NP `
        /XD .git .venv __pycache__ .pytest_cache .mypy_cache .ruff_cache "*.egg-info" `
        /XF *.pyc
    $robocopyExit = $LASTEXITCODE
    if ($robocopyExit -gt 7) {
        throw "Repository synchronization failed (robocopy exit code $robocopyExit)"
    }

    # Normalize control files after ZIP synchronization.
    Push-Location $repo
    try {
        Ensure-GitIgnoreEntry -Path ".gitignore" -Entry "*.egg-info/"
        $attributes = @'
* text=auto
*.py text eol=lf
*.md text eol=lf
*.txt text eol=lf
*.json text eol=lf
*.yaml text eol=lf
*.yml text eol=lf
*.toml text eol=lf
.gitignore text eol=lf
.gitattributes text eol=lf
'@
        Write-Utf8LfFile -Path ".gitattributes" -Content ($attributes.TrimStart("`r", "`n") + "`n")
        Get-ChildItem -Path "src" -Directory -Filter "*.egg-info" -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
    finally {
        Pop-Location
    }

    $completion = Join-Path $repo "scripts\complete_phase5_local.ps1"
    if (-not (Test-Path $completion -PathType Leaf)) {
        throw "Phase 5 repository completion script is missing after synchronization."
    }

    & $completion -Finalize -CommitAndPush
    if (-not $?) {
        throw "Phase 5 repository completion script failed."
    }

    $finalStatus = & git -C $repo status --porcelain
    Assert-Success "Final repository status inspection failed"
    if ($finalStatus) {
        throw "Phase 5 completed, but the working tree is not clean.`n$($finalStatus -join "`n")"
    }

    Write-Host "Phase 5 completed and pushed to origin/main."
}
finally {
    Remove-Item $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
