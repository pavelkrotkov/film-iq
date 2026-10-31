"""One private, locked refresh/report/backup run for a native scheduler."""

import argparse
import json
from pathlib import Path

from film_iq.movary import MovaryClient
from film_iq.operations_run import run_once
from film_iq.refresh_movary import _command
from film_iq.sync_cli import _required_env


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("database", "snapshot", "report", "backups", "status"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--cohort", type=Path, action="append", required=True)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--order", choices=("source", "public-support"), default="public-support")
    for name in ("ratings", "history"):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(f"--{name}-csv", type=Path)
        group.add_argument(f"--{name}-command", type=_command)
    args = parser.parse_args(argv)
    try:
        client = MovaryClient(
            *(_required_env(key) for key in ("MOVARY_URL", "MOVARY_USERNAME", "MOVARY_TOKEN"))
        )
        result = run_once(client, **vars(args))
    except (OSError, ValueError, RuntimeError):
        parser.exit(1, "Private run failed; inspect its status file, then retry.\n")
    print(json.dumps({"status": "complete", "completed_at": result["last_successful_run"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
