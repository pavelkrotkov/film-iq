"""Exercise the review importer with a fictional bearer key and no network."""

import io
import json
import os
import sys
import urllib.error
import urllib.request
import urllib.response
from contextlib import redirect_stdout
from email.message import Message
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import kaneo_direct_reviews as importer


class FictionalHTTP(urllib.request.BaseHandler):
    handler_order = 100

    def __init__(self):
        self.requests = []
        self.values = [{"taskId": "film", "fieldId": "identity", "value": "42"}]
        self.redirect = False
        self.rate_limited = False

    def http_open(self, request):
        self.requests.append(request)
        assert request.get_header("Authorization") == "Bearer fictional-test-key"
        assert request.get_header("Cookie") is None
        headers = Message()
        path = request.selector.removeprefix("/api")
        if self.redirect:
            headers["Location"] = "http://elsewhere.invalid/leak"
            response = urllib.response.addinfourl(io.BytesIO(b""), headers, request.full_url, 302)
            cast(Any, response).msg = "Found"
            return response
        if self.rate_limited:
            headers["Retry-After"] = "60"
            response = urllib.response.addinfourl(io.BytesIO(b""), headers, request.full_url, 429)
            cast(Any, response).msg = "Too Many Requests"
            return response
        if path == "/custom-field/project/project":
            data = [
                {"id": "identity", "name": importer.IDENTITY_FIELD, "type": "text"},
                {"id": "reviews", "name": importer.FIELD, "type": "text"},
            ]
        elif path in ("/custom-field/project/project/values", "/custom-field/task/film"):
            data = self.values
        elif path == "/task/film":
            data = {"title": "Fictional film"}
        else:
            assert path == "/custom-field/value" and request.get_method() == "PUT"
            data = json.loads(request.data)
            self.values.append(data)
        response = urllib.response.addinfourl(
            io.BytesIO(json.dumps(data).encode()), headers, request.full_url, 200
        )
        cast(Any, response).msg = "OK"
        return response


def main():
    for key in (None, "", "bad key", "bad\nkey", "bad\x7fkey", "nonascii-\u00e9"):
        try:
            importer.api_key_opener(key)
        except ValueError as error:
            assert "KANEO_API_KEY" in str(error)
        else:
            raise AssertionError("invalid key was accepted")

    with patch.dict(os.environ, {"http_proxy": "http://127.0.0.1:8181"}):
        opener = importer.api_key_opener("fictional-test-key")
    assert not any(isinstance(handler, urllib.request.ProxyHandler) for handler in opener.handlers)
    handler = FictionalHTTP()
    opener.add_handler(handler)
    row = {"tmdb_id": 42, "links": [{"url": "https://example.invalid/review"}]}
    source = {"films": [{"tmdb_id": 42, "title": "Fictional film"}]}
    with patch.object(importer, "validate_review_manifests", return_value=([row], 0)):
        assert (
            importer.import_reviews(opener, "http://127.0.0.1:9", "project", {}, source)["pending"]
            == 1
        )
        assert (
            importer.import_reviews(
                opener, "http://127.0.0.1:9", "project", {}, source, apply=True
            )["written"]
            == 1
        )
        assert (
            importer.import_reviews(
                opener, "http://127.0.0.1:9", "project", {}, source, apply=True
            )["written"]
            == 0
        )
    handler.redirect = True
    count = len(handler.requests)
    try:
        importer.call(opener, "http://127.0.0.1:9", "/task/film")
    except urllib.error.HTTPError as error:
        assert error.code == 302
    else:
        raise AssertionError("redirect was followed")
    assert len(handler.requests) == count + 1
    handler.redirect = False
    handler.rate_limited = True
    count = len(handler.requests)
    try:
        importer.call(opener, "http://127.0.0.1:9", "/task/film")
    except urllib.error.HTTPError as error:
        assert error.code == 429 and error.headers["Retry-After"] == "60"
    else:
        raise AssertionError("rate limit was ignored")
    assert len(handler.requests) == count + 1

    args = [
        "kaneo_direct_reviews.py",
        "--project",
        "project",
        "--api-key-env",
        "--input",
        "in",
        "--source",
        "src",
    ]
    with (
        patch.object(sys, "argv", args),
        patch.dict(os.environ, {"KANEO_API_KEY": "fictional-test-key"}),
        patch.object(Path, "read_text", return_value="{}"),
        patch.object(
            importer,
            "import_reviews",
            return_value={"pending": 1, "skipped": 0, "conflicts": 0, "written": 0},
        ) as run,
        redirect_stdout(io.StringIO()) as output,
    ):
        importer.main()
    assert run.call_args.args[0].addheaders == [("Authorization", "Bearer fictional-test-key")]
    assert "fictional-test-key" not in output.getvalue()

    args = [
        "kaneo_direct_reviews.py",
        "--project",
        "project",
        "--cookie-file",
        "fictional-cookie-file",
        "--input",
        "in",
        "--source",
        "src",
    ]
    with (
        patch.object(sys, "argv", args),
        patch.object(importer.http.cookiejar, "MozillaCookieJar") as make_jar,
        patch.object(importer.urllib.request, "build_opener") as build,
        patch.object(Path, "read_text", return_value="{}"),
        patch.object(
            importer,
            "import_reviews",
            return_value={"pending": 0, "skipped": 0, "conflicts": 0, "written": 0},
        ) as run,
        redirect_stdout(io.StringIO()),
    ):
        importer.main()
    make_jar.assert_called_once_with("fictional-cookie-file")
    make_jar.return_value.load.assert_called_once_with(ignore_discard=True)
    assert run.call_args.args[0] is build.return_value
    print("Fictional bearer review preview, idempotent import and redirect refusal passed")


if __name__ == "__main__":
    main()
