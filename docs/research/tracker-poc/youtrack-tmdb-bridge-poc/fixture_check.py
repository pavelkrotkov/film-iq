"""Exercise the fixture handler through a local server and a fake YouTrack runtime."""

import json
import shutil
import subprocess
import threading
import urllib.error
import urllib.request
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, make_server

from fixture_bridge import app


class SilentHandler(WSGIRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


def check():
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node is required")
    application = app("fixture-only-token")
    with make_server("127.0.0.1", 0, application, handler_class=SilentHandler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}"
        try:
            request = urllib.request.Request(
                url + "/metadata",
                data=b'{"tmdb_id":11}',
                method="POST",
                headers={"Authorization": "Bearer fixture-only-token"},
            )
            try:
                urllib.request.urlopen(request, timeout=5)
            except urllib.error.HTTPError as error:
                assert error.code == 403
                assert json.load(error) == {"error": "Fixture ID not approved"}
            else:
                raise AssertionError("Non-fixture ID was accepted")
            result = subprocess.run(
                [node, str(Path(__file__).with_name("metadata_check.cjs"))],
                env={"PATH": "/usr/bin:/bin", "FIXTURE_BRIDGE_URL": url},
                check=True,
                capture_output=True,
                text=True,
            )
            print(result.stdout.strip())
        finally:
            server.shutdown()
            thread.join()


if __name__ == "__main__":
    check()
