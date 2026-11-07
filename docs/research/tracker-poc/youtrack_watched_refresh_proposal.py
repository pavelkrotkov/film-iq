"""Propose, but never apply, a newer complete Movary watched observation.

This offline experiment is not a YouTrack app schema or import endpoint. A
real handler must verify the entire stored property and caller visibility;
the existing visibility-filtered watched GET cannot establish completeness.
"""

import re
from copy import deepcopy
from datetime import date, datetime
from typing import Any

from kaneo_movary_mapping import mapping
from youtrack_enrich import custom_value

from film_iq.personal_identity import api_movies, index


def _time(value: object) -> datetime:
    try:
        if not isinstance(value, str):
            raise ValueError
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if instant.utcoffset() is None:
            raise ValueError
        return instant
    except (TypeError, ValueError):
        raise ValueError("Invalid observation time") from None


def _date(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _entry(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "watched",
        "tmdb_id",
        "played_watch_dates",
        "history_export_dates",
    }:
        raise ValueError("Invalid prior watched entry")
    ident, played, history = (
        value["tmdb_id"],
        value["played_watch_dates"],
        value["history_export_dates"],
    )
    if (
        value["watched"] is not True
        or (ident is not None and (type(ident) is not int or not 0 < ident <= 2147483647))
        or not isinstance(played, list)
        or not all(
            isinstance(event, dict)
            and set(event) == {"date", "plays"}
            and _date(event["date"])
            and type(event["plays"]) is int
            and event["plays"] > 0
            for event in played
        )
        or not isinstance(history, list)
        or not all(_date(day) for day in history)
    ):
        raise ValueError("Invalid prior watched entry")
    return value


def current_observation(
    source_snapshot: dict[str, Any],
    source_status: dict[str, Any],
    issues: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, int | None]]:
    """Validate complete source provenance and directly map current issue IDs."""
    provenance = source_snapshot.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("Complete Movary provenance is required")
    api = provenance.get("api")
    if not isinstance(api, dict) or not all(
        isinstance(api.get(name), list) for name in ("played", "history", "watchlist")
    ):
        raise ValueError("Complete Movary API collections are required")
    observation = mapping(source_snapshot, source_status)
    if observation["unresolved_history"]:
        raise ValueError("Unresolved watched history requires review")
    api_records = api_movies(api)
    history = index(provenance["history_csv"])
    expected = {
        ident
        for ident, record in api_records.items()
        if record.get("played") or record.get("history")
    } | set(history)
    if {int(ident) for ident in observation["films"]} != expected:
        raise ValueError("Watched snapshot disagrees with source provenance")
    by_issue: dict[str, int | None] = {}
    by_tmdb: dict[int, str] = {}
    for issue in issues:
        readable = issue.get("idReadable")
        if (
            not isinstance(readable, str)
            or not re.fullmatch(r"FILMREAL-[1-9]\d*", readable)
            or readable in by_issue
        ):
            raise ValueError("Unexpected or duplicate issue")
        ident = custom_value(issue, "FilmIQ TMDB ID")
        if ident is not None:
            if type(ident) is not int or not 0 < ident <= 2147483647 or ident in by_tmdb:
                raise ValueError("Duplicate or invalid issue identity")
            by_tmdb[ident] = readable
        by_issue[readable] = ident

    current: dict[str, dict[str, Any]] = {}
    for ident, events in observation["films"].items():
        source_id = int(ident)
        issue = by_tmdb.get(source_id)
        if issue is None:
            raise ValueError("A watched source identity has no unique issue")
        current[issue] = deepcopy(_entry({**events, "tmdb_id": source_id}))
    return {"observed_at": observation["observed_at"], "films": current}, by_issue


def prior_evidence(
    previous: dict[str, Any], by_issue: dict[str, int | None]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Validate the visible prior projection; the server must check full visibility."""
    if (
        previous.get("status") != "available"
        or previous.get("source") != "Movary"
        or not isinstance(previous.get("films"), dict)
    ):
        raise ValueError("Prior watched snapshot unavailable")
    old_at = previous.get("observed_at")
    _time(old_at)
    prior = previous["films"]
    if not set(prior).issubset(by_issue):
        raise ValueError("A prior watched issue is unavailable")
    prior_history = previous.get("historical", [])
    if not isinstance(prior_history, list):
        raise ValueError("Invalid historical evidence")
    historical = []
    for item in prior_history:
        if (
            not isinstance(item, dict)
            or set(item) != {"issue_id", "observed_at", "reason", "film"}
            or item["issue_id"] not in by_issue
            or item["reason"] not in ("unbound", "superseded")
            or _time(item["observed_at"]) > _time(old_at)
        ):
            raise ValueError("Invalid historical evidence")
        film = _entry(item["film"])
        if (item["reason"] == "unbound") != (film["tmdb_id"] is None):
            raise ValueError("Invalid historical evidence")
        historical.append(deepcopy(item))
    for value in prior.values():
        _entry(value)
    return prior, historical


def propose(
    source_snapshot: dict[str, Any],
    source_status: dict[str, Any],
    issues: list[dict[str, Any]],
    previous: dict[str, Any],
) -> dict[str, Any]:
    """Return a fictional-testable proposal; never change inputs or persist it."""
    observed, by_issue = current_observation(source_snapshot, source_status, issues)
    prior, historical = prior_evidence(previous, by_issue)
    old_at, new_at = previous.get("observed_at"), observed["observed_at"]
    if _time(new_at) <= _time(old_at):
        raise ValueError("A newer watched observation is required")
    current = observed["films"]
    for issue, value in prior.items():
        film = _entry(value)
        if film["tmdb_id"] is None or film != current.get(issue):
            historical.append(
                {
                    "issue_id": issue,
                    "observed_at": old_at,
                    "reason": "unbound" if film["tmdb_id"] is None else "superseded",
                    "film": deepcopy(film),
                }
            )

    return {
        "version": "filmiq-watched-refresh-proposal-v1",
        "project": "FILMREAL",
        "status": "available",
        "source": "Movary",
        "observed_at": new_at,
        "films": current,
        "historical": historical,
    }
