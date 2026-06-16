# ccbox

Run Claude Code inside a sandbox, so it can work freely in one project
directory without reaching the rest of your filesystem, your credentials, or
the network.

ccbox detects whatever container backend is available (Docker, Podman,
Apptainer/Singularity, podman-hpc) and runs on Linux, macOS, and Windows.

## Why

Giving an AI coding agent access to your machine means, in principle, access to
far more than the project you pointed it at. ccbox puts a real, OS-enforced
boundary around the agent: only the directories you choose are visible inside,
and you decide whether the sandbox can reach the network.

## Modes

- **accident** (default) — guards against mistakes and limits blast radius.
  Your project's code can still reach the resources it needs (a conda
  environment, a data directory) while the agent stays within the project.
- **adversarial** — treats the agent as untrusted: minimal mounts, no implicit
  filesystem access, and network denied or restricted to an allowlist.

## Install

```bash
pip install ccbox
```

## Usage

```bash
ccbox init        # scaffold a .ccbox.yaml in the current project
ccbox runtimes    # list backends and show the detected default
ccbox doctor      # check the configuration for safety issues
ccbox enter       # start the sandbox
```

Configuration is layered: a global config provides defaults, and a per-project
`.ccbox.yaml` overrides them.

- global: `<config dir>/ccbox/config.yaml`
- project: `<project>/.ccbox.yaml`

Example `.ccbox.yaml`:

```yaml
mode: accident
runtime: auto
mounts:
  - { src: $CONDA_PREFIX, mode: ro, same_path: true }
  - { src: ./data, dst: /data, mode: rw }
```

## Environment variables

- `CCBOX_CACHE_DIR` — where ccbox stores its per-project cache (in adversarial
  mode, the isolated copy of the project and its outbox). Takes precedence over
  the platform default (`~/.cache/ccbox`, or `%LOCALAPPDATA%\ccbox` on Windows).
  Set it to choose your own location.

## Contributing

```bash
pip install -e ".[dev]"
pytest
```

## Acknowledgments

Developed with the assistance of Claude Code.

## License

MIT — see [LICENSE](LICENSE).
