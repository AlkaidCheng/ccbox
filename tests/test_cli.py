from ccbox.cli.base import Command, registered_commands
from ccbox.cli.main import build_parser, main
from ccbox.cli.registry import ALL_COMMANDS, COMMAND_GROUPS
from ccbox.sandbox import adversarial_workspace


def test_all_commands_have_metadata():
    for command_class in ALL_COMMANDS:
        assert command_class.name and command_class.help and command_class.category


def test_command_names_unique():
    names = [command_class.name for command_class in ALL_COMMANDS]
    assert len(names) == len(set(names))


def test_discovery_finds_known_commands():
    names = {command_class.name for command_class in ALL_COMMANDS}
    assert {"init", "config", "enter", "bake", "harvest"} <= names


def test_command_groups_match_categories():
    for category, commands in COMMAND_GROUPS.items():
        assert commands  # no empty groups
        assert all(command.category == category for command in commands)


def test_subclass_self_registers():
    class _ProbeCommand(Command):
        name = "_probe"
        help = "probe"
        category = "test"

        def run(self, args):
            return 0

    assert _ProbeCommand in registered_commands()


def test_subclass_without_name_is_not_registered():
    class _AbstractBase(Command):
        def run(self, args):
            return 0

    assert _AbstractBase not in registered_commands()


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


def test_main_harvest_adversarial_uses_workcopy(tmp_path, monkeypatch, capsys):
    cache = tmp_path.parent / "ccbox-cache-test"
    monkeypatch.setenv("CCBOX_CACHE_DIR", str(cache))
    (tmp_path / ".ccbox.yaml").write_text(
        "mode: adversarial\nnetwork: deny\nimage: img:latest\n"
    )
    work_dir, _ = adversarial_workspace(tmp_path)
    exit_code = main(["-C", str(tmp_path), "harvest", "main", "--dry-run"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert str(work_dir.resolve()) in out  # bundled from the work copy
    assert "harvest.bundle" in out  # into the outbox


def test_main_apply_adversarial_defaults_to_outbox(tmp_path, monkeypatch, capsys):
    cache = tmp_path.parent / "ccbox-cache-test"
    monkeypatch.setenv("CCBOX_CACHE_DIR", str(cache))
    (tmp_path / ".ccbox.yaml").write_text(
        "mode: adversarial\nnetwork: deny\nimage: img:latest\n"
    )
    exit_code = main(["-C", str(tmp_path), "apply", "--dry-run"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "harvest.bundle" in out
    assert "fetch" in out


def test_main_apply_requires_bundle_when_not_adversarial(tmp_path):
    exit_code = main(["-C", str(tmp_path), "apply", "--dry-run"])
    assert exit_code == 1


def test_main_bake_dry_run(tmp_path, monkeypatch, capsys):
    import ccbox.image_build as ib

    monkeypatch.setattr(
        ib.shutil, "which", lambda b: "/x/docker" if b == "docker" else None
    )
    (tmp_path / ".ccbox.yaml").write_text(
        "image: img:latest\nbuild:\n  recipe: Dockerfile\n"
    )
    exit_code = main(["-C", str(tmp_path), "bake", "--dry-run"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "build" in out and "img:latest" in out and "Dockerfile" in out


def test_main_bake_requires_recipe(tmp_path):
    (tmp_path / ".ccbox.yaml").write_text("image: img:latest\n")
    assert main(["-C", str(tmp_path), "bake", "--dry-run"]) == 1


def test_main_bake_no_builder(tmp_path, monkeypatch):
    import ccbox.image_build as ib

    monkeypatch.setattr(ib.shutil, "which", lambda b: None)
    (tmp_path / ".ccbox.yaml").write_text(
        "image: img:latest\nbuild:\n  recipe: Dockerfile\n"
    )
    assert main(["-C", str(tmp_path), "bake", "--dry-run"]) == 1


def test_main_bake_incompatible_runtime(tmp_path):
    (tmp_path / ".ccbox.yaml").write_text(
        "image: img:latest\nruntime: bwrap\nbuild:\n  recipe: Dockerfile\n"
    )
    assert main(["-C", str(tmp_path), "bake", "--dry-run"]) == 1
