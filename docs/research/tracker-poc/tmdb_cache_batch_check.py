"""Deterministic fictional tests; no network and no real film data."""

import hashlib
import io
import json
import tempfile
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from email.message import Message
from pathlib import Path
from unittest.mock import patch

import tmdb_cache_batch as batch

IDS = set(range(1001, 1131))


def result(ident, *, expired=False):
    offset = -1 if expired else 1
    return {
        "tmdb_id": ident,
        "cache_expires_at": (datetime.now(UTC) + timedelta(days=offset)).isoformat(),
        "availability": {"status": ("complete", "partial", "unknown")[ident % 3]},
    }


class FixtureHTTP:
    def __init__(self, backend, *, failure=None, duplicate=False, bad_readback=False):
        self.backend = backend
        self.failure = failure
        self.duplicate = duplicate
        self.bad_readback = bad_readback
        self.cache = {ident: result(ident) for ident in (1001, 1002)}
        self.events = []
        self.refreshes = 0

    @staticmethod
    def issue(ident):
        return {
            "id": str(ident),
            "idReadable": f"FILMREAL-{ident}",
            "project": {"shortName": "FILMREAL"},
            "customFields": [{"name": "FilmIQ TMDB ID", "value": ident}],
        }

    def request(self, _base, path, *, post=False, query=None):
        if path == "/custom-field/project/fictional-project/values":
            rows = [
                {"fieldName": "POC TMDB ID", "taskId": f"fictional-{ident}", "value": str(ident)}
                for ident in sorted(IDS)
            ]
            return rows + rows[:1] if self.duplicate else rows
        if path.startswith("/custom-field/task/"):
            task = path.rsplit("/", 1)[-1]
            return [
                {
                    "fieldName": "POC TMDB ID",
                    "taskId": task,
                    "fieldType": "text",
                    "value": task.split("-")[-1],
                }
            ]
        if path.startswith("/task/"):
            return {"id": path.rsplit("/", 1)[-1]}
        if path == "/issues":
            rows = [self.issue(ident) for ident in sorted(IDS)]
            if self.duplicate:
                rows.append({**rows[0], "id": "extra"})
            assert query is not None
            start = int(query["$skip"])
            return rows[start : start + 50]
        if path.startswith("/issues/") and "/extensionEndpoints/" not in path:
            return self.issue(int(path.rsplit("-", 1)[-1]))
        action = path.split("/")[-2] if self.backend == "kaneo" else path.rsplit("/", 1)[-1]
        record = path.rsplit("/", 1)[-1] if self.backend == "kaneo" else path.split("/")[2]
        ident = int(record.rsplit("-", 1)[-1])
        is_refresh = action in ("refresh", "read")
        assert post == (self.backend == "youtrack" and is_refresh)
        self.events.append(("refresh" if is_refresh else "cache", ident))
        if is_refresh:
            self.refreshes += 1
            if self.failure and self.refreshes == 3:
                raise batch.BatchError(self.failure)
            self.cache[ident] = result(ident)
            return result(ident)
        if self.bad_readback and self.refreshes and ident in self.cache:
            return result(ident + 1)
        return self.cache.get(ident, batch.CACHE_MISS)


def blank_report():
    return {
        "validated": 0,
        "skipped_fresh": 0,
        "attempted": 0,
        "refreshed": 0,
        "availability_complete": 0,
        "availability_partial": 0,
        "availability_unknown": 0,
    }


