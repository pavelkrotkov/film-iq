"""Extract a frozen 2023 NBR section; its claimed revision needs verification."""

import re
from dataclasses import dataclass
from hashlib import sha256

REVISION = "1370562803"
PARSER_VERSION = "1"
# This adapter accepts only the frozen section, not an arbitrary live page.
SECTION_SHA256 = "4d1a2d409d774c081b6cb2b8af862892b087e6d244055c5122d79f7277b70406"


@dataclass(frozen=True)
class Entry:
    title: str
    raw_context: str
    position: int
    rank: int | None
    locator: str


@dataclass(frozen=True)
class Extraction:
    source_url: str
    original_url: str
    document_revision: str
    parser_revision: str
    content_sha256: str
    eligibility: str
    ballot_completeness: str
    extraction_scope: str
    lineage: str
    entries: tuple[Entry, ...]


def extract(section: bytes) -> Extraction:
    digest = sha256(section).hexdigest()
    if digest != SECTION_SHA256:
        raise ValueError("Source section differs from the audited revision; review required")
    lines = section.decode("utf-8").splitlines()[3:]
    entries = tuple(
        Entry(
            match.group(1).split("|")[-1],
            line,
            index,
            1 if index == 1 else None,
            f"line {index + 3}",
        )
        for index, line in enumerate(lines, 1)
        if (match := re.search(r"\[\[([^\]]+)\]\]", line))
    )
    if len(entries) != 10:
        raise ValueError("Incomplete audited section; review required")
    return Extraction(
        source_url=f"https://en.wikipedia.org/w/index.php?oldid={REVISION}",
        original_url="https://nationalboardofreview.org/2023/12/national-board-of-review-names-2023-honorees/",
        document_revision=REVISION,
        parser_revision=PARSER_VERSION,
        content_sha256=digest,
        eligibility="NBR 2023 Best Film and Top Films selections; detailed eligibility unknown",
        ballot_completeness="unknown",
        extraction_scope="complete Top 10 Films section only; other page sections excluded",
        lineage="Wikipedia summary of National Board of Review selections; derivative",
        entries=entries,
    )
