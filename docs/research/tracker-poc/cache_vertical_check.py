"""Offline fictional vertical check; this does not enable a production cache.

Both real adapter classes run against in-memory tracker transports. All cache
files are synthetic and confined to a new directory under the project cache.
The test-only view conversion below is not a deployed bridge or UI integration.
"""

import json
import subprocess
import sys
import tempfile
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import kaneo_enrich
from enrichment import FixtureSource, enrich
from tmdb_cache import initialize_authority, read_film, write_film
from youtrack_client import YouTrackClient
from youtrack_enrich import YouTrackFixtureBackend, custom_value
from youtrack_enrich_fixture_check import FakeClient

from film_iq.availability.tmdb import normalize
from film_iq.retention import CachePolicy

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / ".cache/tracker-poc"
START = datetime(2026, 1, 1, tzinfo=UTC)
POLICY = CachePolicy(
    "TMDB", True, "Fictional permission", "Fictional attribution", START + timedelta(days=30)
)


class FakeKaneo:
    """Only the routes used by the actual fixture adapter are implemented."""

    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {}
        self.rows: list[dict[str, str]] = []
        self.preferences = {"fictional-user": {"interest_score": 8, "watched_at": None}}

    def call(self, _opener, _base, path, payload=None, method=None):
        if path == "/custom-field/project/fictional/values" and method is None:
            return deepcopy(self.rows)
        if path == "/task/fictional" and method is None:
            assert payload is not None
            ident = f"task-{len(self.records) + 1}"
            self.records[ident] = {"title": payload["title"], "description": payload["description"]}
            self.rows.extend({"taskId": ident, **field} for field in payload["customFields"])
            return {"id": ident}
        if path == "/custom-field/value" and method == "PUT":
            assert payload is not None
            row = next(
                (
                    row
                    for row in self.rows
                    if row["taskId"] == payload["taskId"] and row["fieldId"] == payload["fieldId"]
                ),
                None,
            )
            if row is None:
                self.rows.append(dict(payload))
            else:
                row["value"] = payload["value"]
            return {}
        raise AssertionError(f"Unexpected fictional Kaneo request: {path}")


class FakeYouTrack(FakeClient):
    def request(self, path, *, query=None, body=None):
        result = super().request(path, query=query, body=body)
        if path == "issues" and body is not None:
            self.records[result["id"]]["customFields"].append(
                {"name": "FilmIQ Provider Observation", "value": None}
            )
        return result


class PartialSource(FixtureSource):
    def availability(self, source_id: int) -> dict:
        return {
            "id": source_id,
            "results": {"US": {"link": "https://example.invalid", "flatrate": [{}]}},
        }


class FailedSource(FixtureSource):
    def availability(self, source_id: int) -> None:
        raise RuntimeError("Fictional provider failure")


def fixture_payload(source: FixtureSource, now: datetime, ident: int = 42) -> dict[str, Any]:
    film = source.film(ident)
    observed = normalize(ident, source.availability(ident), now)
    return {
        "tmdb_id": ident,
        "title": film.title,
        "original_title": None,
        "synopsis": film.synopsis,
        "year": film.year,
        "genres": [film.genre] if film.genre else None,
        "directors": ["Fictional Director"],
        "poster_url": None,
        "imdb_title_url": None,
        "availability": {
            "status": observed.status,
            "checked_at": now.isoformat(),
            "provider_url": None,
            "offers": [
                {"provider": offer.provider, "kind": offer.kind} for offer in observed.offers
            ],
        },
    }


