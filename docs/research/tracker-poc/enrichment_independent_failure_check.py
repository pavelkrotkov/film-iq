"""Verify independent film persistence when the fictional provider fails."""

from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from traceback import format_exception
from typing import cast
from unittest.mock import patch

import kaneo_enrich
from cache_vertical_check import FakeKaneo, FakeYouTrack
from enrichment import AvailabilityRefreshError, FixtureSource, enrich
from youtrack_client import YouTrackClient
from youtrack_enrich import YouTrackFixtureBackend, custom_value


class FailedAvailability(FixtureSource):
    def availability(self, source_id: int) -> None:
        raise RuntimeError("fictional provider failure with sensitive detail")


def main() -> None:
    now = datetime(2026, 11, 6, tzinfo=UTC)

    class BadBackend:
        def __init__(self, value: str | None = None):
            self.value = value

        def ensure_film(self, film):
            if self.value is None:
                raise ValueError("fictional backend unavailable")
            return self.value

        def set_availability(self, record_id, value):
            raise AssertionError("availability was written")

    with patch.object(FixtureSource, "film", side_effect=AssertionError("source was called")):
        try:
            enrich(FixtureSource(), BadBackend(), 42, datetime(2026, 11, 6))
        except ValueError as error:
            assert "timezone-aware" in str(error)
        else:
            raise AssertionError("A naive timestamp was accepted")

    for bad_value in (None, "", "  "):
        try:
            enrich(FailedAvailability(), BadBackend(bad_value), 42, now)
        except ValueError as error:
            assert "Film saved" not in str(error)
            assert not isinstance(error, AvailabilityRefreshError)
        else:
            raise AssertionError("Unconfirmed film persistence was reported as saved")

    kaneo, youtrack = FakeKaneo(), FakeYouTrack()
    with (
        patch.object(kaneo_enrich, "call", side_effect=kaneo.call),
        patch.object(kaneo_enrich, "ensure_field", side_effect=lambda _o, _b, _p, name, *_: name),
        patch.object(kaneo_enrich.http.cookiejar, "MozillaCookieJar"),
        patch.object(kaneo_enrich.urllib.request, "build_opener", return_value=object()),
    ):
        backends = (
            kaneo_enrich.KaneoBackend("http://fixture.invalid", "fictional", Path("fictional")),
            YouTrackFixtureBackend(cast(YouTrackClient, youtrack)),
        )
        for index, backend in enumerate(backends):
            try:
                enrich(FailedAvailability(), backend, 42, now)
            except AvailabilityRefreshError as error:
                record = error.record_id
                assert isinstance(error.source_error, RuntimeError)
                assert "sensitive detail" not in str(error)
                assert "sensitive detail" not in "".join(format_exception(error))
                assert error.__suppress_context__
            else:
                raise AssertionError("Availability failure was not reported")

            if index == 0:
                assert len(kaneo.records) == 1
                assert kaneo.records[record]["description"] == "Synthetic source synopsis."
                assert not any(row["fieldId"] == "POC Synthetic Availability" for row in kaneo.rows)
                kaneo.records[record]["description"] = "User-maintained synopsis"
                next(row for row in kaneo.rows if row["fieldId"] == "POC Genre")["value"] = (
                    "User genre"
                )
                preferences = deepcopy(kaneo.preferences)
            else:
                assert len(youtrack.records) == 1
                assert youtrack.records[record]["description"] == "Synthetic source synopsis."
                assert custom_value(youtrack.records[record], "FilmIQ Provider Observation") is None
                youtrack.request(
                    f"issues/{record}",
                    body={
                        "description": "User-maintained synopsis",
                        "customFields": [{"name": "FilmIQ Genre", "value": "User genre"}],
                    },
                )
                preferences = deepcopy(youtrack.preferences)

            assert enrich(FixtureSource(), backend, 42, now) == record
            if index == 0:
                assert len(kaneo.records) == 1
                assert kaneo.records[record]["description"] == "User-maintained synopsis"
                assert (
                    next(row["value"] for row in kaneo.rows if row["fieldId"] == "POC Genre")
                    == "User genre"
                )
                assert kaneo.preferences == preferences
                availability = next(
                    row["value"]
                    for row in kaneo.rows
                    if row["fieldId"] == "POC Synthetic Availability"
                )
            else:
                assert len(youtrack.records) == 1
                assert youtrack.records[record]["description"] == "User-maintained synopsis"
                assert custom_value(youtrack.records[record], "FilmIQ Genre") == "User genre"
                assert youtrack.preferences == preferences
                availability = deepcopy(
                    custom_value(youtrack.records[record], "FilmIQ Provider Observation")
                )
            try:
                enrich(FailedAvailability(), backend, 42, now)
            except AvailabilityRefreshError as error:
                assert error.record_id == record
            else:
                raise AssertionError("Repeated provider failure was not reported")
            if index == 0:
                assert (
                    next(
                        row["value"]
                        for row in kaneo.rows
                        if row["fieldId"] == "POC Synthetic Availability"
                    )
                    == availability
                )
            else:
                assert (
                    custom_value(youtrack.records[record], "FilmIQ Provider Observation")
                    == availability
                )
    print("Both fictional adapters save film metadata despite provider failure and retry safely")


if __name__ == "__main__":
    main()
