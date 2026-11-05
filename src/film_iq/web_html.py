"""Small escaped HTML helpers; source URLs never become executable schemes."""

from html import escape
from urllib.parse import urlsplit


def text(value: object) -> str:
    return escape("unknown" if value is None else str(value), quote=True)


def link(url: str | None, label: object) -> str:
    try:
        parts = urlsplit(url or "")
    except ValueError:
        return text(label)
    safe = parts.scheme in {"http", "https"} and parts.hostname and not parts.username
    if not safe:
        return text(label)
    return f'<a href="{text(url)}" rel="noreferrer">{text(label)} ↗</a>'


def fields(values: list[tuple[str, object]]) -> str:
    return (
        '<dl class="facts">'
        + "".join(
            f"<div><dt>{text(label)}</dt><dd>{text(value)}</dd></div>" for label, value in values
        )
        + "</dl>"
    )


def title(item: dict) -> str:
    return (item.get("display") or {}).get("title") or item["raw_title"]


def film_meta(item: dict) -> str:
    display = item.get("display") or {}
    year = (display.get("release_date") or "")[:4] or item["year"]
    director = ", ".join(display.get("directors", [])) or item["director"]
    minutes = display.get("runtime_minutes")
    return " · ".join(
        text(value) for value in (year, director, f"{minutes} min" if minutes else None) if value
    )