def visible_payload(cache: Path, authority: Path, now: datetime, ident: int = 42) -> dict[str, Any]:
    """Test-only conversion to the shape expected by existing UI filters."""
    record = read_film(cache, POLICY, ident, now, authority=authority)
    assert record is not None and record["metadata"] and record["availability"]
    metadata, availability = record["metadata"], record["availability"]
    return {
        "tmdb_id": ident,
        **metadata["data"],
        "availability": {**availability["data"], "checked_at": availability["observed_at"]},
    }


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(prefix="fictional-cache-vertical-", dir=FIXTURES) as directory:
        root = Path(directory)
        kaneo_transport, youtrack_transport = FakeKaneo(), FakeYouTrack()
        with (
            patch.object(kaneo_enrich, "call", side_effect=kaneo_transport.call),
            patch.object(
                kaneo_enrich, "ensure_field", side_effect=lambda _o, _b, _p, name, *_: name
            ),
            patch.object(kaneo_enrich.http.cookiejar, "MozillaCookieJar"),
            patch.object(kaneo_enrich.urllib.request, "build_opener", return_value=object()),
        ):
            backends = [
                kaneo_enrich.KaneoBackend("http://fixture.invalid", "fictional", Path("fictional")),
                YouTrackFixtureBackend(cast(YouTrackClient, youtrack_transport)),
            ]
            views = []
            for index, backend in enumerate(backends):
                cache, authority = root / f"cache-{index}", root / f"authority-{index}.json"
                initialize_authority(cache, authority, POLICY, START)
                record_id = enrich(FixtureSource(), backend, 42, START)
                write_film(
                    cache,
                    POLICY,
                    fixture_payload(FixtureSource(), START),
                    START,
                    START,
                    authority=authority,
                )
                if index == 0:
                    kaneo_transport.records[record_id]["description"] = "User fictional synopsis"
                    next(
                        row
                        for row in kaneo_transport.rows
                        if row["taskId"] == record_id and row["fieldId"] == "POC Genre"
                    )["value"] = "User fictional genre"
                    preferences = deepcopy(kaneo_transport.preferences)
                    tracker_observation = next(
                        row["value"]
                        for row in kaneo_transport.rows
                        if row["taskId"] == record_id
                        and row["fieldId"] == "POC Synthetic Availability"
                    )
                else:
                    youtrack_transport.records[record_id]["description"] = "User fictional synopsis"
                    youtrack_transport.request(
                        f"issues/{record_id}",
                        body={
                            "customFields": [
                                {"name": "FilmIQ Genre", "value": "User fictional genre"}
                            ]
                        },
                    )
                    preferences = deepcopy(youtrack_transport.preferences)
                    tracker_observation = deepcopy(
                        custom_value(
                            youtrack_transport.records[record_id], "FilmIQ Provider Observation"
                        )
                    )
                assert enrich(FixtureSource(), backend, 42, START) == record_id
                partial_time = START + timedelta(days=1)
                assert enrich(PartialSource(), backend, 42, partial_time) == record_id
                write_film(
                    cache,
                    POLICY,
                    fixture_payload(PartialSource(), partial_time),
                    partial_time,
                    partial_time,
                    authority=authority,
                )
                before = (cache / "42.json").read_bytes()
                try:
                    enrich(FailedSource(), backend, 42, partial_time)
                except RuntimeError:
                    pass
                else:
                    raise AssertionError("Fictional provider failure was not surfaced")
                assert (cache / "42.json").read_bytes() == before
                if index == 0:
                    assert len(kaneo_transport.records) == 1
                    assert (
                        kaneo_transport.records[record_id]["description"]
                        == "User fictional synopsis"
                    )
                    assert kaneo_transport.preferences == preferences
                    assert (
                        next(
                            row["value"]
                            for row in kaneo_transport.rows
                            if row["taskId"] == record_id and row["fieldId"] == "POC Genre"
                        )
                        == "User fictional genre"
                    )
                    assert (
                        next(
                            row["value"]
                            for row in kaneo_transport.rows
                            if row["taskId"] == record_id
                            and row["fieldId"] == "POC Synthetic Availability"
                        )
                        == tracker_observation
                    )
                else:
                    assert len(youtrack_transport.records) == 1
                    assert (
                        youtrack_transport.records[record_id]["description"]
                        == "User fictional synopsis"
                    )
                    assert youtrack_transport.preferences == preferences
                    assert (
                        custom_value(youtrack_transport.records[record_id], "FilmIQ Genre")
                        == "User fictional genre"
                    )
                    assert (
                        custom_value(
                            youtrack_transport.records[record_id], "FilmIQ Provider Observation"
                        )
                        == tracker_observation
                    )
                result = subprocess.run(
                    [
                        sys.executable,
                        str(Path(__file__).resolve()),
                        "--read-fixture",
                        str(cache),
                        str(authority),
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=15,
                )
                views.append(json.loads(result.stdout))
            node = subprocess.run(
                ["node", str(ROOT / "docs/research/tracker-poc/ui/cache_vertical_view_check.mjs")],
                input=json.dumps(views),
                capture_output=True,
                text=True,
                timeout=15,
                check=True,
            )
            assert "Fictional cache view filters passed" in node.stdout
    print("Fictional adapters, cache restart, failed/partial refresh and UI filters passed")


if __name__ == "__main__":
    if len(sys.argv) in (4, 5) and sys.argv[1] == "--read-fixture":
        cache, authority = map(Path, sys.argv[2:4])
        ident = int(sys.argv[4]) if len(sys.argv) == 5 else 42
        if not 0 < ident <= 2_147_483_647:
            raise SystemExit("Invalid fictional ID")
        if not cache.resolve().is_relative_to(
            FIXTURES.resolve()
        ) or not authority.resolve().is_relative_to(FIXTURES.resolve()):
            raise SystemExit("Expected project-local fictional paths")
        print(json.dumps(visible_payload(cache, authority, START + timedelta(days=1), ident)))
    elif len(sys.argv) == 1:
        main()
    else:
        raise SystemExit("Invalid arguments")
