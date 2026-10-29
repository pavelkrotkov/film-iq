"""Minimal CLI entry point; domain features are tracked in GitHub epics."""

import argparse
from collections.abc import Sequence

from film_iq import __version__


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="film-iq", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="Show the bootstrap implementation status")
    args = parser.parse_args(argv)
    if args.command == "status":
        print("film-iq bootstrap: CI and plan present; POC features are not implemented")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
