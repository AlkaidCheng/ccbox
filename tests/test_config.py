from ccbox.config import deep_merge, load_config


def test_deep_merge_scalar_override():
    assert deep_merge({"a": 1}, {"a": 2}) == {"a": 2}


def test_deep_merge_list_append():
    assert deep_merge({"m": [1]}, {"m": [2]}) == {"m": [1, 2]}


def test_deep_merge_nested_dict():
    merged = deep_merge(
        {"claude": {"deny": ["a"], "allow": []}},
        {"claude": {"deny": ["b"]}},
    )
    assert merged["claude"]["deny"] == ["a", "b"]
    assert merged["claude"]["allow"] == []


def test_load_config_layers_project_over_global(tmp_path):
    global_cfg = tmp_path / "global.yaml"
    global_cfg.write_text("mode: accident\nmounts:\n  - {src: /a, mode: ro}\n")
    project = tmp_path / "proj"
    project.mkdir()
    (project / ".ccbox.yaml").write_text(
        "mode: adversarial\nmounts:\n  - {src: /b, mode: rw}\n"
    )

    config = load_config(project_dir=project, global_path=global_cfg)

    assert config["mode"] == "adversarial"  # scalar overridden
    assert [m["src"] for m in config["mounts"]] == ["/a", "/b"]  # lists appended


def test_load_config_defaults_present(tmp_path):
    config = load_config(project_dir=tmp_path, global_path=tmp_path / "missing.yaml")
    assert config["runtime"] == "auto"
    assert "Read(~/.ssh/**)" in config["claude"]["deny"]
