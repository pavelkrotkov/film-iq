"""The shared write boundary for native forms behind a configured private origin."""

from secrets import compare_digest
from urllib.parse import parse_qs, urlsplit


def normalize_origin(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Public origin must be an absolute HTTP(S) origin")
    if (
        parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Public origin cannot include credentials, path, query or fragment")
    return f"{parsed.scheme}://{parsed.netloc.lower()}"


def check_origin(environ, public_origin: str) -> None:
    # Proxy requests must retain the public Host; forwarded headers are untrusted.
    host = urlsplit(public_origin).netloc
    if environ.get("HTTP_ORIGIN") != public_origin or environ.get("HTTP_HOST") != host:
        raise PermissionError("Open FilmIQ at its configured private URL before changing films.")


def read_form(environ, csrf_token: str, public_origin: str) -> dict[str, str]:
    check_origin(environ, public_origin)
    if environ.get("CONTENT_TYPE", "").split(";", 1)[0] != "application/x-www-form-urlencoded":
        raise ValueError("Expected a native HTML form")
    length = int(environ.get("CONTENT_LENGTH") or "0")
    if not 0 < length <= 16384:
        raise ValueError("Invalid form size")
    values = parse_qs(
        environ["wsgi.input"].read(length).decode(),
        keep_blank_values=True,
        strict_parsing=True,
        max_num_fields=12,
    )
    if any(len(items) != 1 for items in values.values()):
        raise ValueError("Repeated form fields are not supported")
    fields = {key: items[0] for key, items in values.items()}
    if not compare_digest(fields.pop("csrf_token", "").encode(), csrf_token.encode()):
        raise PermissionError("This form expired. Reload the film page and try again.")
    return fields
