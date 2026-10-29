"""Frozen MediaWiki response contract; captures do not themselves record acceptance."""

import json
import re
from dataclasses import dataclass
from hashlib import sha256

from film_iq.ingest.adapters.nbr_2023 import Entry as PublishedEntry


@dataclass(frozen=True)
class Entry(PublishedEntry):
    """Published film label and literal source row, including unparsed context."""

    tie: str | None


@dataclass(frozen=True)
class Extraction:
    """A complete captured section may still be only part of an aggregate poll."""

    source_url: str
    original_url: str
    document_revision: str
    parser_revision: str
    content_sha256: str
    eligibility: str
    ballot_completeness: str
    extraction_scope: str
    lineage: str
    rank_semantics: str
    entries: tuple[Entry, ...]
    review_reason: str = (
        "Independent automated oracle available; explicit acceptance attestation not yet recorded"
    )


def frozen_text(body: bytes, expected_hash: str, revision: int) -> str:
    """Only previously inspected exact response bytes can enter these POC adapters."""
    if sha256(body).hexdigest() != expected_hash:
        raise ValueError("Capture changed, failed or incomplete; review required")
    page = json.loads(body)["parse"]
    if page["revid"] != revision:
        raise ValueError("Document revision mismatch; review required")
    return page["wikitext"]["*"]


def linked_title(line: str) -> str:
    """The first wiki link is the film in these frozen selection rows only."""
    match = re.search(r"\[\[([^\]]+)\]\]", line)
    if match is None:
        raise ValueError("Selection has no film link; review required")
    return match[1].split("|")[-1]
