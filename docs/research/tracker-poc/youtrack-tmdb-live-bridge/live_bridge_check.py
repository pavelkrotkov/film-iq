"""Synthetic in-memory checks; never reads credentials or contacts a provider."""

import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import live_bridge
from live_bridge import (
    DESTINATIONS,
    Config,
    app,
    config_from_env,
    decode_allowlist,
    parse_allowlist,
    safe_poster,
)
from tmdb_readonly import TMDbAccessDenied, TMDbRateLimited, read_movie

TOKEN = "fixture-token-" + "x" * 32


def invoke(application, ident, token=TOKEN, *, path="/metadata", title=None):
    payload = json.dumps(
        {"tmdb_id": ident, **({"title": title} if path == "/catalog" else {})}
    ).encode()
    result = {}

    def start(status, headers):
        result.update(status=status, headers=dict(headers))

    result["body"] = json.loads(
        b"".join(
            application(
                {
                    "REQUEST_METHOD": "POST",
                    "PATH_INFO": path,
                    "CONTENT_LENGTH": str(len(payload)),
                    "HTTP_AUTHORIZATION": "Bearer " + token,
                    "wsgi.input": BytesIO(payload),
                },
                start,
            )
        )
    )
    assert result["headers"]["Cache-Control"] == "no-store"
    return result


