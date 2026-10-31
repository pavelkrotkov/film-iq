"""Preview local changes, optionally acknowledging only after successful output."""

import argparse
import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from film_iq.changes import checkpoint, digest, markdown
from film_iq.operations_write import private_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="film-iq changes", description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument(
        "--checkpoint",
        type=Path,
        required=True,
        help="Private IDs-only state; one consumer per file",
    )
    parser.add_argument(
        "--ack",
        action="store_true",
        help="Acknowledge successful output; first use records a baseline",
    )
    parser.add_argument(
        "--output", type=Path, help="Atomic private output; otherwise flushed stdout"
    )
    parser.add_argument("--now", type=datetime.fromisoformat)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args(argv)
    try:
        _run(args)
    except (OSError, ValueError, TypeError, sqlite3.Error) as error:
        parser.error(str(error))
    return 0


def _run(args) -> None:
    now = args.now or datetime.now(UTC)
    paths = [args.database.resolve(), args.checkpoint.resolve()]
    if args.output:
        paths.append(args.output.resolve())
    if len(paths) != len(set(paths)):
        raise ValueError("database, checkpoint and output must be different files")
    with closing(sqlite3.connect(paths[0].as_uri() + "?mode=ro", uri=True)) as db:
        db.execute("BEGIN")
        result, acknowledged = digest(db, checkpoint(args.checkpoint), now)
    result["acknowledgement"] = (
        "requested after successful output" if args.ack else "preview; not acknowledged"
    )
    output = json.dumps(result, indent=2) if args.format == "json" else markdown(result)
    if args.output:
        private_text(args.output, output)
    else:
        print(output, flush=True)
    if args.ack:
        private_text(args.checkpoint, json.dumps(acknowledged, indent=2))
