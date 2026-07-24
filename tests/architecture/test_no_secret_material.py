import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = [ROOT / "src", ROOT / "tests", ROOT / "examples", ROOT / "policies"]
PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "openai_key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
}


def test_no_secret_material_patterns():
    findings = []
    for root in SCAN_ROOTS:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix in {".pyc"}:
                continue
            text = path.read_text(errors="ignore")
            for name, pattern in PATTERNS.items():
                if pattern.search(text):
                    findings.append((str(path.relative_to(ROOT)), name))
    assert not findings, findings