def check():
    policy = {"version": 1, "allowed_ids": [101, 202], "destinations": sorted(DESTINATIONS)}
    env = {
        "FILMIQ_TMDB_BRIDGE_ENABLE_LIVE": "1",
        "FILMIQ_BRIDGE_TOKEN": TOKEN,
        "TMDB_API_KEY": "fake-key",
    }
    assert parse_allowlist(policy) == frozenset({101, 202})
    assert config_from_env(env) == Config(TOKEN)
    manifest = json.dumps({"films": [{"tmdb_id": item} for item in range(1, 131)]}).encode()
    preview = b"Fictional watched preview"
    full_document = {
        "version": 1,
        "allowed_ids": list(range(1, 131)),
        "destinations": sorted(DESTINATIONS),
        "source_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        "watched_approval_preview_sha256": hashlib.sha256(preview).hexdigest(),
    }
    raw = json.dumps(full_document).encode()
    assert live_bridge.validate_collection_approval(raw, manifest, preview) == frozenset(
        range(1, 131)
    )
    changed = {**full_document, "allowed_ids": [*range(1, 130), 999]}
    for bad_raw, bad_preview in ((json.dumps(changed).encode(), preview), (raw, preview + b"x")):
        try:
            live_bridge.validate_collection_approval(bad_raw, manifest, bad_preview)
        except ValueError:
            pass
        else:
            raise AssertionError("Altered collection approval was accepted")
    try:
        decode_allowlist('{"version":1,"version":1}')
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate configuration keys were accepted")
    for bad in (
        None,
        {},
        {**policy, "allowed_ids": []},
        {**policy, "allowed_ids": [True]},
        {**policy, "allowed_ids": [101, 101]},
        {**policy, "destinations": ["other.example"]},
    ):
        try:
            parse_allowlist(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid allowlist was accepted")
    for bad in (
        {},
        {**env, "FILMIQ_TMDB_BRIDGE_ENABLE_LIVE": "0"},
        {**env, "FILMIQ_BRIDGE_TOKEN": ""},
        {**env, "TMDB_API_KEY": ""},
    ):
        try:
            config_from_env(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("Missing live bridge configuration was accepted")
    assert safe_poster("https://image.tmdb.org/t/p/w500/example.jpg")
    assert safe_poster("https://image.tmdb.org.evil.example/example.jpg") is None
    assert safe_poster("https://user@image.tmdb.org/example.jpg") is None

    calls = []

    def fake_get(path, parameters=None):
        calls.append(path)
        if path == "movie/202":
            raise TMDbRateLimited("fixture secret must not leak")
        if path == "movie/101":
            return {
                "id": 101,
                "title": "Fictional",
                "original_title": "Fictional original",
                "overview": "Fictional synopsis",
                "release_date": "2001-01-01",
                "genres": [],
                "credits": {"crew": []},
                "poster_path": "/example.jpg",
                "external_ids": {"imdb_id": "tt0000101"},
            }
        if path == "configuration":
            return {
                "images": {
                    "secure_base_url": "https://image.tmdb.org/t/p/",
                    "poster_sizes": ["w500"],
                }
            }
        if path == "movie/101/watch/providers":
            return {"id": 101, "results": {}}
        raise AssertionError("Unexpected provider call")

    def reader(ident):
        return read_movie(ident, get=fake_get, now=datetime(2026, 1, 1, tzinfo=UTC))

    application = app(config_from_env(env), lambda: policy, reader)
    assert invoke(application, 101, "incorrect")["status"] == "401 Unauthorized"
    assert invoke(application, 999)["status"] == "403 Forbidden"
    assert calls == []

    catalog_calls = []

    def catalog_reader(ident, title):
        catalog_calls.append((ident, title))
        return {"tmdb_id": ident, "title": "Fictional"} if title == "Fictional" else None

    catalog_app = app(config_from_env(env), lambda: policy, reader, catalog_reader)
    assert (
        invoke(catalog_app, 101, "incorrect", path="/catalog", title="Fictional")["status"]
        == "401 Unauthorized"
    )
    assert invoke(catalog_app, 999, path="/catalog", title="Fictional")["status"] == "403 Forbidden"
    assert invoke(catalog_app, 101, path="/catalog", title=" ")["status"] == "400 Bad Request"
    assert catalog_calls == [] and calls == []
    result = invoke(catalog_app, 101, path="/catalog", title="Fictional")
    assert result["status"] == "200 OK" and result["body"]["status"] == "available"
    assert result["body"]["film"]["tmdb_id"] == 101 and calls == []
    assert invoke(catalog_app, 101, path="/catalog", title="Different")["body"] == {
        "status": "unknown"
    }
    assert invoke(application, 101, path="/catalog", title="Fictional")["body"] == {
        "status": "unknown"
    }

    # An independently approved local catalog remains available while the
    # provider/cache allowlist is restricted to a single fictional film.
    restricted = {**policy, "allowed_ids": [101]}
    catalog_approval = {**policy, "allowed_ids": [101, 202]}
    separated = app(
        config_from_env(env),
        lambda: restricted,
        reader,
        catalog_reader,
        load_catalog_allowlist=lambda: catalog_approval,
    )
    assert invoke(separated, 202, path="/catalog", title="Fictional")["status"] == "200 OK"
    assert invoke(separated, 202)["status"] == "403 Forbidden"
    assert invoke(separated, 202, path="/cache")["status"] == "403 Forbidden"
    assert calls == [], "A catalog read or denied film must not call the provider"
    default_restricted = app(config_from_env(env), lambda: restricted, reader, catalog_reader)
    assert (
        invoke(default_restricted, 202, path="/catalog", title="Fictional")["status"]
        == "403 Forbidden"
    )
    catalog_approval["allowed_ids"] = [101]
    assert invoke(separated, 202, path="/catalog", title="Fictional")["status"] == "403 Forbidden"
    catalog_approval["allowed_ids"] = []
    assert (
        invoke(separated, 101, path="/catalog", title="Fictional")["status"]
        == "503 Service Unavailable"
    )
    assert invoke(separated, 202)["status"] == "403 Forbidden" and calls == []

    # Exercise the actual startup wiring without binding a socket: the catalog
    # facts file and its separate approval directory must remain distinct.
    root = Path(__file__).resolve().parents[4] / ".cache/tracker-poc"
    with tempfile.TemporaryDirectory(prefix="fictional-catalog-approval-", dir=root) as place:
        directory = Path(place)
        primary, catalog_dir = directory / "primary", directory / "catalog-approval"
        primary.mkdir()
        catalog_dir.mkdir()
        (primary / "approved-ids.json").write_text(json.dumps(restricted))
        (catalog_dir / "approved-ids.json").write_text(
            json.dumps({**policy, "allowed_ids": [101, 202]})
        )
        reviewed_file = directory / "fictional-reviewed-catalog.json"
        startup_env = {
            **env,
            "FILMIQ_REVIEWED_CATALOG": str(reviewed_file),
            "FILMIQ_CATALOG_APPROVAL_DIR": str(catalog_dir),
        }
        observed = []

        def fake_catalog(path, ident, title):
            observed.append((path, ident, title))
            return {"tmdb_id": ident, "title": title}

        class FakeServer:
            def __init__(self, application):
                self.application = application

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return None

            def serve_forever(self):
                result = invoke(self.application, 202, path="/catalog", title="Fictional")
                assert result["status"] == "200 OK" and result["body"]["status"] == "available"
                assert invoke(self.application, 202)["status"] == "403 Forbidden"

        with (
            patch.dict(os.environ, startup_env, clear=True),
            patch.object(live_bridge, "ALLOWLIST_PATH", primary / "approved-ids.json"),
            patch.object(
                live_bridge,
                "make_server",
                side_effect=lambda _host, _port, application, **_kw: FakeServer(application),
            ),
            patch("reviewed_catalog.catalog_facts", side_effect=fake_catalog),
        ):
            live_bridge.main()
        assert observed == [(reviewed_file, 202, "Fictional")]
        for invalid in ("", "relative/path"):
            with (
                patch.dict(
                    os.environ, {**startup_env, "FILMIQ_CATALOG_APPROVAL_DIR": invalid}, clear=True
                ),
                patch.object(live_bridge, "ALLOWLIST_PATH", primary / "approved-ids.json"),
                patch.object(live_bridge, "make_server") as make_server,
            ):
                try:
                    live_bridge.main()
                except SystemExit as error:
                    assert str(error) == "Live bridge configuration unavailable"
                else:
                    raise AssertionError("An invalid catalog approval directory was accepted")
                make_server.assert_not_called()

    def missing_allowlist():
        raise FileNotFoundError("fixture path must not leak")

    missing = invoke(app(config_from_env(env), missing_allowlist, reader), 101)
    assert missing["status"] == "503 Service Unavailable" and calls == []
    assert "fixture path" not in json.dumps(missing["body"])
    ok = invoke(application, 101)
    assert ok["status"] == "200 OK"
    assert set(ok["body"]) == {
        "tmdb_id",
        "title",
        "original_title",
        "synopsis",
        "year",
        "genres",
        "directors",
        "poster_url",
        "imdb_title_url",
        "availability",
    }
    assert ok["body"]["tmdb_id"] == 101 and ok["body"]["availability"]["status"] == "unknown"
    assert ok["body"]["original_title"] == "Fictional original"
    assert ok["body"]["poster_url"] == "https://image.tmdb.org/t/p/w500/example.jpg"
    limited = invoke(application, 202)
    assert limited["status"] == "429 Too Many Requests" and "secret" not in json.dumps(
        limited["body"]
    )

    def denied(_):
        raise TMDbAccessDenied("secret must not be returned")

    failure = invoke(app(config_from_env(env), lambda: policy, denied), 101)
    assert failure["status"] == "502 Bad Gateway" and failure["body"] == {
        "error": "TMDB unavailable"
    }
    policy["allowed_ids"] = []
    count = len(calls)
    assert invoke(application, 101)["status"] == "503 Service Unavailable" and len(calls) == count
    policy["allowed_ids"] = [202]
    assert invoke(application, 101)["status"] == "403 Forbidden" and len(calls) == count
    print("Synthetic allowlist, credential, no-store, payload and 429 checks passed")


if __name__ == "__main__":
    check()
