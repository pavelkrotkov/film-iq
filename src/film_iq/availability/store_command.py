"""Local rights-reviewed offer import, state inspection and explicit retention purge.

Policy registration records an explicit review; it never infers permission from
a public URL. Import uses that registered policy and never fetches the network.
"""

import argparse
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from film_iq.availability.codec import decode_fetch, decode_policy
from film_iq.availability.ledger import save_fetch
from film_iq.availability.policies import purge_source, record_policy
from film_iq.availability.state import read_state
from film_iq.storage import connect, migrate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("policy", "import", "state", "purge"))
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--input", type=Path, help="Reviewed policy JSON or scoped Fetch JSON")
    parser.add_argument("--source", help="Exact source for purge preview/execution")
    parser.add_argument("--now", required=True, help="Explicit timezone-aware assessment time")
    parser.add_argument("--execute", action="store_true", help="Execute named-source purge")
    args = parser.parse_args(argv)
    try:
        with closing(connect(args.database)) as db:
            migrate(db)
            output = _run(db, args)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, sqlite3.Error) as error:
        parser.error(str(error))
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def _run(db, args):
    now = datetime.fromisoformat(args.now)
    if args.command == "purge":
        if not args.source:
            raise ValueError("purge requires an explicit source")
        return {"purge": purge_source(db, args.source, now, execute=args.execute)}
    if args.input is None:
        raise ValueError("policy/import/state requires an explicit input file")
    payload = args.input.read_text()
    if args.command == "policy":
        policy = decode_policy(payload)
        record_policy(db, policy, now)
        return {"source": policy.source, "policy_recorded": True}
    fetch = decode_fetch(payload)
    if args.command == "import":
        return {"fetch_id": save_fetch(db, fetch, now)}
    return read_state(db, fetch, now)


if __name__ == "__main__":
    raise SystemExit(main())