def main():
    with tempfile.TemporaryDirectory(dir=batch.LOCAL) as directory:
        private = Path(directory)
        (private / "kaneo-private-ids.json").write_text('{"project":"fictional-project"}')
        (private / "tmdb-approval").mkdir()
        manifest = json.dumps({"films": [{"tmdb_id": ident} for ident in sorted(IDS)]}).encode()
        preview = b"Fictional watched approval"
        (private / "film-input.json").write_bytes(manifest)
        (private / "tmdb-watched-lookup-preview.md").write_bytes(preview)
        allowed_file = private / "tmdb-approval/approved-ids.json"
        document = {
            "version": 1,
            "allowed_ids": sorted(IDS),
            "destinations": ["api.themoviedb.org", "image.tmdb.org"],
            "source_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
            "watched_approval_preview_sha256": hashlib.sha256(preview).hexdigest(),
        }
        allowed_file.write_text(json.dumps(document))
        with patch.object(batch, "PRIVATE", private):
            assert batch.identities() == IDS
            allowed_file.write_text(
                json.dumps({**document, "allowed_ids": sorted((IDS - {1001}) | {9999})})
            )
            try:
                batch.identities()
            except batch.BatchError as error:
                assert error.kind == "approval"
            else:
                raise AssertionError("Same-count approval substitution was accepted")
            allowed_file.write_text(json.dumps(document))
            (private / "tmdb-watched-lookup-preview.md").write_bytes(b"Different fictional preview")
            try:
                batch.identities()
            except batch.BatchError as error:
                assert error.kind == "approval"
            else:
                raise AssertionError("Changed watched approval preview was accepted")
            (private / "tmdb-watched-lookup-preview.md").write_bytes(preview)
            for backend in ("kaneo", "youtrack"):
                http, report = FixtureHTTP(backend), blank_report()
                batch.run(http, backend, IDS, report)
                assert report == {
                    "validated": 130,
                    "skipped_fresh": 2,
                    "attempted": 25,
                    "refreshed": 25,
                    "availability_complete": 9,
                    "availability_partial": 9,
                    "availability_unknown": 9,
                }
                assert http.refreshes == 25
                for index, (action, ident) in enumerate(http.events):
                    if action == "refresh":
                        assert http.events[index + 1] == ("cache", ident)

                for kind in ("rate_limited", "authentication_or_approval", "error"):
                    http, report = FixtureHTTP(backend, failure=kind), blank_report()
                    try:
                        batch.run(http, backend, IDS, report)
                    except batch.BatchError as error:
                        assert error.kind == kind
                    else:
                        raise AssertionError("Failure did not stop the batch")
                    assert (
                        http.refreshes == 3
                        and report["attempted"] == 3
                        and report["refreshed"] == 2
                    )
                    assert http.events[-1][0] == "refresh"

                http, report = FixtureHTTP(backend, duplicate=True), blank_report()
                try:
                    batch.run(http, backend, IDS, report)
                except batch.BatchError as error:
                    assert error.kind == "records"
                else:
                    raise AssertionError("Duplicate identity was accepted")
                assert not http.events

                http, report = FixtureHTTP(backend, bad_readback=True), blank_report()
                try:
                    batch.run(http, backend, IDS, report)
                except batch.BatchError as error:
                    assert error.kind == "response"
                else:
                    raise AssertionError("Mismatched cache readback was accepted")
                assert report["attempted"] == 1 and report["refreshed"] == 0

    # An expired or invalid cached response is an error, not a cache miss.
    for value in (None, result(1001, expired=True)):
        try:
            batch.validate_result(value, 1001, datetime.now(UTC))
        except batch.BatchError:
            pass
        else:
            raise AssertionError("Invalid cached response was accepted")

    # Only the bridge's explicit cache-miss body permits a refresh after 404.
    http = object.__new__(batch.LocalHTTP)
    http.headers = {}
    http.opener = urllib.request.build_opener()
    for payload, expected in (
        (b'{"error":"Cache miss"}', True),
        (b'{"error":"Film unavailable"}', False),
    ):

        def open_error(*_args, payload=payload, **_kwargs):
            raise urllib.error.HTTPError(
                "http://fixture", 404, "not found", Message(), io.BytesIO(payload)
            )

        with patch.object(http.opener, "open", side_effect=open_error):
            try:
                outcome = http.request("http://localhost:15176", "/cache/fictional")
                assert expected and outcome is batch.CACHE_MISS
            except batch.BatchError:
                assert not expected

    # Effective settings come from authenticated status routes, never process environments.
    with tempfile.TemporaryDirectory(dir=batch.LOCAL) as directory:
        private = Path(directory)
        (private / "tmdb-pilot-approval").mkdir()
        (private / "tmdb-pilot-approval/selection.json").write_text(
            '{"tmdb_id":1001,"youtrack_issue":"FILMREAL-1001"}'
        )

        class StatusHTTP(batch.LocalHTTP):
            def __init__(self, status):
                self.status = status
                self.calls = []

            def request(self, base, path, *, post=False, query=None):
                self.calls.append((path, post))
                assert not post
                if path == "/issues/FILMREAL-1001":
                    return FixtureHTTP.issue(1001)
                return self.status

        with patch.object(batch, "PRIVATE", private):
            for backend in ("kaneo", "youtrack"):
                for active, idle, accepted in (
                    (
                        {"pace_enabled": True, "refresh_enabled": True},
                        {"pace_enabled": False, "refresh_enabled": False},
                        True,
                    ),
                    (
                        {"pace_enabled": False, "refresh_enabled": True},
                        {"pace_enabled": False, "refresh_enabled": False},
                        False,
                    ),
                    (
                        {"pace_enabled": True, "refresh_enabled": True},
                        {"pace_enabled": True, "refresh_enabled": True},
                        False,
                    ),
                    (
                        {"pace_enabled": True, "refresh_enabled": False},
                        {"pace_enabled": False, "refresh_enabled": False},
                        False,
                    ),
                    (
                        {"pace_enabled": "1", "refresh_enabled": True},
                        {"pace_enabled": False, "refresh_enabled": False},
                        False,
                    ),
                ):
                    kaneo = StatusHTTP(active if backend == "kaneo" else idle)
                    youtrack = StatusHTTP(active if backend == "youtrack" else idle)
                    try:
                        batch.require_pacing(backend, IDS, kaneo, youtrack)
                        assert accepted
                    except batch.BatchError as error:
                        assert not accepted and error.kind == "pacing_not_established"
                    assert all(not post for _, post in kaneo.calls + youtrack.calls)

    with (
        patch.object(batch, "identities") as load,
        patch.object(batch, "LocalHTTP") as factory,
        patch.object(batch.sys, "argv", ["batch", "--backend", "kaneo"]),
        patch("sys.stdout", new_callable=io.StringIO) as output,
    ):
        assert batch.main() == 2
        assert json.loads(output.getvalue())["result"] == "not_started"
        load.assert_not_called()
        factory.assert_not_called()

    with (
        patch.object(
            batch, "require_pacing", side_effect=batch.BatchError("pacing_not_established")
        ),
        patch.object(batch, "LocalHTTP") as factory,
        patch.object(batch, "identities", return_value=IDS),
        patch.object(batch, "run") as run,
        patch.object(batch.sys, "argv", ["batch", "--backend", "kaneo", "--run"]),
        patch("sys.stdout", new_callable=io.StringIO) as output,
    ):
        assert batch.main() == 1
        assert json.loads(output.getvalue())["result"] == "pacing_not_established"
        assert factory.call_count == 2
        run.assert_not_called()
    print("Fictional batch limits, preflight, cache verification and stop-on-error checks passed")


if __name__ == "__main__":
    main()
