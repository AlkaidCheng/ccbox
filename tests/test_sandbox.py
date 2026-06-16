import json
import os

import pytest

from ccbox.runtime.oci import DockerRuntime
from ccbox.sandbox import (
    build_enter_command,
    container_name,
    effective_config,
    enter,
    expand_mounts,
    merge_claude_settings,
    warm_command_sequence,
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


def test_expand_mounts_expands_env_var(monkeypatch):
    monkeypatch.setenv("CCBOX_TEST_DIR", "/opt/env")
    result = expand_mounts([{"src": "$CCBOX_TEST_DIR/lib", "dst": "/d", "mode": "ro"}])
    assert result[0]["src"] == "/opt/env/lib"
    assert result[0]["dst"] == "/d"


def test_expand_mounts_expands_user():
    result = expand_mounts([{"src": "~/data", "mode": "rw"}])
    assert result[0]["src"] == os.path.expanduser("~/data")


def test_expand_mounts_preserves_plain_mount():
    assert expand_mounts([{"src": "/x", "mode": "ro"}]) == [{"src": "/x", "mode": "ro"}]


def test_effective_config_expands_mount_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("CCBOX_TEST_DIR", "/opt/env")
    result = effective_config(
        {"mounts": [{"src": "$CCBOX_TEST_DIR", "mode": "ro"}]}, tmp_path
    )
    assert any(mount["src"] == "/opt/env" for mount in result["mounts"])


def test_write_claude_settings_merges_existing(tmp_path):
    settings = tmp_path / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(
        json.dumps(
            {
                "model": "opus",
                "permissions": {"deny": ["Read(/secret/**)"], "allow": []},
            }
        )
    )
    write_claude_settings(CONFIG, tmp_path)
    data = json.loads(settings.read_text())
    assert data["model"] == "opus"  # unrelated key preserved
    assert data["permissions"]["deny"] == ["Read(/secret/**)", "Read(/pscratch/**)"]


def test_write_claude_settings_is_idempotent(tmp_path):
    write_claude_settings(CONFIG, tmp_path)
    write_claude_settings(CONFIG, tmp_path)
    data = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    assert data["permissions"]["deny"] == ["Read(/pscratch/**)"]


def test_write_claude_settings_invalid_json_raises(tmp_path):
    settings = tmp_path / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text("{not json")
    with pytest.raises(ValueError, match="valid JSON"):
        write_claude_settings(CONFIG, tmp_path)


def test_merge_claude_settings_unions_and_dedups():
    existing = {"x": 1, "permissions": {"deny": ["a"], "allow": ["p"]}}
    rendered = {"permissions": {"deny": ["a", "b"], "allow": []}}
    merged = merge_claude_settings(existing, rendered)
    assert merged["x"] == 1
    assert merged["permissions"]["deny"] == ["a", "b"]
    assert merged["permissions"]["allow"] == ["p"]


def test_container_name_stable_and_prefixed(tmp_path):
    assert container_name(tmp_path) == container_name(tmp_path)
    assert container_name(tmp_path).startswith("ccbox-")


def test_container_name_differs_by_path(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    assert container_name(tmp_path / "a") != container_name(tmp_path / "b")


def test_warm_command_sequence_running():
    commands = warm_command_sequence(
        DockerRuntime(),
        {"image": "img"},
        "ccbox-x",
        ["claude"],
        lambda binary, name: "running",
    )
    assert commands == [["docker", "exec", "-it", "ccbox-x", "claude"]]


def test_warm_command_sequence_stopped():
    commands = warm_command_sequence(
        DockerRuntime(),
        {"image": "img"},
        "ccbox-x",
        ["claude"],
        lambda binary, name: "stopped",
    )
    assert commands[0] == ["docker", "start", "ccbox-x"]
    assert commands[1][:2] == ["docker", "exec"]


def test_warm_command_sequence_absent():
    commands = warm_command_sequence(
        DockerRuntime(),
        {"image": "img"},
        "ccbox-x",
        ["claude"],
        lambda binary, name: "absent",
    )
    assert commands[0][:5] == ["docker", "run", "-d", "--name", "ccbox-x"]
    assert commands[1][:2] == ["docker", "exec"]


def test_enter_warm_dry_run(tmp_path, capsys):
    code = enter(
        CONFIG, tmp_path, dry_run=True, warm=True, status=lambda binary, name: "running"
    )
    assert code == 0
    assert "exec" in capsys.readouterr().out


def test_enter_warm_unsupported_runtime_raises(tmp_path):
    config = {"runtime": "apptainer", "image": "img.sif"}
    with pytest.raises(ValueError, match="warm"):
        enter(
            config,
            tmp_path,
            warm=True,
            dry_run=True,
            status=lambda binary, name: "running",
        )
