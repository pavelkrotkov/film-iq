"""Private server-rendered FilmIQ UI, reusing the existing discovery read contract."""

import json
import sqlite3
from pathlib import Path
from urllib.parse import parse_qs

from film_iq.discovery_command import discovery_command
from film_iq.web_data import films, filters, select
from film_iq.web_detail import detail
from film_iq.web_render import browse, layout

# Browser copies have no longer retention lease than the live evidence.
# Tailnet HTTPS supplies transport/authentication; these headers protect pages.
HEADERS = [
    ("Cache-Control", "no-store"),
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "no-referrer"),
    (
        "Content-Security-Policy",
        "default-src 'none'; style-src 'self'; img-src https://www.themoviedb.org; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
    ),
]


class Application:
    def __init__(
        self,
        database: Path,
        cohort: Path | list[Path],
        snapshot: Path | None = None,
        catalog: Path | None = None,
    ):
        self.database, self.cohort = database, cohort
        self.snapshot, self.catalog = snapshot, catalog

    def report(self) -> dict:
        # Recheck accepted revisions and provider retention on every request.
        # A long-running UI must not freeze rights-expired facts at startup.
        return json.loads(
            discovery_command(
                self.cohort, self.snapshot, self.database, "json", catalog=self.catalog
            )
        )

    def __call__(self, environ, start_response):
        try:
            status, body, content_type = self.get(environ)
        except (OSError, ValueError, KeyError, TypeError, sqlite3.Error):
            # Errors describe unavailable input, never an empty or removed catalog.
            # Do not disclose private filesystem paths or response contents.
            status, body, content_type = (
                "503 Service Unavailable",
                layout(
                    "Source unavailable",
                    '<section class="empty"><h1>Film data is temporarily unavailable</h1><p>The source inputs could not be read. This does not mean your films disappeared. Check the private server inputs, then retry.</p></section>',
                ),
                "text/html",
            )
        payload = body.encode("utf-8")
        start_response(
            status,
            [
                *HEADERS,
                ("Content-Type", content_type + "; charset=utf-8"),
                ("Content-Length", str(len(payload))),
            ],
        )
        return [] if environ["REQUEST_METHOD"] == "HEAD" else [payload]

    def get(self, environ):
        if environ["REQUEST_METHOD"] not in {"GET", "HEAD"}:
            return "405 Method Not Allowed", "Use GET to browse films.", "text/plain"
        path = environ.get("PATH_INFO", "/")
        if path == "/style.css":
            return "200 OK", Path(__file__).with_name("web.css").read_text(), "text/css"
        report = self.report()
        if path == "/health":
            return "200 OK", "FilmIQ source inputs readable\n", "text/plain"
        return self.page(path, environ.get("QUERY_STRING", ""), report)

    def page(self, path: str, query: str, report: dict):
        try:
            values = filters(parse_qs(query, max_num_fields=20))
        except ValueError:
            return "400 Bad Request", "Unknown film filters.", "text/plain"
        items = films(report, values["order"])
        if path == "/":
            return (
                "200 OK",
                browse(report, select(items, values), values, len(items)),
                "text/html",
            )
        item = next((item for item in items if path == f"/films/{item['tmdb_id']}"), None)
        if item is not None:
            return "200 OK", detail(report, item), "text/html"
        return (
            "404 Not Found",
            layout(
                "Not found",
                '<section class="empty"><h1>Film not found</h1><p>This is not a currently accepted, reviewed film in your selected sources.</p><a href="/">Return to discovery</a></section>',
            ),
            "text/html",
        )
