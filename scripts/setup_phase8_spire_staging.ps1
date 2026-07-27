param(
    [string]$ClusterName = "phase8-spire",
    [string]$KindNodeImage = "kindest/node:v1.34.0",
    [string]$SpireChartVersion = "0.29.0",
    [string]$SpireCrdsChartVersion = "0.5.0"
)

$ErrorActionPreference = "Stop"

foreach ($tool in @("docker", "kind", "kubectl", "helm")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "Required command is unavailable: $tool"
    }
}

$clusters = @(kind get clusters)
if ($ClusterName -notin $clusters) {
    kind create cluster --name $ClusterName --image $KindNodeImage
}

kubectl config use-context "kind-$ClusterName"
helm upgrade --install spire-crds spire-crds `
    --repo https://spiffe.github.io/helm-charts-hardened/ `
    --namespace spire-mgmt `
    --create-namespace `
    --version $SpireCrdsChartVersion `
    --wait `
    --timeout 10m
helm upgrade --install spire spire `
    --repo https://spiffe.github.io/helm-charts-hardened/ `
    --namespace spire-mgmt `
    --version $SpireChartVersion `
    --values staging/spire/values.yaml `
    --wait `
    --timeout 15m

foreach ($namespace in @(
    "phase8-control",
    "phase8-execution",
    "phase8-range",
    "phase8-evidence",
    "phase8-management"
)) {
    kubectl create namespace $namespace --dry-run=client -o yaml | kubectl apply -f -
}

kubectl get pods --all-namespaces -l app.kubernetes.io/instance=spire
Write-Output "SPIRE staging foundation installed. Deploy labeled workloads and execute the mTLS evidence cases documented under staging/spire/README.md."
