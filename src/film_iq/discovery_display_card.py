"""Show reviewed catalog aliases separately from unchanged source assertions."""

from film_iq.discovery_order import public_support


def text(value):
    return "unknown" if value is None else str(value).replace("\n", " ")


def title(item: dict) -> str:
    display = item.get("display")
    name = display["title"] if display else f"{text(item['raw_title'])} ({text(item['year'])})"
    director = ", ".join(display["directors"]) if display else text(item["director"])
    if item["identity_status"] == "reviewed" and item["tmdb_id"]:
        name = f"[{name}](https://www.themoviedb.org/movie/{item['tmdb_id']})"
    return f"{name} — {director}"


def display_details(item: dict) -> list[str]:
    display = item.get("display")
    lines = []
    if display:
        lines.append(
            f"Catalog release: {text(display['release_date'])}; runtime: {text(display['runtime_minutes'])} minutes. Source-listed year: {text(item['year'])}."
        )
    count = public_support(item)
    lines.append(
        "Public source support: not assessed; missing evidence stays unknown."
        if count is None
        else f"Public source support: {count} reviewed evidence groups; not a personal rating."
    )
    return lines
