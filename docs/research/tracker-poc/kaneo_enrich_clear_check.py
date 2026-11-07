"""Exercise fixture backfill without a tracker or browser session."""

from unittest.mock import patch
from urllib.request import build_opener

from enrichment import FilmMetadata
from kaneo_enrich import KaneoBackend


def main() -> None:
    backend = KaneoBackend.__new__(KaneoBackend)
    backend.base, backend.project, backend.opener = "fictional", "project", build_opener()
    backend.fields = {"identity": "identity", "year": "year", "genre": "genre"}
    rows = [
        {"taskId": "film", "fieldId": "identity", "value": "42"},
        {"taskId": "film", "fieldId": "genre", "value": ""},
    ]
    writes = []

    def request(_opener, _base, path, body=None, method=None):
        if path == "/custom-field/project/project/values":
            return rows
        writes.append((path, body, method))
        return {}

    film = FilmMetadata(42, "Fictional film", "Fictional synopsis", 2001, "Drama")
    with patch("kaneo_enrich.call", request):
        assert backend.ensure_film(film) == "film"
    assert writes == [
        (
            "/custom-field/value",
            {"taskId": "film", "fieldId": "year", "value": "2001"},
            "PUT",
        )
    ], "untouched year is filled, but explicitly cleared genre is preserved"
    print("Fictional Kaneo backfill preserves explicit clears")


if __name__ == "__main__":
    main()
