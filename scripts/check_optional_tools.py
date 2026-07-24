import shutil
TOOLS = ["opa","tofu","terraform","markdownlint","trivy","syft","grype","cosign","gitleaks"]
for tool in TOOLS:
    print(f"{tool}: {'available' if shutil.which(tool) else 'not installed'}")
