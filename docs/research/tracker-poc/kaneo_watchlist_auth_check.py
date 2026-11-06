"""Exercise the watchlist WSGI gate against a fresh fictional Kaneo API.

The caller supplies only an API-created session in memory. The sidecar and
SQLite database are in memory; file-backed bridge restart is tested separately.
"""

import http.cookiejar
import io
import json
import sys
import types
import urllib.request
from pathlib import Path
from unittest.mock import patch

from kaneo_smoke import call

# The WSGI application is invoked directly; no HTTP server is started here.
waitress = types.ModuleType("waitress")
waitress.__dict__["serve"] = None
sys.modules["waitress"] = waitress
import preferences  # noqa: E402


def cookie(jar, base):
    request = urllib.request.Request(base + "/api/auth/get-session")
    jar.add_cookie_header(request)
    return request.get_header("Cookie", "")


def check(base, owner_jar, owner_id, project, password):
    preferences.KANEO = base + "/api"
    preferences.DATABASE = Path(":memory:")
    view = {
        "version": "tracker-poc-movary-watchlist-v1",
        "source": "Movary",
        "observed_at": "2026-11-06T12:00:00+00:00",
        "entries": [{"tmdb_id": 42, "title": "Fictional film", "added_at": None}],
    }
    stored = json.dumps(
        {
            "version": "tracker-poc-movary-watchlist-users-v1",
            "project_id": project,
            "users": {owner_id: view},
        }
    )

    class FictionalSidecar:
        def read_text(self):
            return stored

    def read(session, origin=preferences.ORIGIN):
        response = {}

        def start(status, headers):
            response.update(status=status, headers=dict(headers))

        body = b"".join(
            preferences.application(
                {
                    "REQUEST_METHOD": "GET",
                    "PATH_INFO": "/movary-watchlist/" + project,
                    "HTTP_ORIGIN": origin,
                    "HTTP_COOKIE": session,
                    "wsgi.input": io.BytesIO(),
                },
                start,
            )
        )
        return response, json.loads(body)

    with patch.object(preferences, "MOVARY_WATCHLIST_SIDECAR", FictionalSidecar()):
        owner_cookie = cookie(owner_jar, base)
        assert owner_cookie
        response, body = read(owner_cookie)
        assert response["status"] == "200 OK" and response["headers"]["Cache-Control"] == "no-store"
        assert body == {
            "status": "available",
            **{k: view[k] for k in ("source", "observed_at", "entries")},
        }
        assert read("")[0]["status"] == "403 Forbidden"
        assert read(owner_cookie, "http://unrelated.invalid")[0]["status"] == "403 Forbidden"

        other_jar = http.cookiejar.CookieJar()
        other = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(other_jar)
        )
        call(
            other,
            base,
            "/auth/sign-up/email",
            {
                "name": "Fictional outsider",
                "email": "outside@example.invalid",
                "password": password,
            },
        )
        outsider_cookie = cookie(other_jar, base)
        assert outsider_cookie
        response, body = read(outsider_cookie)
        assert response["status"] == "403 Forbidden" and "entries" not in body
        other_jar.clear()
