"""Extract already-reviewed source-document links from a FilmIQ discovery report.

The input must be produced by FilmIQ's discovery pipeline with an accepted
evidence database. Links identify published evidence, which may be a ballot,
award, or list rather than a film review. They do not prove full coverage.
"""

from urllib.parse import urlsplit


def _url(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return None
        if parsed.username is not None or parsed.password is not None:
            return None
        return value
    except ValueError:
        return None


def links_for_film(report: dict, tmdb_id: int) -> dict:
    """Return current accepted evidence for exactly one reviewed TMDB ID.

    This deliberately never consults title similarity, copies article text, or
    constructs a review-site URL. Unresolved identities and pending extractions
    are excluded; absence is unknown rather than a negative assessment.
    """
    if type(tmdb_id) is not int or tmdb_id <= 0:
        raise ValueError("tmdb_id must be a positive integer")
    if not isinstance(report, dict) or not isinstance(report.get("candidates"), list):
        raise ValueError("expected a FilmIQ discovery report with candidates")

    links = []
    seen = set()

    def add(row, *, component=False):
        url = _url(row.get("url") if component else row.get("source_url"))
        entry, revision = row.get("entry_id"), row.get("revision_id")
        if not url or not entry or not revision:
            return
        key = (entry, revision, url)
        if key in seen:
            return
        seen.add(key)
        links.append(
            {
                "url": url,
                "source_id": row.get("source_id"),
                "kind": row.get("kind" if component else "evidence_kind", "unknown"),
                "author": row.get("author" if component else "ballot_scope"),
                "edition": row.get("edition"),
                "published_at": row.get("published_at"),
                "rank": row.get("rank"),
                "tie": row.get("tie"),
                "locator": row.get("locator"),
                "lineage_kind": row.get("lineage_kind" if component else "source_lineage_kind"),
                "lineage": row.get("lineage" if component else "source_lineage"),
                "entry_id": entry,
                "revision_id": revision,
            }
        )

    for item in report["candidates"]:
        if not isinstance(item, dict):
            raise ValueError("invalid candidate record")
        if (
            type(item.get("tmdb_id")) is not int
            or item["tmdb_id"] != tmdb_id
            or item.get("identity_status") != "reviewed"
            or item.get("extraction_status") != "accepted"
        ):
            continue
        add(item)
        components = item.get("public_evidence_components", {})
        if not isinstance(components, dict):
            raise ValueError("invalid evidence components")
        for values in components.values():
            if not isinstance(values, list):
                continue  # Includes the interpretation string.
            for row in values:
                if (
                    isinstance(row, dict)
                    and type(row.get("tmdb_id")) is int
                    and row["tmdb_id"] == tmdb_id
                    and row.get("match_decision_id")
                ):
                    add(row, component=True)
    return {"tmdb_id": tmdb_id, "status": "available" if links else "unknown", "links": links}


def attach_evidence(manifest: dict, report: dict) -> dict:
    """Attach derived source-document links without changing personal/source fields.

    The returned manifest is a new object; `accepted_discovery_evidence` is an
    adapter-owned derived field that can be regenerated from the current report.
    Existing `source_reasons`, notes, and viewing history are left untouched.
    """
    if not isinstance(manifest, dict) or not isinstance(manifest.get("films"), list):
        raise ValueError("expected a manifest with a films list")
    if not isinstance(report, dict) or not isinstance(report.get("candidates"), list):
        raise ValueError("expected a FilmIQ discovery report with candidates")
    cached = {}
    films = []
    for film in manifest["films"]:
        if not isinstance(film, dict):
            raise ValueError("invalid film record")
        ident = film.get("tmdb_id")
        if type(ident) is int and ident > 0:
            if ident not in cached:
                cached[ident] = links_for_film(report, ident)
            evidence = cached[ident]
        else:
            evidence = {"tmdb_id": None, "status": "unknown", "links": []}
        films.append({**film, "accepted_discovery_evidence": evidence})
    return {**manifest, "films": films}
