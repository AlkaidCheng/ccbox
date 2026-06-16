from ccbox.git_sync import apply, build_apply_command, build_bundle_command, harvest


def test_build_bundle_command():
    assert build_bundle_command("main", "out.bundle") == [
        "git",
        "bundle",
        "create",
        "out.bundle",
        "main",
    ]


def test_build_bundle_command_repo_dir():
    command = build_bundle_command("HEAD", "o.bundle", repo_dir="/repo")
    assert command[:3] == ["git", "-C", "/repo"]
    assert command[-2:] == ["o.bundle", "HEAD"]


def test_build_apply_command_neutralises_hooks():
    command = build_apply_command("o.bundle", "main")
    assert "core.hooksPath=/dev/null" in command
    assert command[-3:] == ["fetch", "o.bundle", "main"]


def test_harvest_dry_run(capsys):
    assert harvest("main", "o.bundle", dry_run=True) == 0
    assert "bundle" in capsys.readouterr().out


def test_harvest_runs_with_injected_runner(tmp_path):
    captured: dict[str, list[str]] = {}

    def runner(command: list[str]) -> int:
        captured["command"] = command
        return 0

    assert harvest("main", "o.bundle", repo_dir=str(tmp_path), runner=runner) == 0
    assert captured["command"][:3] == ["git", "-C", str(tmp_path)]


def test_apply_dry_run(capsys):
    assert apply("o.bundle", "main", dry_run=True) == 0
    out = capsys.readouterr().out
    assert "fetch" in out
    assert "core.hooksPath=/dev/null" in out
