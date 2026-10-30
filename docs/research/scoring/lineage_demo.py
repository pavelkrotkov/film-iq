"""Small synthetic check, not a production scorer or a real ballot dataset."""

from collections import Counter


def independent_counts(rows: tuple[tuple[str, str | None, str, str], ...]) -> Counter[str]:
    """Count verified people once per film; aggregated and unidentified rows stay separate."""
    pairs = {
        (film, person)
        for film, person, _source, kind in rows
        if kind == "ballot" and person is not None
    }
    return Counter(film for film, _person in pairs)


def main() -> None:
    # All people and films are fictional; labels illustrate source relationships.
    rows = (
        ("X", "alice", "film-comment", "ballot"),
        ("X", "bob", "slant", "ballot"),
        ("X", "alice", "slant", "ballot"),
        ("X", None, "bfi", "aggregate"),
        ("X", None, "tspdt", "aggregate"),
        ("X", None, "unknown-critic", "ballot"),
        ("Y", "carol", "bfi", "ballot"),
        ("Y", "dan", "film-comment", "ballot"),
        ("Y", "erin", "senses", "ballot"),
    )
    raw = Counter(film for film, _person, _source, _kind in rows)
    independent = independent_counts(rows)
    unresolved = sum(person is None and kind == "ballot" for _film, person, _source, kind in rows)

    assert raw == {"X": 6, "Y": 3}
    assert independent == {"X": 2, "Y": 3}
    assert independent_counts(rows + rows) == independent
    assert unresolved == 1
    print(
        f"raw={dict(raw)} independent={dict(sorted(independent.items()))} unresolved={unresolved}"
    )


if __name__ == "__main__":
    main()
