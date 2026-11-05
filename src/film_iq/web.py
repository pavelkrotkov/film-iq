"""Private server-rendered FilmIQ UI, reusing the existing discovery read contract."""

import json
import sqlite3
from pathlib import Path
from secrets import token_urlsafe
from urllib.parse import parse_qs

from film_iq.discovery_command import discovery_command
from film_iq.dispositions import attach, read
from film_iq.web_data import films, filters, select
from film_iq.web_detail import detail
from film_iq.web_dispositions import VIEWS, actions, navigation, submit
from film_iq.web_forms import normalize_origin, read_form
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
        public_origin: str = "http://127.0.0.1:8770",
    ):
        self.database, self.cohort = database, cohort
        self.snapshot, self.catalog = snapshot, catalog
        self.public_origin = normalize_origin(public_origin)
        self.csrf_token = token_urlsafe(32)

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
        headers = [
            *HEADERS,
            ("Content-Type", content_type + "; charset=utf-8"),
            ("Content-Length", str(len(payload))),
        ]
        if status == "303 See Other":
            headers.append(("Location", body))
        start_response(status, headers)
        return [] if environ["REQUEST_METHOD"] == "HEAD" else [payload]

    def get(self, environ):
        if environ["REQUEST_METHOD"] == "POST":
            return self.post(environ)
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
            query_fields = parse_qs(query, max_num_fields=20)
            values = filters(query_fields)
        except ValueError:
            return "400 Bad Request", "Unknown film filters.", "text/plain"
        items = attach(films(report, values["order"]), read(self.database))
        if path in VIEWS:
            return self.collection(path, query_fields, report, items, values)
        item = next((item for item in items if path == f"/films/{item['tmdb_id']}"), None)
        if item is not None:
            return (
                "200 OK",
                detail(
                    report,
                    item,
                    actions=actions(item, self.csrf_token),
                    navigation=navigation(items, item["disposition"]),
                ),
                "text/html",
            )
        return (
            "404 Not Found",
            layout(
                "Not found",
                '<section class="empty"><h1>Film not found</h1><p>This is not a currently accepted, reviewed film in your selected sources.</p><a href="/">Return to discovery</a></section>',
            ),
            "text/html",
        )

    def collection(self, path, query_fields, report, items, values):
        view = VIEWS[path]
        if view != "discover" and "watched" not in query_fields:
            values["watched"] = "all"
        selected = select([item for item in items if item["disposition"] == view], values)
        body = browse(
            report,
            selected,
            values,
            len(items),
            csrf_token=self.csrf_token,
            view=view,
            navigation=navigation(items, view),
        )
        return "200 OK", body, "text/html"

    def post(self, environ):
        try:
            values = read_form(environ, self.csrf_token, self.public_origin)
        except PermissionError as error:
            return "403 Forbidden", str(error), "text/plain"
        except ValueError:
            return "400 Bad Request", "Invalid film form.", "text/plain"
        path = environ.get("PATH_INFO", "")
        # Acceptance is re-read at submission; forms never grant identity authority.
        item = next(
            (
                item
                for item in films(self.report())
                if path.startswith(f"/films/{item['tmdb_id']}/")
            ),
            None,
        )
        if item is None or path != f"/films/{item['tmdb_id']}/disposition":
            return "404 Not Found", "No accepted film action at this address.", "text/plain"
        return submit(self.database, item, values)
