import json

import pytest

from ccbox.sandbox import (
    build_enter_command,
    effective_config,
    enter,
    write_claude_settings,
)

CONFIG = {
    "runtime": "docker",
    "image": "img:latest",
    "mounts": [{"src": "/data", "mode": "rw"}],
    "claude": {"deny": ["Read(/pscratch/**)"], "allow": []},
}


def test_effective_config_mounts_project_rw(tmp_path):
    result = effective_config({"mounts": []}, tmp_path)
    project = str(tmp_path.resolve())
    assert result["workdir"] == project
    assert result["mounts"][0] == {"src": project, "dst": project, "mode": "rw"}


def test_effective_config_preserves_existing_mounts(tmp_path):
    result = effective_config({"mounts": [{"src": "/data", "mode": "ro"}]}, tmp_path)
    sources = [mount["src"] for mount in result["mounts"]]
    assert str(tmp_path.resolve()) in sources
    assert "/data" in sources


def test_effective_config_no_duplicate_project_mount(tmp_path):
    project = str(tmp_path.resolve())
    result = effective_config({"mounts": [{"src": project, "mode": "ro"}]}, tmp_path)
    assert sum(1 for mount in result["mounts"] if mount["src"] == project) == 1


def test_write_claude_settings(tmp_path):
    path = write_claude_settings(CONFIG, tmp_path)
    assert path == tmp_path / ".claude" / "settings.json"
    data = json.loads(path.read_text())
    assert data["permissions"]["deny"] == ["Read(/pscratch/**)"]


def test_build_enter_command_default_inner(tmp_path):
    name, command = build_enter_command(effective_config(CONFIG, tmp_path))
    assert name == "docker"
    assert command[0] == "docker"
    assert command[-1] == "claude"
    assert "img:latest" in command


def test_build_enter_command_custom_argv(tmp_path):
    _, command = build_enter_command(
        effective_config(CONFIG, tmp_path), ["pytest", "-q"]
    )
    assert command[-2:] == ["pytest", "-q"]


def test_build_enter_command_requires_image():
    with pytest.raises(ValueError, match="image"):
        build_enter_command({"runtime": "docker", "image": None, "mounts": []})


def test_enter_dry_run_does_not_write_or_run(tmp_path, capsys):
    calls: list[list[str]] = []
    code = enter(
        CONFIG,
        tmp_path,
        dry_run=True,
        runner=lambda command: calls.append(command) or 0,
    )
    assert code == 0
    assert calls == []
    assert not (tmp_path / ".claude" / "settings.json").exists()
    assert "docker" in capsys.readouterr().out


def test_enter_writes_settings_and_runs(tmp_path):
    captured: dict[str, list[str]] = {}

    def fake_runner(command: list[str]) -> int:
        captured["command"] = command
        return 7

    code = enter(CONFIG, tmp_path, ["bash"], runner=fake_runner)
    assert code == 7
    assert (tmp_path / ".claude" / "settings.json").is_file()
    assert captured["command"][0] == "docker"
    assert captured["command"][-1] == "bash"
