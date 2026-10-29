"""Preview a single recommendation before authorizing a future sync."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Preview:
    title: str
    tmdb_id: int

    def __post_init__(self) -> None:
        if not self.title.strip() or type(self.tmdb_id) is not int or self.tmdb_id <= 0:
            raise ValueError("a title and positive TMDB movie ID are required")


def approved_movie(preview: Preview, *, approved: bool = False) -> int:
    """Return the previewed TMDB ID only after an explicit approval."""
    if approved is not True:
        raise PermissionError("explicit approval of the preview is required")
    return preview.tmdb_id
