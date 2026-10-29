"""A lost write response requires a fresh read before retrying."""

import pytest
from conftest import TransportStub

from film_iq.approval import Preview, sync_one
from film_iq.movary_write import MovaryWriteBackend


def test_retry_after_lost_write_response_reads_first() -> None:
    stub = TransportStub()

    def transport(method: str, path: str, body: object) -> tuple[int, object]:
        result = stub(method, path, body)
        if method == "POST" and path.endswith("watchlist/movies"):
            raise ConnectionError("response lost")
        return result

    preview = Preview("Example", 123)
    backend = MovaryWriteBackend(preview, "user", transport)
    with pytest.raises(ConnectionError):
        sync_one(preview, backend, execute=True, approved=True)
    assert sync_one(preview, backend, execute=True, approved=True) == "already on watchlist"
    assert len([call for call in stub.calls if call[0] == "POST"]) == 2
