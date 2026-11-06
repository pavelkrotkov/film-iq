"""Exercise the real bearer importer inside a new, isolated fictional server."""

import http.cookiejar
import json
import os
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime

from direct_review_links_check import fixtures
from enrichment import FixtureSource, enrich
from kaneo_direct_reviews import FIELD, IDENTITY_FIELD, api_key_opener, import_reviews
from kaneo_enrich import KaneoBackend
from kaneo_smoke import call, ensure_field
from kaneo_watched_refresh import prepare
from kaneo_watchlist_auth_check import check as check_watchlist_auth

BASE = "http://kaneo:5173"
stage = "readiness"


class FixtureOffers(FixtureSource):
    def availability(self, source_id):
        value = super().availability(source_id)
        assert value is not None
        value["results"]["US"]["buy"] = [{"provider_id": 103, "provider_name": "Fixture Purchase"}]
        return value


def lifecycle_round_trip(opener, project):
    """Exercise real worker/API transitions on a distinct fictional task."""
    backend = KaneoBackend.__new__(KaneoBackend)
    backend.base, backend.project, backend.opener = BASE, project, opener
    backend.fields = {
        "identity": ensure_field(opener, BASE, project, "POC Synthetic External ID", "text"),
        "year": ensure_field(opener, BASE, project, "POC Year", "number"),
        "genre": ensure_field(opener, BASE, project, "POC Genre", "text"),
        "availability": ensure_field(opener, BASE, project, "POC Synthetic Availability", "text"),
    }
    task_id = enrich(FixtureOffers(), backend, 4242, datetime.now(UTC))

    def fields():
        rows = call(opener, BASE, f"/custom-field/task/{task_id}")
        values = {row["fieldId"]: row["value"] for row in rows}
        assert len(values) == len(rows), "duplicate fictional custom fields"
        return values

    initial = fields()
    assert initial[backend.fields["identity"]] == "4242"
    assert initial[backend.fields["year"]] == "2001"
    assert initial[backend.fields["genre"]] == "Drama"
    offers = json.loads(initial[backend.fields["availability"]])
    assert offers["subscription"] == ["Fixture Stream"]
    assert offers["rent"] == ["Fixture Rental"]
    assert offers["buy"] == ["Fixture Purchase"]

    for state in ("to-do", "in-progress", "in-review", "archived", "in-progress"):
        call(opener, BASE, f"/task/status/{task_id}", {"status": state}, "PUT")
        record = call(opener, BASE, f"/task/{task_id}")
        assert record["id"] == task_id and record["status"] == state
        assert record["title"] == "Synthetic imported film 4242"
        assert record["description"] == "Synthetic source synopsis."
        assert fields() == initial, "fictional custom fields changed during transition"
        board = call(opener, BASE, f"/task/tasks/{project}?limit=100&page=1")
        buckets = board["data"]
        archived = [row["id"] for row in buckets["archivedTasks"]]
        active = [row["id"] for column in buckets["columns"] for row in column["tasks"]]
        assert (task_id in archived) == (state == "archived")
        assert (task_id in active) == (state != "archived")


