"""Registered synthetic repository and fixed Runner profile catalog."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from cyber_eval.errors import ResourceLimitError, ScopeViolationError
from cyber_eval.identifiers import require_generic_object_id, require_identifier
from cyber_eval.runner.contracts import RegisteredRepository, RunnerProfile

_IMAGE_REF = re.compile(r"^(?:sha256:[a-f0-9]{64}|[a-z0-9][a-z0-9./_-]*@sha256:[a-f0-9]{64})$")


class LocalRunnerRegistry:
    """In-memory catalog; public job APIs receive IDs, never paths or image names."""

    def __init__(self) -> None:
        self._repositories: dict[str, RegisteredRepository] = {}
        self._profiles: dict[str, RunnerProfile] = {}

    def register_repository(
        self,
        repository_id: str,
        target_id: str,
        source_path: Path,
    ) -> RegisteredRepository:
        require_generic_object_id(repository_id)
        require_identifier(target_id, "tgt")
        resolved = source_path.expanduser().resolve(strict=True)
        if not resolved.is_dir():
            raise ValueError("registered repository must be a directory")
        digest = hash_repository(resolved)
        record = RegisteredRepository(repository_id, target_id, resolved, digest)
        self._repositories[repository_id] = record
        return record

    def register_profile(self, profile: RunnerProfile) -> None:
        require_generic_object_id(profile.profile_id)
        require_identifier(profile.test_case_id, "tc")
        if not _IMAGE_REF.fullmatch(profile.image_ref):
            raise ResourceLimitError("runner image must be a digest-pinned local reference")
        if not profile.operations:
            raise ResourceLimitError("runner profile must enable fixed operations")
        self._profiles[profile.profile_id] = profile

    def repository(self, repository_id: str) -> RegisteredRepository:
        require_generic_object_id(repository_id)
        try:
            return self._repositories[repository_id]
        except KeyError as exc:
            raise ScopeViolationError("repository identifier is not registered") from exc

    def profile(self, profile_id: str) -> RunnerProfile:
        require_generic_object_id(profile_id)
        try:
            return self._profiles[profile_id]
        except KeyError as exc:
            raise ScopeViolationError("runner profile identifier is not registered") from exc


def hash_repository(root: Path) -> str:
    digest = hashlib.sha256()
    file_count = 0
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if ".git" in relative.parts:
            continue
        if path.is_symlink():
            raise ScopeViolationError("synthetic repository cannot contain symbolic links")
        if not path.is_file():
            continue
        file_count += 1
        if file_count > 5000:
            raise ResourceLimitError("repository contains too many files")
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
    return digest.hexdigest()
