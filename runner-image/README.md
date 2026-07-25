# Offline Runner image

The Runner image is built only from a Python base image already loaded into local Podman storage.
The build uses `--pull-never` and `--network=none`. The image contains only the repository's
standard-library workload package and runs as UID/GID 65532.

The base image archive, its checksum, provenance, and license record are operator-managed internal
artifacts and are intentionally not committed to this public repository. No registry lookup or
package installation is permitted during a Phase 04 job.