def main():
    global stage
    # This fresh API-only session exists solely in the fictional container's
    # memory; it is neither loaded from nor written to a browser or file.
    jar = http.cookiejar.CookieJar()
    setup = urllib.request.build_opener(
        urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(jar)
    )
    for attempt in range(60):
        try:
            call(setup, BASE, "/auth/get-session")
            break
        except (urllib.error.URLError, OSError, ValueError):
            if attempt == 59:
                raise RuntimeError("Fictional server did not start") from None
            time.sleep(1)
    stage = "signup"
    call(
        setup,
        BASE,
        "/auth/sign-up/email",
        {
            "name": "Fictional API Test",
            "email": "fictional-key@example.invalid",
            "password": os.environ["FIXTURE_PASSWORD"],
        },
    )
    stage = "workspace"
    workspace = call(
        setup, BASE, "/auth/organization/create", {"name": "Fictional", "slug": "fictional"}
    )
    stage = "project"
    project = call(
        setup,
        BASE,
        "/project",
        {
            "name": "Fictional Films",
            "workspaceId": workspace["id"],
            "slug": "fictional-films",
            "icon": "🎬",
        },
    )["id"]
    stage = "fields"
    identity = ensure_field(setup, BASE, project, IDENTITY_FIELD, "text")
    review = ensure_field(setup, BASE, project, FIELD, "text")
    columns = call(setup, BASE, f"/column/{project}")
    names = {"to-do": "Discovery", "in-progress": "Evaluation", "in-review": "Watchlist"}
    assert names.keys() <= {column["slug"] for column in columns}
    for column in columns:
        if column["slug"] in names:
            call(setup, BASE, f"/column/{column['id']}", {"name": names[column["slug"]]}, "PUT")
    observed = {
        column["slug"]: column["name"] for column in call(setup, BASE, f"/column/{project}")
    }
    assert all(observed.get(slug) == name for slug, name in names.items())
    status = "to-do"
    stage = "task"
    task = call(
        setup,
        BASE,
        f"/task/{project}",
        {
            "title": "Fictional Title",
            "description": "User-entered fictional synopsis",
            "priority": "no-priority",
            "status": status,
            "customFields": [{"fieldId": identity, "value": "42"}],
        },
    )["id"]
    stage = "key"
    result = call(setup, BASE, "/auth/api-key/create", {"name": "fictional-review-import"})
    key = result.get("key")
    if not isinstance(key, str) or not key:
        raise RuntimeError("Fictional key issuance returned no key")
    owner_id = call(setup, BASE, "/auth/get-session")["user"]["id"]
    stage = "watchlist-auth"
    check_watchlist_auth(BASE, jar, owner_id, project, os.environ["FIXTURE_PASSWORD"])
    # Drop the API-only bootstrap session before any importer operation.
    jar.clear()
    del setup, jar, result
    stage = "import"
    opener = api_key_opener(key)
    del key
    stage = "owner"
    assert call(opener, BASE, "/user/me")["id"] == owner_id
    stage = "watched"
    old_time = "2026-11-05T12:00:00+00:00"
    new_time = "2026-11-06T12:00:00+00:00"
    prior = {"source": "Movary", "observed_at": old_time, "films": {}, "unresolved_history": []}
    sidecar = {
        "version": "tracker-poc-movary-watched-v1",
        "project_id": project,
        "users": {owner_id: prior},
    }
    snapshot = {
        "version": "movary-personal-v1",
        "last_successful_refresh": new_time,
        "films": [{"tmdb_id": 42, "watched": True}],
        "provenance": {
            "api": {
                "played": [{"movie": {"ids": {"tmdb": 42, "movary": 142}}, "watchDates": []}],
                "history": [],
                "watchlist": [],
            },
            "history_csv": [],
        },
    }
    watched_status = {"stale": False, "last_successful_refresh": new_time}
    refreshed = prepare(opener, BASE, project, sidecar, snapshot, watched_status)
    assert set(refreshed["users"][owner_id]["films"]) == {"42"}
    stage = "preview"
    manifest, source = fixtures()
    expected = {"pending": 1, "skipped": 0, "conflicts": 0, "written": 0}
    assert import_reviews(opener, BASE, project, manifest, source) == expected
    stage = "apply"
    expected = {"pending": 0, "skipped": 0, "conflicts": 0, "written": 1}
    assert import_reviews(opener, BASE, project, manifest, source, apply=True) == expected
    stage = "retry"
    expected = {"pending": 0, "skipped": 1, "conflicts": 0, "written": 0}
    assert import_reviews(opener, BASE, project, manifest, source, apply=True) == expected
    value = next(
        row["value"]
        for row in call(opener, BASE, f"/custom-field/task/{task}")
        if row["fieldId"] == review
    )
    assert json.loads(value)["links"][0]["url"] == "https://example.com/review"
    record = call(opener, BASE, f"/task/{task}")
    assert record["description"] == "User-entered fictional synopsis" and record["status"] == status
    stage = "clear"
    call(
        opener, BASE, "/custom-field/value", {"taskId": task, "fieldId": review, "value": ""}, "PUT"
    )
    assert import_reviews(opener, BASE, project, manifest, source, apply=True) == expected
    assert (
        next(
            row["value"]
            for row in call(opener, BASE, f"/custom-field/task/{task}")
            if row["fieldId"] == review
        )
        == ""
    )
    stage = "lifecycle"
    lifecycle_round_trip(opener, project)
    stage = "denial"
    try:
        call(urllib.request.build_opener(urllib.request.ProxyHandler({})), BASE, f"/task/{task}")
    except urllib.error.HTTPError as error:
        assert error.code in (401, 403)
    else:
        raise AssertionError("Fictional server allowed an unauthenticated read")
    print("Fictional real-server key, import, lifecycle, metadata and denial checks passed")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Avoid printing URLs, request headers, keys or server-provided details.
        code = f" HTTP {error.code}" if isinstance(error, urllib.error.HTTPError) else ""
        raise SystemExit(
            f"Fictional bearer check failed at {stage}: {type(error).__name__}{code}"
        ) from None
