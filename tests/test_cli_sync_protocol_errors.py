"""Protocol failures stop CLI execution without exposing remote response details."""

from http.client import BadStatusLine, HTTPException, IncompleteRead
from unittest.mock import patch

import pytest
from test_sync_cli_http import response

from film_iq.cli import main

DETAIL = "https://user:password@movary.invalid/private Bearer secret-token response-body"


@pytest.mark.parametrize(
    "error",
    [IncompleteRead(DETAIL.encode(), 100), BadStatusLine(DETAIL), HTTPException(DETAIL)],
    ids=["truncated-body", "malformed-status", "protocol-error"],
)
@pytest.mark.parametrize("failure_at", ["open", "read"])
@pytest.mark.parametrize("stage", range(4), ids=["search", "add-movie", "watchlist", "add-entry"])
def test_protocol_failure_stops_cli(error, failure_at, stage, capsys):
    config = dict(
        MOVARY_URL="https://user:password@movary.invalid/private",
        MOVARY_USERNAME="private-user",
        MOVARY_TOKEN="secret-token",
    )
    replies = [
        response(
            200,
            b'{"results":[{"ids":{"tmdb":123,"movary":null}}],"currentPage":1,"maxPage":1}',
        ),
        response(200, b'{"movaryId":456}'),
        response(200, b'{"watchlist":[],"currentPage":1,"maxPage":1}'),
        response(204, b""),
    ]
    failed = response(200, b"")
    failed.read.side_effect = error
    replies[stage] = error if failure_at == "open" else failed
    with (
        patch.dict("os.environ", config, clear=True),
        patch("film_iq.movary_http.urlopen", side_effect=replies) as opening,
        pytest.raises(SystemExit) as caught,
    ):
        main(["sync", "--title", "Example", "--tmdb-id", "123", "--execute", "--approve"])
    assert caught.value.code == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err.endswith("film-iq: error: Movary HTTP transport failed\n")
    assert not any(
        detail in output.err
        for detail in (
            "Traceback",
            "https://",
            "password",
            "private",
            "secret-token",
            "response-body",
        )
    )
    assert [call.args[0].method for call in opening.call_args_list] == [
        "GET",
        "POST",
        "GET",
        "POST",
    ][: stage + 1]
