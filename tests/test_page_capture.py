"""Keep exact captures and their acquisition/revision/license evidence verifiable."""

import json
from hashlib import sha256
from pathlib import Path

import pytest

from film_iq.ingest.adapters.page_capture import frozen_text, linked_title

PAGES = Path(__file__).parent / "fixtures/ingest/pages"
CAPTURES = json.loads((PAGES / "captures.json").read_text())


@pytest.mark.parametrize("capture", CAPTURES, ids=lambda item: item["key"])
def test_exact_response_receipts(capture):
    for kind in ("capture", "revision_evidence", "rendered_evidence"):
        receipt = capture[kind]
        body = (PAGES / receipt["file"]).read_bytes()
        assert (len(body), sha256(body).hexdigest()) == (receipt["bytes"], receipt["sha256"])
        assert receipt["http_status"] == 200
        assert receipt["response_url"] == receipt["requested_url"]


@pytest.mark.parametrize("capture", CAPTURES, ids=lambda item: item["key"])
def test_exact_revision_evidence_and_license(capture):
    page = json.loads((PAGES / capture["capture"]["file"]).read_bytes())["parse"]
    evidence = json.loads((PAGES / capture["revision_evidence"]["file"]).read_bytes())
    revision = next(iter(evidence["query"]["pages"].values()))["revisions"][0]
    assert page["revid"] == revision["revid"] == capture["revision"]
    assert revision["timestamp"] < capture["capture"]["accessed_at"]
    assert (
        capture["license"]
        == json.loads((PAGES / "rightsinfo.json").read_bytes())["query"]["rightsinfo"]
    )


def test_contract_rejects_revision_mismatch_and_missing_film_link():
    body = b'{"parse":{"revid":1,"wikitext":{"*":"text"}}}'
    with pytest.raises(ValueError, match="revision mismatch"):
        frozen_text(body, sha256(body).hexdigest(), 2)
    with pytest.raises(ValueError, match="no film link"):
        linked_title("plain text is not the reviewed row format")
