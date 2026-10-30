"""Ballot scope and reviewed-ID assertions, separate from CSV syntax."""

from film_iq.ingest.curated_row import CuratedRow


def validate_ballot(rows: list[CuratedRow]) -> None:
    """One file is one ballot, not a publisher poll or collection of critics."""
    metadata = (
        "source_id",
        "source_url",
        "edition",
        "ballot_scope",
        "published_at",
        "eligibility_date",
    )
    for name in metadata:
        if len({getattr(row, name) for row in rows}) != 1:
            raise ValueError(f"one source edition/ballot per CSV; inconsistent {name}")
    for row in rows:
        _validate_identity(row)


def _validate_identity(row: CuratedRow) -> None:
    """An ID is an explicit reviewed assertion; a numeric value alone is insufficient."""
    if row.tie and row.rank is None:
        raise ValueError("tie requires a published rank")
    if row.tmdb_id and not (row.identity_reviewer and row.identity_evidence):
        raise ValueError("TMDB ID requires explicit identity reviewer and evidence")
