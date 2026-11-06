"""Offline synthetic check; no credentials, filesystem writes, or network."""

import hashlib
import json
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from unittest.mock import patch

import tmdb_live
from tmdb_addendum_candidate import load_on_demand_allowlist, on_demand_allowlist
from tmdb_live_check import invoke as invoke_kaneo
from tmdb_readonly import Movie

from film_iq.availability.tmdb import Observation

live_bridge = import_module("live_bridge")
live_bridge_check = import_module("live_bridge_check")
TOKEN = live_bridge_check.TOKEN
invoke_youtrack = live_bridge_check.invoke


def check():
    now = datetime(2026, 11, 6, tzinfo=UTC)
    manifest = json.dumps({"films": [{"tmdb_id": i} for i in range(1, 131)]}).encode()
    old_preview = b"Fictional original approval"
    original = json.dumps(
        {
            "version": 1,
            "allowed_ids": list(range(1, 131)),
            "destinations": sorted(live_bridge.DESTINATIONS),
            "source_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
            "watched_approval_preview_sha256": hashlib.sha256(old_preview).hexdigest(),
        }
    ).encode()
    preview = "1. Fictional one — TMDb ID `201`\n2. Fictional two — TMDb ID `202`\n".encode()
    addendum = {
        "version": 1,
        "scope": "on-demand",
        "allowed_ids": [201, 202],
        "preview_sha256": hashlib.sha256(preview).hexdigest(),
        "expires_at": "2026-12-06T00:00:00Z",
    }

    def validate(value=addendum, displayed=preview, *, timestamp=now, base=original):
        return on_demand_allowlist(
            base, manifest, old_preview, json.dumps(value).encode(), displayed, now=timestamp
        )

    with patch("socket.socket", side_effect=AssertionError("No network permitted")):
        approved = validate()
        assert set(approved["allowed_ids"]) == set(range(1, 131)) | {201, 202}
        for value, displayed, timestamp, base in (
            ({**addendum, "allowed_ids": [201, 203]}, preview, now, original),
            ({**addendum, "allowed_ids": [1, 202]}, preview, now, original),
            ({**addendum, "scope": "scheduled"}, preview, now, original),
            ({**addendum, "expires_at": "2026-12-07T00:00:00Z"}, preview, now, original),
            (addendum, preview + b"changed", now, original),
            (addendum, preview, datetime(2026, 12, 6, tzinfo=UTC), original),
            (addendum, preview, now, b"{}"),
        ):
            try:
                validate(value, displayed, timestamp=timestamp, base=base)
            except (ValueError, TypeError):
                pass
            else:
                raise AssertionError("Invalid approval was accepted")

        calls = []

        def reader(ident):
            calls.append(ident)
            return Movie(
                ident, "Fictional", None, None, None, None, None, Observation((), "unknown", now)
            )

        youtrack = live_bridge.app(live_bridge.Config(TOKEN), lambda: approved, reader)
        kaneo = tmdb_live.app(reader, lambda _: "fictional", lambda: approved)
        for ident in (1, 201, 202):
            assert invoke_youtrack(youtrack, ident)["status"] == "200 OK"
            assert invoke_kaneo(kaneo, f"/movie/{ident}")["status"] == "200 OK"
        assert invoke_youtrack(youtrack, 203)["status"] == "403 Forbidden"
        assert invoke_kaneo(kaneo, "/movie/203")["status"] == "403 Forbidden"
        assert calls == [1, 1, 201, 201, 202, 202]

        files = {
            "approved-ids.json": original,
            "film-input.json": manifest,
            "tmdb-watched-lookup-preview.md": old_preview,
            "tmdb-addendum-approval.json": json.dumps(addendum).encode(),
            "tmdb-watchlist-two-id-lookup-preview-20261106.md": preview,
        }

        def read_file(path):
            try:
                return files[path.name]
            except KeyError:
                raise FileNotFoundError from None

        with (
            patch.object(Path, "read_bytes", read_file),
            patch("tmdb_addendum_candidate.datetime", wraps=datetime) as clock,
        ):
            clock.now.return_value = now

            def load():
                return load_on_demand_allowlist(
                    Path("/fixture/approved-ids.json"), Path("/fixture")
                )

            youtrack = live_bridge.app(live_bridge.Config(TOKEN), load, reader)
            kaneo = tmdb_live.app(reader, lambda _: "fictional", load)
            assert invoke_youtrack(youtrack, 201)["status"] == "200 OK"
            assert invoke_kaneo(kaneo, "/movie/201")["status"] == "200 OK"
            clock.now.return_value = datetime(2026, 12, 6, tzinfo=UTC)
            assert invoke_youtrack(youtrack, 201)["status"] == "403 Forbidden"
            assert invoke_kaneo(kaneo, "/movie/201")["status"] == "403 Forbidden"
            assert invoke_youtrack(youtrack, 1)["status"] == "200 OK"
            assert invoke_kaneo(kaneo, "/movie/1")["status"] == "200 OK"
            del files["tmdb-addendum-approval.json"]
            clock.now.return_value = now
            assert invoke_youtrack(youtrack, 201)["status"] == "403 Forbidden"
            assert invoke_kaneo(kaneo, "/movie/1")["status"] == "200 OK"
    print("Synthetic addendum checks passed; no network or credentials used.")


if __name__ == "__main__":
    check()
