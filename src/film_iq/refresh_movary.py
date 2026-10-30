"""Read-only Movary refresh; personal output remains in a private local snapshot."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from film_iq.movary import MovaryClient
from film_iq.personal_refresh import refresh
from film_iq.sync_cli import _required_env


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    for name in ("ratings", "history"):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(f"--{name}-csv", type=Path)
        group.add_argument(
            f"--{name}-command", type=_command, help="JSON argv emitting complete CSV to stdout"
        )
    args = parser.parse_args(argv)
    try:
        client = MovaryClient(
            *(_required_env(key) for key in ("MOVARY_URL", "MOVARY_USERNAME", "MOVARY_TOKEN"))
        )
        result = refresh(client, **vars(args))
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(
        json.dumps(
            {
                "status": "complete",
                "films": len(result["films"]),
                "last_successful_refresh": result["last_successful_refresh"],
            }
        )
    )
    return 0


def _command(value: str) -> list[str]:
    result = json.loads(value)
    if (
        not isinstance(result, list)
        or not result
        or not all(isinstance(item, str) for item in result)
    ):
        raise argparse.ArgumentTypeError("Export command must be a nonempty JSON string array")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
