param(
    [Parameter(Mandatory = $true)]
    [string]$BaseImage
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot

$rootless = podman info --format "{{.Host.Security.Rootless}}"
if ($LASTEXITCODE -ne 0 -or $rootless.Trim().ToLowerInvariant() -ne "true") {
    throw "Podman must be available in rootless mode."
}

podman image exists $BaseImage
if ($LASTEXITCODE -ne 0) {
    throw "The digest-pinned base image is not present in local Podman storage."
}

podman build `
    --pull-never `
    --network=none `
    --build-arg "BASE_IMAGE=$BaseImage" `
    --file "$repo\runner-image\Containerfile" `
    --tag localhost/cyber-eval-runner:phase4 `
    $repo
if ($LASTEXITCODE -ne 0) {
    throw "Runner image build failed."
}

$imageId = podman image inspect --format "{{.Id}}" localhost/cyber-eval-runner:phase4
if ($LASTEXITCODE -ne 0 -or -not $imageId) {
    throw "Could not resolve the local Runner image ID."
}

Write-Host "Runner image reference: $($imageId.Trim())"
Write-Host "Run: python scripts/live_runner_smoke.py --image-ref $($imageId.Trim())"
Write-Output $imageId.Trim()
