"""NBR's Wikipedia summaries: winner plus alphabetical selections, never top-N slicing."""

from hashlib import sha256

from film_iq.ingest.adapters.page_capture import Entry, Extraction, frozen_text, linked_title

CAPTURES = {
    2022: (1269459635, "a8113a002fc2a3298ca208a0faf5e407c80c0732eb3ada5ce9ae6dd783ad53de", 11),
    2023: (1370562803, "a1229f15e48d10bd44ec31efeeaea76ac27bbaf755087f015db474cd9850d7f2", 10),
}
ORIGINALS = {
    2022: "https://nationalboardofreview.org/2022/12/national-board-of-review-announces-2022-award-winners/",
    2023: "https://nationalboardofreview.org/2023/12/national-board-of-review-names-2023-honorees/",
}


def extract(year: int, body: bytes) -> Extraction:
    if year not in CAPTURES:
        raise ValueError("Unknown NBR edition; review required")
    revision, digest, count = CAPTURES[year]
    text = frozen_text(body, digest, revision)
    rows = [
        (n, line)
        for n, line in enumerate(text.splitlines(), 1)
        if line.startswith(("* ", "'''''[["))
    ]
    entries = tuple(
        Entry(
            linked_title(line),
            line,
            position,
            1 if position == 1 else None,
            f"section 1 wikitext line {number}",
            None,
        )
        for position, (number, line) in enumerate(rows, 1)
    )
    if len(entries) != count:
        raise ValueError("Incomplete NBR section; review required")
    return Extraction(
        source_url=f"https://en.wikipedia.org/w/index.php?oldid={revision}#Top_10_Films",
        original_url=ORIGINALS[year],
        document_revision=str(revision),
        parser_revision="nbr-page-1",
        content_sha256=sha256(body).hexdigest(),
        eligibility=f"NBR {year} Best Film and Top Films; detailed eligibility unknown",
        ballot_completeness="unknown; published selections are not individual ballots",
        extraction_scope="complete published Top 10 Films section; remainder of page excluded",
        lineage=f"Wikipedia contributors -> NBR {year} selections; derivative, not another vote",
        rank_semantics="winner ranked; alphabetical selections unranked",
        entries=entries,
    )
