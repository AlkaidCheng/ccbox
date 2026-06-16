from ccbox.cli.main import build_parser, main
from ccbox.cli.registry import ALL_COMMANDS
from ccbox.sandbox import adversarial_workspace


def test_all_commands_have_metadata():
    for command_class in ALL_COMMANDS:
        assert command_class.name and command_class.help and command_class.category


def test_command_names_unique():
    names = [command_class.name for command_class in ALL_COMMANDS]
    assert len(names) == len(set(names))


def test_parser_dispatches_subcommand():
    args = build_parser().parse_args(["runtimes"])
    assert args.command_impl.name == "runtimes"


def test_main_config_command(tmp_path, capsys):
    exit_code = main(["-C", str(tmp_path), "config"])
    assert exit_code == 0
    assert '"mode"' in capsys.readouterr().out


def test_main_init_writes_file(tmp_path):
    exit_code = main(["-C", str(tmp_path), "init"])
    assert exit_code == 0
    assert (tmp_path / ".ccbox.yaml").is_file()


def test_main_enter_dry_run(tmp_path, capsys):
    (tmp_path / ".ccbox.yaml").write_text("runtime: docker\nimage: img:latest\n")
    exit_code = main(["-C", str(tmp_path), "enter", "--dry-run"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "docker" in out
    assert "img:latest" in out


def test_main_enter_warm_dry_run(tmp_path, capsys):
    (tmp_path / ".ccbox.yaml").write_text("runtime: docker\nimage: img:latest\n")
    exit_code = main(["-C", str(tmp_path), "enter", "--warm", "--dry-run"])
    assert exit_code == 0
    assert "exec" in capsys.readouterr().out


def test_main_harvest_dry_run(tmp_path, capsys):
    exit_code = main(["-C", str(tmp_path), "harvest", "main", "--dry-run"])
    assert exit_code == 0
    assert "bundle" in capsys.readouterr().out


def test_main_apply_dry_run(tmp_path, capsys):
    exit_code = main(["-C", str(tmp_path), "apply", "x.bundle", "main", "--dry-run"])
    assert exit_code == 0
    assert "fetch" in capsys.readouterr().out


def test_main_enter_adversarial_dry_run(tmp_path, monkeypatch, capsys):
    cache = tmp_path.parent / "ccbox-cache-test"  # outside the project dir
    monkeypatch.setenv("CCBOX_CACHE_DIR", str(cache))
    (tmp_path / ".ccbox.yaml").write_text(
        "runtime: docker\nimage: img:latest\nmode: adversarial\nnetwork: deny\n"
    )
    work_dir, _ = adversarial_workspace(tmp_path)
    exit_code = main(["-C", str(tmp_path), "enter", "--dry-run"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert str(work_dir.resolve()) in out
    assert str(tmp_path.resolve()) not in out
