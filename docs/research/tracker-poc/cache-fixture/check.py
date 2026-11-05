"""Check fictional cache persistence, failure handling and endpoint authorization."""

import io
import json
import tempfile
from datetime import UTC, datetime, timedelta
from importlib import import_module
from pathlib import Path
from unittest.mock import patch

import kaneo_bridge
from fictional_cache import POLICY, read, seed
from tmdb_cache import write_film

youtrack_app = import_module("fixture_bridge").app

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / ".cache/tracker-poc"
NOW = datetime.now(UTC) - timedelta(seconds=3)


def invoke(app, path, *, method="GET", origin="http://localhost:15174", body=None, token=None):
    raw = json.dumps(body).encode() if body is not None else b""
    env = {
        "PATH_INFO": path,
        "REQUEST_METHOD": method,
        "HTTP_ORIGIN": origin,
        "wsgi.input": io.BytesIO(raw),
        "CONTENT_LENGTH": str(len(raw)),
        "HTTP_AUTHORIZATION": token or "",
        "HTTP_COOKIE": "fixture",
    }
    status = []
    data = b"".join(app(env, lambda s, _h: status.append(s)))
    return int(status[0].split()[0]), json.loads(data)


def main():
    with tempfile.TemporaryDirectory(prefix="fictional-cache-check-", dir=BASE) as temp:
        directory = Path(temp)
        seed(directory, NOW)
        before = read(directory, 900000001, NOW)
        assert before and before["availability"]["offers"][0]["provider"] == "Fixture Stream"
        assert read(directory, 7, NOW) is None
        assert read(directory, 900000001, POLICY.expires_at + timedelta(seconds=1)) is None
        partial = {
            **before,
            "availability": {
                "status": "partial",
                "checked_at": (NOW + timedelta(seconds=1)).isoformat(),
                "offers": [],
            },
        }
        write_film(
            directory / "cache",
            POLICY,
            partial,
            NOW + timedelta(seconds=1),
            NOW + timedelta(seconds=1),
            authority=directory / "authority.json",
        )
        after_partial = read(directory, 900000001, NOW + timedelta(seconds=2))
        assert after_partial and after_partial["availability"] == before["availability"]
        fixture = youtrack_app(
            "fixture-only-token",
            cached=lambda ident: read(directory, ident, NOW + timedelta(seconds=2)),
        )
        assert invoke(fixture, "/metadata", method="POST", body={"tmdb_id": 900000001})[0] == 401
        assert (
            invoke(
                fixture,
                "/metadata",
                method="POST",
                body={"tmdb_id": 123},
                token="Bearer fixture-only-token",
            )[0]
            == 403
        )
        status, data = invoke(
            fixture,
            "/metadata",
            method="POST",
            body={"tmdb_id": 900000001},
            token="Bearer fixture-only-token",
        )
        assert status == 200 and data["title"] == before["title"]
        broken = youtrack_app("fixture-only-token", cached=lambda _ident: None)
        assert (
            invoke(
                broken,
                "/metadata",
                method="POST",
                body={"tmdb_id": 900000001},
                token="Bearer fixture-only-token",
            )[0]
            == 404
        )
        after_failure = read(directory, 900000001, NOW + timedelta(seconds=2))
        assert after_failure and after_failure["availability"] == before["availability"]

        def upstream(path, _cookie):
            if path.startswith("/task/"):
                return {"id": "fixture", "projectId": "synthetic"}
            return [
                {
                    "fieldName": "POC TMDB ID",
                    "fieldType": "text",
                    "taskId": "fixture",
                    "value": "900000001",
                }
            ]

        kaneo = kaneo_bridge.app("synthetic", directory)
        with (
            patch.object(kaneo_bridge, "current_user", return_value="fixture-user"),
            patch.object(kaneo_bridge, "upstream", side_effect=upstream),
        ):
            assert invoke(kaneo, "/cache/fixture")[0] == 200
            assert invoke(kaneo, "/cache/fixture", origin="http://other.invalid")[0] == 404
            assert invoke(kaneo_bridge.app("other", directory), "/cache/fixture")[0] == 404
        with patch.object(kaneo_bridge, "current_user", side_effect=PermissionError):
            assert invoke(kaneo, "/cache/fixture")[0] == 404
    print("Fictional cache, partial response, expiry and authorization checks passed")


if __name__ == "__main__":
    main()
