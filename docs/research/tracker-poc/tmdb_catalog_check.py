"""Fictional checks for the task-scoped, read-only Kaneo catalog endpoint."""

import json
import urllib.error
from datetime import UTC, datetime, timedelta
from email.message import Message
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from tmdb_live import app


def invoke(application, path, *, cookie="fictional-session", origin="http://localhost:15174"):
    result = {}

    def start(status, headers):
        result.update(status=status, headers=dict(headers))

    result["body"] = json.loads(
        b"".join(
            application(
                {
                    "REQUEST_METHOD": "GET",
                    "PATH_INFO": path,
                    "HTTP_ORIGIN": origin,
                    "HTTP_COOKIE": cookie,
                    "wsgi.input": BytesIO(),
                },
                start,
            )
        )
    )
    return result


def main():
    policy = {
        "version": 1,
        "allowed_ids": [42],
        "destinations": ["api.themoviedb.org", "image.tmdb.org"],
    }
    task = {"id": "fixture-1", "title": "Fictional Film"}
    row = {"taskId": "fixture-1", "fieldName": "POC TMDB ID", "fieldType": "text", "value": "42"}
    rows = [row]
    calls = []
    reads = []

    def upstream(path, cookie):
        assert cookie == "fictional-session"
        calls.append(path)
        return task if path == "/task/fixture-1" else rows

    def catalog(path, identity, title):
        reads.append((path, identity, title))
        if path == Path("/fictional/catalog") and identity == 42 and title == "Fictional Film":
            return {"tmdb_id": 42, "title": "Fictional Film", "source": "Reviewed display catalog"}
        return None

    def no_live(_):
        raise AssertionError("catalog must never contact the live metadata reader")

    application = app(
        no_live,
        lambda _: "fictional-user",
        lambda: policy,
        upstream,
        lambda: Path("/fictional/catalog"),
        catalog,
    )
    result = invoke(application, "/catalog/fixture-1")
    assert result["status"] == "200 OK" and result["body"]["tmdb_id"] == 42
    assert result["headers"]["Cache-Control"] == "no-store"
    assert calls == ["/task/fixture-1", "/custom-field/task/fixture-1"]
    assert len(reads) == 1

    def denied(_path, _cookie):
        raise urllib.error.HTTPError("http://fixture.invalid", 403, "denied", Message(), None)

    denied_app = app(
        no_live,
        lambda _: "fictional-user",
        lambda: policy,
        denied,
        lambda: Path("/fictional/catalog"),
        catalog,
    )
    assert invoke(denied_app, "/catalog/fixture-1")["status"] == "404 Not Found"
    assert len(reads) == 1
    assert (
        invoke(application, "/catalog/fixture-1", origin="https://unrelated.invalid")["status"]
        == "403 Forbidden"
    )
    assert invoke(application, "/catalog/../fixture-1")["status"] == "404 Not Found"
    assert invoke(app(no_live), "/catalog/fixture-1", cookie="")["status"] == "401 Unauthorized"
    for bad_rows in (
        [],
        [row, row],
        [{**row, "taskId": "another"}],
        [{**row, "fieldType": "number"}],
        [{**row, "value": "43"}],
        [{**row, "value": "042"}],
        [{**row, "value": "2147483648"}],
    ):
        rows = bad_rows
        assert invoke(application, "/catalog/fixture-1")["status"] == "404 Not Found"
    assert len(reads) == 1
    rows = [row]
    task["title"] = "Different Fictional Film"
    assert invoke(application, "/catalog/fixture-1")["status"] == "404 Not Found"
    assert len(reads) == 2

    task["title"] = "Fictional Film"
    now = datetime.now(UTC)
    snapshot = {
        "version": "reviewed-display-v1",
        "observed_at": (now - timedelta(days=1)).isoformat(),
        "expires_at": (now + timedelta(days=1)).isoformat(),
        "attribution": "Fictional attribution",
        "records": [
            {
                "tmdb_id": 42,
                "title": "Fictional Film",
                "original_title": "Fictional Original",
                "directors": ["Fictional Director"],
                "release_date": "2001-02-03",
                "runtime_minutes": 100,
                "reviewer": "private reviewer",
                "evidence": ["private evidence"],
            }
        ],
    }
    integrated = app(
        no_live,
        lambda _: "fictional-user",
        lambda: policy,
        upstream,
        lambda: Path("/fictional/catalog"),
    )
    with patch.object(Path, "read_text", return_value=json.dumps(snapshot)):
        result = invoke(integrated, "/catalog/fixture-1")
    assert result["status"] == "200 OK"
    assert (
        result["body"]["year"] == 2001 and result["body"]["attribution"] == "Fictional attribution"
    )
    assert "reviewer" not in result["body"] and "evidence" not in result["body"]
    print("Fictional task visibility, approved identity and catalog-only checks passed")


if __name__ == "__main__":
    main()
