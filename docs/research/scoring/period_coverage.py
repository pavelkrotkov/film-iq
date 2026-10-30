"""Observed period/format denominators, with unknown exposure kept explicit."""


def coverage(rows: list[dict]) -> dict:
    """A missing list is unknown; it cannot supply a negative relevance label."""
    return {
        "films": len(rows),
        "known_training": sum(row["training_count"] is not None for row in rows),
        "known_heldout": sum(row["heldout_count"] is not None for row in rows),
        "paired": sum(
            row["training_count"] is not None and row["heldout_count"] is not None for row in rows
        ),
    }


def groups(rows: list[dict], key: str) -> dict:
    """Country memberships overlap; these denominators must not be added."""
    labels = sorted({label for row in rows for label in row[key]})
    return {label: coverage([row for row in rows if label in row[key]]) for label in labels}
