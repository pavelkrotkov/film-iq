"""Serve the synthetic-only provider on YouTrack's shared loopback interface."""

from wsgiref.simple_server import WSGIRequestHandler, make_server

from fixture_bridge import app


class SilentHandler(WSGIRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


if __name__ == "__main__":
    # Public test constant: protects the fixture protocol, not real credentials.
    with make_server(
        "127.0.0.1", 15176, app("fixture-only-token"), handler_class=SilentHandler
    ) as server:
        server.serve_forever()
