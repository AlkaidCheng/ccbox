from ccbox.cli.main import build_parser, main
from ccbox.cli.registry import ALL_COMMANDS


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
