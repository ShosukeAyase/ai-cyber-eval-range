"""Identifier validation that prevents raw network destinations from crossing APIs."""

from __future__ import annotations

import re
from uuid import uuid4

from cyber_eval.errors import InvalidIdentifierError

_PATTERNS = {
    "eng": re.compile(r"^eng-[a-z0-9-]{3,64}$"),
    "tgt": re.compile(r"^tgt-[a-z0-9-]{3,64}$"),
    "tc": re.compile(r"^tc-[a-z0-9-]{3,64}$"),
    "apr": re.compile(r"^apr-[a-z0-9-]{3,64}$"),
    "req": re.compile(r"^req-[a-z0-9-]{3,64}$"),
    "tmpl": re.compile(r"^tmpl-[a-z0-9-]{3,64}$"),
    "job": re.compile(r"^job-[a-z0-9-]{3,64}$"),
}
_GENERIC_OBJECT = re.compile(r"^(repo|prof|tc|poc|evd|fnd|pat|suite|scn|ctx)-[a-z0-9-]{3,64}$")


def require_identifier(value: str, prefix: str) -> str:
    pattern = _PATTERNS[prefix]
    if not pattern.fullmatch(value):
        raise InvalidIdentifierError(f"invalid {prefix} identifier")
    return value


def require_generic_object_id(value: str) -> str:
    if not _GENERIC_OBJECT.fullmatch(value):
        raise InvalidIdentifierError("invalid registered object identifier")
    return value


def new_identifier(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"
