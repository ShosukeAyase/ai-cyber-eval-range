import shutil

TOOLS = [
    "opa",
    "tofu",
    "terraform",
    "markdownlint",
    "ruff",
    "mypy",
    "pip-audit",
    "cyclonedx-py",
    "trivy",
    "syft",
    "grype",
    "cosign",
    "gitleaks",
]

for tool in TOOLS:
    status = "available" if shutil.which(tool) else "not installed"
    print(f"{tool}: {status}")
