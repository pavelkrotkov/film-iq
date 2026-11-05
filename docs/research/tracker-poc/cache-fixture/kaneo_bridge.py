"""Cache-only endpoint for visible tasks in one explicit fictional Kaneo project."""

import json
import re
import urllib.error
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote
from wsgiref.simple_server import WSGIRequestHandler, make_server

from fictional_cache import IDS, read
from preferences import current_user, upstream

ORIGIN = "http://localhost:15174"


def app(project: str, directory: Path):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", project):
        raise ValueError("Invalid fictional project")

    def application(environ, start):
        def send(status, value):
            body = json.dumps(value).encode()
            headers = [
                ("Content-Type", "application/json"),
                ("Cache-Control", "no-store"),
                ("Content-Length", str(len(body))),
                ("Vary", "Origin"),
            ]
            if environ.get("HTTP_ORIGIN") == ORIGIN:
                headers.extend(
                    [
                        ("Access-Control-Allow-Origin", ORIGIN),
                        ("Access-Control-Allow-Credentials", "true"),
                    ]
                )
            start(status, headers)
            return [body]

        match = re.fullmatch(r"/cache/([A-Za-z0-9_-]{1,200})", environ.get("PATH_INFO", ""))
        if (
            environ.get("HTTP_ORIGIN") != ORIGIN
            or environ.get("REQUEST_METHOD") != "GET"
            or not match
        ):
            return send("404 Not Found", {"error": "Not found"})
        task_id = match.group(1)
        try:
            current_user(environ)
            cookie = environ.get("HTTP_COOKIE", "")
            task = upstream("/task/" + quote(task_id, safe=""), cookie)
            rows = upstream("/custom-field/task/" + quote(task_id, safe=""), cookie)
            fields = [row for row in rows if row.get("fieldName") == "POC TMDB ID"]
            if (
                task.get("id") != task_id
                or task.get("projectId") != project
                or len(fields) != 1
                or fields[0].get("taskId") != task_id
                or fields[0].get("fieldType") != "text"
                or fields[0].get("value") not in {str(i) for i in IDS}
            ):
                return send("404 Not Found", {"error": "Fictional task unavailable"})
            result = read(directory, int(fields[0]["value"]), datetime.now(UTC))
            return (
                send("200 OK", result) if result else send("404 Not Found", {"error": "Cache miss"})
            )
        except (PermissionError, urllib.error.HTTPError):
            return send("404 Not Found", {"error": "Fictional task unavailable"})
        except (OSError, ValueError, TypeError):
            return send("503 Service Unavailable", {"error": "Fixture cache unavailable"})

    return application


class Silent(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--cache-directory", required=True, type=Path)
    args = parser.parse_args()
    with make_server(
        "127.0.0.1", 15179, app(args.project, args.cache_directory), handler_class=Silent
    ) as server:
        server.serve_forever()
