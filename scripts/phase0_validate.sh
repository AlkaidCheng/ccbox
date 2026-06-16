#!/usr/bin/env bash
# Phase 0 validation: prove the project's code can use a read-only conda env
# inside the sandbox. Runtime-agnostic for OCI backends (docker/podman/podman-hpc).
#
# Usage: scripts/phase0_validate.sh <repo_dir> <conda_prefix> [image]
set -euo pipefail

REPO_DIR=${1:?usage: phase0_validate.sh <repo_dir> <conda_prefix> [image]}
CONDA_PREFIX_ARG=${2:?usage: phase0_validate.sh <repo_dir> <conda_prefix> [image]}
IMAGE=${3:-docker.io/library/python:3.12-slim}

# Pick the first available OCI runtime.
RUNTIME=""
for candidate in podman-hpc podman docker; do
  if command -v "$candidate" >/dev/null 2>&1; then
    RUNTIME=$candidate
    break
  fi
done
if [[ -z "$RUNTIME" ]]; then
  echo "no OCI runtime found (looked for podman-hpc, podman, docker)" >&2
  exit 1
fi
echo "runtime: $RUNTIME"

# Mount the repo rw and the conda env ro at its identical absolute path.
"$RUNTIME" run --rm \
  --volume "${REPO_DIR}:${REPO_DIR}:rw" \
  --volume "${CONDA_PREFIX_ARG}:${CONDA_PREFIX_ARG}:ro" \
  --workdir "${REPO_DIR}" \
  "$IMAGE" \
  "${CONDA_PREFIX_ARG}/bin/python" -c \
  "import sys; print('env python OK:', sys.executable)"

echo "PASS: the conda env's python ran inside the sandbox."
echo "Next: add Read(${CONDA_PREFIX_ARG}/**) to .claude/settings.json deny and"
echo "confirm Claude's Read tool refuses it while python still imports from it."
