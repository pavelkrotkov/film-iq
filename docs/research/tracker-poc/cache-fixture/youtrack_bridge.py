"""Serve only cached synthetic records in the YouTrack network namespace."""

from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, make_server

from fictional_cache import read

app = import_module("fixture_bridge").app


class Silent(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    directory = Path("/opt/filmiq/fictional-cache")
    with make_server(
        "127.0.0.1",
        15176,
        app("fixture-only-token", cached=lambda ident: read(directory, ident, datetime.now(UTC))),
        handler_class=Silent,
    ) as server:
        server.serve_forever()
