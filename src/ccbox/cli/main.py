"""Parser construction and dispatch for the ccbox CLI."""

import argparse

from ccbox import __version__
from ccbox.cli.registry import ALL_COMMANDS


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level parser with every command registered.

    Returns
    -------
    argparse.ArgumentParser
        A parser whose subcommands dispatch to their :class:`~ccbox.cli.base.Command`.
    """
    parser = argparse.ArgumentParser(
        prog="ccbox", description="Run Claude Code in a sandbox."
    )
    parser.add_argument("--version", action="version", version=f"ccbox {__version__}")
    parser.add_argument(
        "-C", "--project-dir", default=".", help="project directory (default: cwd)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command_class in ALL_COMMANDS:
        command = command_class()
        subparser = subparsers.add_parser(command.name, help=command.help)
        command.add_arguments(subparser)
        subparser.set_defaults(command_impl=command)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``ccbox`` console script.

    Parameters
    ----------
    argv : list[str] or None, optional
        Argument vector to parse. Defaults to ``sys.argv`` when ``None``.

    Returns
    -------
    int
        The process exit code returned by the dispatched command.
    """
    args = build_parser().parse_args(argv)
    return int(args.command_impl.run(args))
