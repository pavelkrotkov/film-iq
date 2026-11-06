"""Exercise the real bearer importer inside a new, isolated fictional server."""

import http.cookiejar
import json
import os
import time
import urllib.error
import urllib.request

from direct_review_links_check import fixtures
from kaneo_direct_reviews import FIELD, IDENTITY_FIELD, api_key_opener, import_reviews
from kaneo_smoke import call, ensure_field
from kaneo_watched_refresh import prepare

BASE = "http://kaneo:5173"
stage = "readiness"


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
    status = call(setup, BASE, f"/column/{project}")[0]["slug"]
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
    stage = "denial"
    try:
        call(urllib.request.build_opener(urllib.request.ProxyHandler({})), BASE, f"/task/{task}")
    except urllib.error.HTTPError as error:
        assert error.code in (401, 403)
    else:
        raise AssertionError("Fictional server allowed an unauthenticated read")
    print("Fictional real-server key, preview, import, retry, clear and denial checks passed")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Avoid printing URLs, request headers, keys or server-provided details.
        code = f" HTTP {error.code}" if isinstance(error, urllib.error.HTTPError) else ""
        raise SystemExit(
            f"Fictional bearer check failed at {stage}: {type(error).__name__}{code}"
        ) from None
