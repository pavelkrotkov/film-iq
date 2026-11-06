"""Import a synthetic external film into an isolated Kaneo project."""

import argparse
import http.cookiejar
import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from enrichment import FilmMetadata, FixtureSource, enrich
from kaneo_smoke import call, ensure_field


class KaneoBackend:
    """Backfill fields with no value row; preserve explicit empty values.

    Run a single worker without concurrent edits: the value API has no
    compare-and-swap for these updates.
    """

    def __init__(self, base: str, project: str, cookie_file: Path):
        self.base, self.project = base, project
        cookies = http.cookiejar.MozillaCookieJar(str(cookie_file))
        cookies.load(ignore_discard=True)
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
        self.fields = {
            "identity": ensure_field(
                self.opener, base, project, "POC Synthetic External ID", "text"
            ),
            "year": ensure_field(self.opener, base, project, "POC Year", "number"),
            "genre": ensure_field(self.opener, base, project, "POC Genre", "text"),
            "availability": ensure_field(
                self.opener, base, project, "POC Synthetic Availability", "text"
            ),
        }

    def ensure_film(self, film: FilmMetadata) -> str:
        rows = call(self.opener, self.base, f"/custom-field/project/{self.project}/values")
        matches = [
            r["taskId"]
            for r in rows
            if r["fieldId"] == self.fields["identity"] and r["value"] == str(film.source_id)
        ]
        if len(matches) > 1:
            raise ValueError("duplicate synthetic external IDs")
        metadata = {
            "year": str(film.year) if film.year is not None else "",
            "genre": film.genre or "",
        }
        if matches:
            task = matches[0]
            existing = {r["fieldId"]: r["value"] for r in rows if r["taskId"] == task}
            for key, value in metadata.items():
                if value and self.fields[key] not in existing:
                    self._set(task, self.fields[key], value)
            return task
        fields = [{"fieldId": self.fields["identity"], "value": str(film.source_id)}]
        fields.extend(
            {"fieldId": self.fields[key], "value": value}
            for key, value in metadata.items()
            if value
        )
        return call(
            self.opener,
            self.base,
            f"/task/{self.project}",
            {
                "title": film.title,
                "description": film.synopsis,
                "priority": "no-priority",
                "status": "to-do",
                "customFields": fields,
            },
        )["id"]

    def _set(self, task: str, field: str, value: str) -> None:
        call(
            self.opener,
            self.base,
            "/custom-field/value",
            {"taskId": task, "fieldId": field, "value": value},
            "PUT",
        )

    def set_availability(self, record_id: str, value: dict) -> None:
        self._set(record_id, self.fields["availability"], json.dumps(value, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:15173")
    parser.add_argument("--project", required=True)
    parser.add_argument("--cookie-file", required=True, type=Path)
    parser.add_argument("--fixture-id", type=int, required=True)
    args = parser.parse_args()
    backend = KaneoBackend(args.base.rstrip("/"), args.project, args.cookie_file)
    result = enrich(FixtureSource(), backend, args.fixture_id, datetime.now(UTC))
    print(f"Synthetic record: {result}")
