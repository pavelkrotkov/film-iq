"""Compact film headings; exact catalog assertions remain in the audit."""


def text(value):
    return "unknown" if value is None else str(value).replace("\n", " ")


def title(item: dict) -> str:
    display = item.get("display")
    name = display["title"] if display else text(item["raw_title"])
    year = _year(display, item["year"])
    director = ", ".join(display["directors"]) if display else item["director"]
    name += f" ({year})" if year else ""
    if item["identity_status"] == "reviewed" and item["tmdb_id"]:
        name = f"[{name}](https://www.themoviedb.org/movie/{item['tmdb_id']})"
    return name + (f" — {director}" if director else "")


def display_details(item: dict) -> list[str]:
    minutes = (item.get("display") or {}).get("runtime_minutes")
    return [f"{minutes} min"] if minutes else []


def _year(display, source_year):
    return (display["release_date"] or "")[:4] if display else source_year
