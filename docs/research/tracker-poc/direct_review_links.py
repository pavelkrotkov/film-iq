"""Validate direct review links against the private discovery input without fetching pages."""

import re
from copy import deepcopy
from datetime import date, datetime
from ipaddress import ip_address
from urllib.parse import urlsplit

LINK_FIELDS = {"url", "provider", "type", "checked_at", "identity_evidence"}
LINK_TYPES = {"individual_critic_review", "review_aggregator_title_page"}
REQUIRED_EVIDENCE = {"input_title", "source_page_title", "input_source_year", "basis"}
DIRECTOR_FIELDS = {"director", "input_director"}
ALTERNATE_FIELDS = {"alternate_title_basis", "alternate_title_evidence_url"}
DIRECTOR_EVIDENCE = {"source_director_name", "director_basis"}
OPTIONAL_EVIDENCE = ALTERNATE_FIELDS | DIRECTOR_FIELDS | DIRECTOR_EVIDENCE | {"year_note"}


def _public_url(value: object) -> bool:
    if not isinstance(value, str) or value != value.strip() or any(c.isspace() for c in value):
        return False
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        if (
            not host
            or parsed.scheme not in {"http", "https"}
            or parsed.username is not None
            or parsed.password is not None
        ):
            return False
        if host.lower() == "localhost" or host.lower().endswith(
            (".localhost", ".local", ".internal", ".invalid", ".test", ".example")
        ):
            return False
        try:
            return ip_address(host).is_global
        except ValueError:
            return "." in host and not host.endswith(".")
    except ValueError:
        return False


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_review_manifest(manifest: dict, source: dict) -> list[dict]:
    """Validate the full batch and return sanitized eligible rows.

    A review page's title/director match does not independently verify its TMDB ID.
    """
    if (
        not isinstance(source, dict)
        or source.get("version") != "tracker-poc-private-film-input-v1"
        or not isinstance(source.get("films"), list)
    ):
        raise ValueError("invalid source manifest")
    source_by_id = {}
    for film in source["films"]:
        if (
            not isinstance(film, dict)
            or type(film.get("tmdb_id")) is not int
            or film["tmdb_id"] <= 0
            or film["tmdb_id"] in source_by_id
        ):
            raise ValueError("ambiguous source identity")
        source_by_id[film["tmdb_id"]] = film
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != 1
        or not isinstance(manifest.get("films"), list)
    ):
        raise ValueError("invalid review manifest")
    output, seen = [], set()
    for film in manifest["films"]:
        if not isinstance(film, dict) or set(film) != {"tmdb_id", "links"}:
            raise ValueError("invalid review film")
        ident = film["tmdb_id"]
        if type(ident) is not int or ident <= 0 or ident in seen:
            raise ValueError("ambiguous review identity")
        seen.add(ident)
        reference = source_by_id.get(ident)
        if reference is None:
            raise ValueError("identity not present in an eligible source")
        origin = reference.get("origin", [])
        provenance = reference.get("field_provenance", {}).get("tmdb_id")
        discovery = "discovery" in origin and provenance == "reviewed accepted identity match"
        watched = (
            "movary_watched" in origin
            and provenance == "Movary API or native export; not independently reverified here"
        )
        if not discovery and not watched:
            raise ValueError("identity not present in an eligible source")
        if not isinstance(film["links"], list) or not film["links"]:
            raise ValueError("review film has no links")
        if any(
            isinstance(link, dict)
            and isinstance(link.get("identity_evidence"), dict)
            and "release_note" in link["identity_evidence"]
            for link in film["links"]
        ):
            continue
        urls = set()
        public_links = []
        for link in film["links"]:
            if not isinstance(link, dict) or set(link) != LINK_FIELDS:
                raise ValueError("invalid review link fields")
            if (
                not _public_url(link["url"])
                or link["url"] in urls
                or not _nonempty(link["provider"])
                or link["type"] not in LINK_TYPES
            ):
                raise ValueError("invalid or duplicated review link")
            urls.add(link["url"])
            try:
                checked_at = link["checked_at"]
                if isinstance(checked_at, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", checked_at):
                    date.fromisoformat(checked_at)
                else:
                    checked = datetime.fromisoformat(checked_at.replace("Z", "+00:00"))
                    if checked.tzinfo is None or checked.utcoffset() is None:
                        raise ValueError("timezone missing")
            except (TypeError, ValueError, AttributeError) as exc:
                raise ValueError("invalid review timestamp") from exc
            evidence = link["identity_evidence"]
            if watched and not discovery:
                public_links.append(_sanitize_public_identity(link, reference))
                continue
            if (
                not isinstance(evidence, dict)
                or not REQUIRED_EVIDENCE.issubset(evidence)
                or set(evidence) - REQUIRED_EVIDENCE - OPTIONAL_EVIDENCE
            ):
                raise ValueError("invalid identity evidence fields")
            director_fields = DIRECTOR_FIELDS & set(evidence)
            if len(director_fields) != 1 or not all(
                _nonempty(evidence.get(k))
                for k in (
                    "input_title",
                    "source_page_title",
                    "basis",
                    next(iter(director_fields), ""),
                )
            ):
                raise ValueError("missing identity evidence")
            director = evidence[next(iter(director_fields))]
            if (
                evidence["input_title"] != reference.get("title")
                or director != reference.get("director")
                or evidence["input_source_year"] != reference.get("source_year")
            ):
                raise ValueError("identity evidence does not match source")
            if "year_note" in evidence and not _nonempty(evidence["year_note"]):
                raise ValueError("invalid year evidence")
            director_evidence = DIRECTOR_EVIDENCE & set(evidence)
            if director_evidence and (
                director_evidence != DIRECTOR_EVIDENCE
                or not all(_nonempty(evidence[key]) for key in DIRECTOR_EVIDENCE)
            ):
                raise ValueError("invalid director evidence")
            alternate = ALTERNATE_FIELDS & set(evidence)
            if alternate and (
                alternate != ALTERNATE_FIELDS
                or not _nonempty(evidence["alternate_title_basis"])
                or not _public_url(evidence["alternate_title_evidence_url"])
            ):
                raise ValueError("invalid alternate-title evidence")
            if (
                evidence["source_page_title"] != evidence["input_title"]
                and alternate != ALTERNATE_FIELDS
            ):
                raise ValueError("alternate title lacks evidence")
            directors = [director]
            if (
                evidence.get("source_director_name")
                and evidence["source_director_name"] not in directors
            ):
                directors.append(evidence["source_director_name"])
            public_links.append(_public_link(link, directors, evidence["input_source_year"]))
        output.append({"tmdb_id": ident, "links": public_links})
    return output


def _sanitize_public_identity(link: dict, reference: dict) -> dict:
    evidence = link.get("identity_evidence")
    required = {
        "input_title",
        "source_page_title",
        "source_directors",
        "tmdb_id_source_url",
        "basis",
        "mapping_limit",
        "personal_identity_caveat",
    }
    if (
        not isinstance(evidence, dict)
        or not required.issubset(evidence)
        or set(evidence) - required - {"source_year"}
    ):
        raise ValueError("invalid source identity evidence")
    if (
        evidence["input_title"] != reference.get("title")
        or evidence["source_page_title"] != evidence["input_title"]
    ):
        raise ValueError("source page title does not match input")
    if not all(
        _nonempty(evidence.get(k))
        for k in (
            "input_title",
            "source_page_title",
            "basis",
            "mapping_limit",
            "personal_identity_caveat",
        )
    ):
        raise ValueError("missing source identity evidence")
    directors = evidence["source_directors"]
    if (
        not isinstance(directors, list)
        or not directors
        or not all(_nonempty(director) for director in directors)
    ):
        raise ValueError("missing source directors")
    url = evidence["tmdb_id_source_url"]
    if not _public_url(url):
        raise ValueError("invalid crosswalk URL")
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in {"www.wikidata.org", "wikidata.org"}
        or not re.fullmatch(r"/wiki/Q[1-9][0-9]*", parsed.path)
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("invalid Wikidata crosswalk")
    year = evidence.get("source_year")
    if year is not None and (type(year) is not int or not 1800 <= year <= 2200):
        raise ValueError("invalid source year")
    if (
        year is not None
        and reference.get("source_year") is not None
        and year != reference["source_year"]
    ):
        raise ValueError("source year mismatch")
    return _public_link(link, directors, year)


def _public_link(link: dict, directors: list, year: int | None) -> dict:
    evidence = link["identity_evidence"]
    public_evidence = {
        "input_title": evidence["input_title"],
        "source_page_title": evidence["source_page_title"],
        "source_directors": deepcopy(directors),
        "source_year": year,
        "corroboration_urls": [],
        "identity_caveat": "Source-supplied film identity not independently verified.",
        "details_note": "Additional identity details are retained privately.",
    }
    result = {key: deepcopy(link[key]) for key in LINK_FIELDS if key != "identity_evidence"}
    result["identity_evidence"] = public_evidence
    if "movary" in str(result).casefold():
        raise ValueError("private source name in public evidence")
    return result


def review_manifest_conflict_count(manifest: dict, source: dict) -> int:
    """Count source records held back for manual identity review, without exposing them."""
    validated = validate_review_manifest(manifest, source)
    return len(manifest["films"]) - len(validated)


def validate_review_manifests(manifests: list[dict], source: dict) -> tuple[list[dict], int]:
    """Preflight all batches; a held-back identity cannot enter through another batch."""
    if not isinstance(manifests, list) or not manifests:
        raise ValueError("missing review batches")
    batches = [validate_review_manifest(manifest, source) for manifest in manifests]
    held = set()
    for manifest, rows in zip(manifests, batches, strict=True):
        eligible = {row["tmdb_id"] for row in rows}
        held.update(
            film["tmdb_id"] for film in manifest["films"] if film["tmdb_id"] not in eligible
        )
    combined = {}
    for rows in batches:
        for row in rows:
            ident = row["tmdb_id"]
            if ident in held:
                continue
            current = combined.setdefault(ident, {})
            for link in row["links"]:
                old = current.get(link["url"])
                if old is not None and old != link:
                    raise ValueError("conflicting review link between batches")
                current[link["url"]] = link
    return [
        {"tmdb_id": ident, "links": list(links.values())} for ident, links in combined.items()
    ], len(held)
