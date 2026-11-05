"""Link reviewed private crosswalks to Movary's supported native rating editor."""

import json
from pathlib import Path
from urllib.parse import quote

from film_iq.web_html import link


def native_editor(item: dict, snapshot: Path | None, settings: tuple[str, ...]) -> str:
    base, username, _ = settings
    if not snapshot or not base or not username:
        return ""
    data = json.loads(snapshot.read_text())
    movie = next((row for row in data["films"] if row["tmdb_id"] == item["tmdb_id"]), {})
    identifier = movie.get("movary_id")
    if type(identifier) is not int or identifier <= 0:
        return ""
    url = f"{base.rstrip('/')}/users/{quote(username, safe='')}/movies/{identifier}"
    return f"<p>{link(url, 'Edit enjoyment rating in Movary')}. Return here and refresh to see changes. Artistic merit remains separate.</p>"
