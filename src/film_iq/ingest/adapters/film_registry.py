"""Extract reviewed transcriptions of Library of Congress annual selections."""

import re
from dataclasses import dataclass
from hashlib import sha256

SOURCES = {
    2020: (
        "45bb68330c9d5f9c750a4ffbf7573bc3aea6ecebe75a186a61e113f67aacbe33",
        "https://www.loc.gov/item/prn-20-082/",
    ),
    2022: (
        "17d428b8c2a00e981f2173605a06cde5028eff8bbeca32e83cdb41c8e82d0bbd",
        "https://blogs.loc.gov/now-see-hear/2022/12/announcing-the-2022-national-film-registry/",
    ),
    2025: (
        "662e3df3f994701d5af755cfc211f63b5b0526126eb8009ca0a810f91dfd8990",
        "https://newsroom.loc.gov/news/library-names-25-films-to-the-national-film-registry-for-preservation/s/54d2521d-cc42-4987-9c75-4a08d2d901e1",
    ),
}


@dataclass(frozen=True)
class Entry:
    title: str
    release_date: str
    position: int
    rank: None
    locator: str


@dataclass(frozen=True)
class Extraction:
    source_url: str
    document_revision: str
    parser_revision: str
    content_sha256: str
    eligibility: str
    ballot_completeness: str
    extraction_scope: str
    lineage: str
    entries: tuple[Entry, ...]


def extract(year: int, transcription: bytes) -> Extraction:
    if year not in SOURCES:
        raise ValueError("Unreviewed edition; review required")
    expected, url = SOURCES[year]
    digest = sha256(transcription).hexdigest()
    if digest != expected:
        raise ValueError("Transcription changed or incomplete; review required")
    entries = []
    for position, line in enumerate(transcription.decode("utf-8").splitlines(), 1):
        match = re.fullmatch(r"(.+) \((\d{4}(?:-\d{4})?)\)", line)
        if not match:
            raise ValueError("Invalid entry; review required")
        entries.append(Entry(match[1], match[2], position, None, f"transcription line {position}"))
    if len(entries) != 25:
        raise ValueError("Incomplete selection; review required")
    return Extraction(
        source_url=url,
        document_revision=f"transcription sha256:{digest}",
        parser_revision="1",
        content_sha256=digest,
        eligibility="American films at least 10 years old, selected for cultural, historic or aesthetic significance",
        ballot_completeness="unknown; selections are not ballots",
        extraction_scope="complete 25 selections; other page content omitted",
        lineage="Library of Congress primary announcement; transcription",
        entries=tuple(entries),
    )
