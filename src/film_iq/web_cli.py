"""Run the single-user FilmIQ WSGI application on a loopback HTTP listener."""

import argparse
from pathlib import Path

from film_iq.web import Application


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--cohort", type=Path, action="append", required=True)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8770)
    parser.add_argument("--public-origin", help="Browser-facing origin, including HTTPS proxy port")
    args = vars(parser.parse_args(argv))
    host, port = args.pop("host"), args.pop("port")
    args["public_origin"] = args["public_origin"] or f"http://{host}:{port}"
    from waitress import serve

    serve(Application(**args), host=host, port=port, threads=1, max_request_body_size=16384)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
