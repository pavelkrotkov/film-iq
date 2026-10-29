"""Explicit tied ranks in frozen 2012/2022 directors' poll section responses."""

import re
from collections import Counter
from hashlib import sha256

from film_iq.ingest.adapters.page_capture import Entry, Extraction, frozen_text, linked_title

CAPTURES = {
    2012: (1196879962, "c8f9e3e60b622d7805a62324d206f47d916b1996ef950bd2dfdaab4c0d41e8ee", 10, 3),
    2022: (1332699136, "664b739c737878b6fc5221faa25c93626765a8ddb6a9ff62433b956d478f936b", 11, 2),
}
ORIGINALS = {
    2012: "https://www.bfi.org.uk/sight-and-sound/polls/greatest-films-all-time/directors-100-best",
    2022: "https://www.bfi.org.uk/sight-and-sound/directors-100-greatest-films-all-time",
}


def extract(year: int, body: bytes) -> Extraction:
    if year not in CAPTURES:
        raise ValueError("Unknown Sight and Sound edition; review required")
    revision, digest, count, section = CAPTURES[year]
    text = frozen_text(body, digest, revision)
    rows = [
        (number, line, int(match[1]))
        for number, line in enumerate(text.splitlines(), 1)
        if (match := re.match(r'(?:# )?<li value="(\d+)">', line))
    ]
    ranks = Counter(rank for _, _, rank in rows)
    entries = tuple(
        Entry(
            linked_title(line),
            line,
            position,
            rank,
            f"section {section} wikitext line {number}",
            f"rank-{rank}" if ranks[rank] > 1 else None,
        )
        for position, (number, line, rank) in enumerate(rows, 1)
    )
    if len(entries) != count:
        raise ValueError("Incomplete directors' section; review required")
    return Extraction(
        source_url=f"https://en.wikipedia.org/w/index.php?oldid={revision}#Directors%27_poll",
        original_url=ORIGINALS[year],
        document_revision=str(revision),
        parser_revision="directors-page-1",
        content_sha256=sha256(body).hexdigest(),
        eligibility=f"Sight and Sound {year} directors' all-time film poll; not release-year limited",
        ballot_completeness="not individual ballots; partial aggregate ranking, top ten ranks only",
        extraction_scope="complete published directors' section; partial underlying top-100 aggregate",
        lineage=f"Wikipedia contributors -> BFI Sight and Sound {year} directors' poll; derivative",
        rank_semantics="explicit source ranks with ties; position is separate",
        entries=entries,
    )
