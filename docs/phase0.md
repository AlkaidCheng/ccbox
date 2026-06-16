# Phase 0 — Validate the core mechanic

Before building automation, prove the one assumption the whole tool rests on:

> Inside a sandbox, the project's **code** can reach a mounted path while
> **Claude's own file tools** are denied it.

This asymmetry is what "code can, Claude can't" (accident mode) depends on. It
comes from a documented Claude Code behavior: `deny` rules gate the built-in
file tools and recognised Bash file commands (`cat`, `sed`, …) but **not**
arbitrary subprocesses such as `python script.py`.

## Acceptance criteria

1. A container runtime is available and detected (`ccbox runtimes`).
2. A read-only mount of a conda env at its **identical absolute path** lets
   `python` import from it.
3. With `Read(<mounted path>/**)` denied in `.claude/settings.json`, Claude's
   Read tool refuses the path, while a `python` subprocess still reads it.
4. Nothing outside the explicit mounts is reachable.

## Steps (runtime-agnostic)

The example below uses an OCI runtime (docker / podman / podman-hpc). For
Apptainer/Singularity the flags differ (`--bind`, `.sif` image); `ccbox enter`
will render the right form per backend.

1. Pick a project dir (a git repo) and note your conda env prefix
   (`echo $CONDA_PREFIX`).
2. Run the validation helper:

   ```bash
   scripts/phase0_validate.sh /path/to/repo "$CONDA_PREFIX"
   ```

   It mounts the repo `rw` and the env `ro` at the same path, then checks that
   the env's `python` runs inside the sandbox.
3. Add deny rules and confirm the asymmetry by hand:
   - `Read(<env>/**)` denied → Claude's Read refuses; `python -c "import ..."`
     still works.
4. Try to read a path you did **not** mount → it should not exist inside.

## Notes

- **Conda paths are absolute**: bind the env at the same path inside the
  container, or call `"$CONDA_PREFIX/bin/python"` directly to avoid needing
  `conda activate` (and the base install mount).
- **Wrong architecture = emulation**: always use a `linux/amd64` image on
  x86-64 hosts; an `arm64` image runs under slow emulation.
- **Windows**: run the bash helper under WSL or Git Bash; the `ccbox` CLI itself
  is cross-platform.

## Outcome

When all four criteria hold, the asymmetry is proven and Phase 1 (live
`enter`, warm-container reuse, settings injection) can build on it.
