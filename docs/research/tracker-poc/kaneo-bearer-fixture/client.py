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
    # Drop the API-only bootstrap session before any importer operation.
    jar.clear()
    del setup, jar, result
    stage = "import"
    opener = api_key_opener(key)
    del key
    manifest, source = fixtures()
    expected = {"pending": 1, "skipped": 0, "conflicts": 0, "written": 0}
    assert import_reviews(opener, BASE, project, manifest, source) == expected
    expected = {"pending": 0, "skipped": 0, "conflicts": 0, "written": 1}
    assert import_reviews(opener, BASE, project, manifest, source, apply=True) == expected
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
