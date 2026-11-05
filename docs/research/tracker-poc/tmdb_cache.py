"""Opt-in TMDB cache primitives; no policy is selected or provider contacted here.

The caller must supply a reviewed policy and an isolated project-local cache
directory. One writer and offline purge are assumed; backups are separately
inventoried by the operator. These functions never touch tracker records.
An independently retained authority file records chronological policy changes
and per-film purge watermarks. Cache restore requires that latest authority;
losing or rolling back both copies cannot be detected. Authority files contain
film IDs and are private. Expiry while stopped requires an external purge.
"""

import json
import os
import re
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from film_iq.retention import CachePolicy, status

VERSION = "tracker-poc-tmdb-cache-v1"
MAX_AGE = timedelta(days=180)
NAME = re.compile(r"^[1-9][0-9]{0,9}\.json(?:\.tmp)?$")
KINDS = {"subscription", "rent", "buy", "free", "ads"}
AUTHORITY_VERSION = "tracker-poc-tmdb-authority-v1"
CACHE_ID = ".cache-instance"


def _time(value: datetime | str) -> datetime:
    result = datetime.fromisoformat(value) if isinstance(value, str) else value
    if not isinstance(result, datetime) or result.utcoffset() is None:
        raise ValueError("A timezone-aware timestamp is required")
    return result.astimezone(UTC)


def _policy(policy: CachePolicy, now: datetime) -> str:
    if (
        not isinstance(policy, CachePolicy)
        or policy.source != "TMDB"
        or type(policy.allowed) is not bool
        or type(policy.terminated) is not bool
        or not isinstance(policy.version, str)
        or not policy.version.strip()
    ):
        raise ValueError("A reviewed TMDB policy is required")
    return status(policy, _time(now))


def _path(root: Path, ident: int) -> Path:
    if type(ident) is not int or not 0 < ident <= 2_147_483_647:
        raise ValueError("Invalid film identifier")
    return root / f"{ident}.json"


def _url(value: Any, host: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError("Invalid provider URL")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname != host
        or parsed.port is not None
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise ValueError("Invalid provider URL")
    return value


def _metadata(film: dict[str, Any]) -> dict[str, Any]:
    title = film.get("title")
    if not isinstance(title, str) or not title.strip() or len(title) > 512:
        raise ValueError("Invalid film title")
    output: dict[str, Any] = {"title": title}
    for name, limit in (("original_title", 512), ("synopsis", 30000)):
        value = film.get(name)
        if value is not None and (not isinstance(value, str) or len(value) > limit):
            raise ValueError("Invalid film metadata")
        output[name] = value if value and value.strip() else None
    year = film.get("year")
    if year is not None and (type(year) is not int or not 1 <= year <= 9999):
        raise ValueError("Invalid release year")
    output["year"] = year
    for name in ("genres", "directors"):
        values = film.get(name)
        if values is not None and (
            not isinstance(values, (list, tuple))
            or len(values) > 30
            or any(not isinstance(v, str) or not v.strip() or len(v) > 256 for v in values)
        ):
            raise ValueError("Invalid film metadata")
        output[name] = list(values) if values is not None else None
    poster = _url(film.get("poster_url"), "image.tmdb.org")
    if poster is not None:
        parsed = urlsplit(poster)
        if parsed.query or not re.fullmatch(r"/t/p/w500/[A-Za-z0-9_.-]+", parsed.path):
            raise ValueError("Invalid poster path")
        output["poster_path"] = parsed.path.removeprefix("/t/p/w500")
    else:
        output["poster_path"] = None
    output["imdb_title_url"] = _url(film.get("imdb_title_url"), "www.imdb.com")
    return output


def _availability(value: Any, now: datetime) -> tuple[datetime, dict[str, Any]] | None:
    if not isinstance(value, dict) or value.get("status") not in ("complete", "partial"):
        return None
    try:
        checked = _time(value["checked_at"])
        if checked > now:
            return None
        offers = value.get("offers")
        if not isinstance(offers, list) or len(offers) > 500:
            return None
        cleaned = []
        for offer in offers:
            if not isinstance(offer, dict) or set(offer) != {"provider", "kind"}:
                return None
            provider, kind = offer["provider"], offer["kind"]
            if (
                not isinstance(provider, str)
                or not provider.strip()
                or len(provider) > 256
                or kind not in KINDS
            ):
                return None
            cleaned.append({"provider": provider, "kind": kind})
        link = _url(value.get("provider_url"), "www.themoviedb.org")
        return checked, {"status": value["status"], "offers": cleaned, "provider_url": link}
    except (ValueError, TypeError, KeyError):
        return None


def _section(policy: CachePolicy, observed: datetime, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "observed_at": observed.isoformat(),
        "expires_at": min(observed + MAX_AGE, _time(policy.expires_at)).isoformat(),
        "policy_version": policy.version,
        "rights_evidence": policy.rights_evidence,
        "attribution": policy.attribution,
        "data": data,
    }


def _load(path: Path, ident: int) -> dict[str, Any]:
    if path.is_symlink():
        raise ValueError("Cache file must not be a symlink")
    if not path.exists():
        return {
            "version": VERSION,
            "source": "TMDB",
            "tmdb_id": ident,
            "metadata": None,
            "availability": None,
        }
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or set(value) != {"version", "source", "tmdb_id", "metadata", "availability"}
        or value["version"] != VERSION
        or value["source"] != "TMDB"
        or type(value["tmdb_id"]) is not int
        or value["tmdb_id"] != ident
    ):
        raise ValueError("Invalid cache record")
    for name in ("metadata", "availability"):
        item = value[name]
        if item is not None:
            if (
                not isinstance(item, dict)
                or set(item)
                != {
                    "observed_at",
                    "expires_at",
                    "policy_version",
                    "rights_evidence",
                    "attribution",
                    "data",
                }
                or not isinstance(item["data"], dict)
            ):
                raise ValueError("Invalid cache section")
            observed, expires = _time(item["observed_at"]), _time(item["expires_at"])
            if (
                expires <= observed
                or expires - observed > MAX_AGE
                or any(
                    not isinstance(item[k], str) or not item[k].strip()
                    for k in ("policy_version", "rights_evidence", "attribution")
                )
            ):
                raise ValueError("Invalid cache section")
            data = item["data"]
            if name == "metadata":
                poster = data.get("poster_path")
                source = {
                    **data,
                    "poster_url": f"https://image.tmdb.org/t/p/w500{poster}"
                    if isinstance(poster, str)
                    else poster,
                }
                if _metadata(source) != data:
                    raise ValueError("Invalid cached metadata")
            else:
                parsed = _availability({**data, "checked_at": observed.isoformat()}, observed)
                if parsed is None or parsed[1] != data:
                    raise ValueError("Invalid cached availability")
    return value


def _save(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.is_symlink():
        raise ValueError("Cache temporary file must not be a symlink")
    created = False
    try:
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        created = True
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            os.fchmod(output.fileno(), 0o600)
            json.dump(value, output, ensure_ascii=False, separators=(",", ":"))
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if created:
            temporary.unlink(missing_ok=True)


def _policy_record(policy: CachePolicy, effective: datetime) -> dict[str, Any]:
    _policy(policy, effective)
    return {
        "effective_at": _time(effective).isoformat(),
        "source": policy.source,
        "allowed": policy.allowed,
        "rights_evidence": policy.rights_evidence,
        "attribution": policy.attribution,
        "expires_at": _time(policy.expires_at).isoformat(),
        "terminated": policy.terminated,
        "policy_version": policy.version,
    }


def _authority(path: Path) -> dict[str, Any]:
    """Read independently retained policy history and per-film purge marks."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("The independent cache authority is unavailable")
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or set(value) != {"version", "cache_id", "policies", "films"}
        or value["version"] != AUTHORITY_VERSION
        or not isinstance(value["cache_id"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", value["cache_id"])
        or not isinstance(value["policies"], list)
        or not value["policies"]
        or not isinstance(value["films"], dict)
    ):
        raise ValueError("Invalid cache authority")
    previous = None
    for item in value["policies"]:
        if not isinstance(item, dict) or set(item) != {
            "effective_at",
            "source",
            "allowed",
            "rights_evidence",
            "attribution",
            "expires_at",
            "terminated",
            "policy_version",
        }:
            raise ValueError("Invalid cache policy history")
        effective = _time(item["effective_at"])
        if previous is not None and effective <= previous:
            raise ValueError("Invalid cache policy order")
        previous = effective
        policy = CachePolicy(
            item["source"],
            item["allowed"],
            item["rights_evidence"],
            item["attribution"],
            _time(item["expires_at"]),
            item["terminated"],
            item["policy_version"],
        )
        if _policy_record(policy, effective) != item:
            raise ValueError("Invalid cache policy history")
    for key, marks in value["films"].items():
        if (
            not isinstance(key, str)
            or not re.fullmatch(r"[1-9][0-9]{0,9}", key)
            or int(key) > 2_147_483_647
            or not isinstance(marks, dict)
            or set(marks) != {"metadata", "availability"}
        ):
            raise ValueError("Invalid cache authority")
        for name in ("metadata", "availability"):
            if marks[name] is not None:
                _time(marks[name])
    return value


def initialize_authority(root: Path, authority: Path, policy: CachePolicy, now: datetime) -> None:
    """Bind a new empty cache to a separately retained authority, without replacing either."""
    root = root.resolve()
    if authority.resolve().is_relative_to(root):
        raise ValueError("Authority must be outside the cache root")
    if authority.exists() or authority.is_symlink():
        raise ValueError("Cache authority already exists")
    if root.exists() and any(root.iterdir()):
        raise ValueError("A new empty cache root is required")
    entry = _policy_record(policy, now)
    cache_id = secrets.token_hex(32)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    authority.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Exclusive creation makes interrupted setup fail closed on a subsequent run.
    for path, content in (
        (
            authority,
            json.dumps(
                {
                    "version": AUTHORITY_VERSION,
                    "cache_id": cache_id,
                    "policies": [entry],
                    "films": {},
                }
            ),
        ),
        (root / CACHE_ID, cache_id),
    ):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())


def record_policy(authority: Path, policy: CachePolicy, now: datetime) -> None:
    """Append a reviewed decision; every previous decision remains binding."""
    value = _authority(authority)
    entry = _policy_record(policy, now)
    latest = value["policies"][-1]
    if entry == latest:
        return
    if _time(entry["effective_at"]) <= _time(latest["effective_at"]):
        raise ValueError("Policy decisions must be recorded in chronological order")
    value["policies"].append(entry)
    _save(authority, value)


def _bound_authority(root: Path, path: Path, policy: CachePolicy, now: datetime) -> dict[str, Any]:
    if path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Authority must be outside the cache root")
    value = _authority(path)
    marker = root / CACHE_ID
    if (
        marker.is_symlink()
        or not marker.is_file()
        or marker.read_text(encoding="utf-8") != value["cache_id"]
    ):
        raise ValueError("Cache and authority do not match")
    latest = value["policies"][-1]
    if (
        _time(latest["effective_at"]) > _time(now)
        or _policy_record(policy, _time(latest["effective_at"])) != latest
    ):
        raise ValueError("The supplied policy is not the latest recorded decision")
    return value


def _deadline(authority: dict[str, Any], observed: datetime, now: datetime) -> datetime:
    """An observation keeps the shortest deadline imposed since it was acquired."""
    events = authority["policies"]
    active = [
        index for index, event in enumerate(events) if _time(event["effective_at"]) <= observed
    ]
    if not active:
        raise ValueError("Observation predates cache policy history")
    deadline = observed + MAX_AGE
    for event in events[active[-1] :]:
        effective = _time(event["effective_at"])
        if effective > now:
            break
        deadline = min(deadline, _time(event["expires_at"]))
        if not event["allowed"] or event["terminated"]:
            deadline = min(deadline, effective)
    return deadline


def _observation_policy(authority: dict[str, Any], observed: datetime) -> CachePolicy:
    """Return the recorded source decision active when an observation occurred."""
    events = [event for event in authority["policies"] if _time(event["effective_at"]) <= observed]
    if not events:
        raise ValueError("Observation predates cache policy history")
    event = events[-1]
    return CachePolicy(
        event["source"],
        event["allowed"],
        event["rights_evidence"],
        event["attribution"],
        _time(event["expires_at"]),
        event["terminated"],
        event["policy_version"],
    )


def _merge(old: dict[str, Any] | None, new: dict[str, Any]) -> dict[str, Any]:
    if old is None:
        return new
    prior, incoming = _time(old["observed_at"]), _time(new["observed_at"])
    if incoming < prior:
        return old
    if incoming == prior:
        if old["data"] != new["data"]:
            raise ValueError("Conflicting data for the same observation")
        return old
    return new


def write_film(
    root: Path,
    policy: CachePolicy,
    film: dict[str, Any],
    observed_at: datetime,
    now: datetime,
    *,
    authority: Path,
) -> dict[str, str]:
    """Store an observation and report if incomplete metadata was preserved instead."""
    now, observed = _time(now), _time(observed_at)
    journal = _bound_authority(root, authority, policy, now)
    if _policy(policy, now) != "retain":
        raise PermissionError("Source retention is not enabled")
    if observed > now or _deadline(journal, observed, now) <= now:
        raise ValueError("Metadata observation is not retainable")
    if not isinstance(film, dict):
        raise ValueError("Invalid film")
    ident = film.get("tmdb_id")
    if type(ident) is not int or not 0 < ident <= 2_147_483_647:
        raise ValueError("Invalid film identifier")
    path = _path(root, ident)
    metadata = _section(_observation_policy(journal, observed), observed, _metadata(film))
    metadata["expires_at"] = min(
        _time(metadata["expires_at"]), _deadline(journal, observed, now)
    ).isoformat()
    availability = _availability(film.get("availability"), now)
    current = _load(path, ident)
    marks = journal["films"].get(str(ident), {"metadata": None, "availability": None})
    if marks["metadata"] is not None and observed <= _time(marks["metadata"]):
        raise ValueError("Metadata observation was previously purged")
    for name in ("metadata", "availability"):
        if (
            current[name]
            and min(
                _time(current[name]["expires_at"]),
                _deadline(journal, _time(current[name]["observed_at"]), now),
            )
            <= now
        ):
            raise ValueError("Expired cache data requires purge before writing")
    previous_metadata = current["metadata"]
    missing_prior_fact = previous_metadata and any(
        previous_metadata["data"].get(key) not in (None, [])
        and metadata["data"].get(key) in (None, [])
        for key in (
            "original_title",
            "synopsis",
            "year",
            "genres",
            "directors",
            "poster_path",
            "imdb_title_url",
        )
    )
    if not missing_prior_fact:
        current["metadata"] = _merge(previous_metadata, metadata)
    metadata_result = (
        "preserved_incomplete"
        if missing_prior_fact
        else ("unchanged" if current["metadata"] == previous_metadata else "updated")
    )
    if availability:
        checked, data = availability
        try:
            availability_deadline = _deadline(journal, checked, now)
        except ValueError:
            availability_deadline = now
        if availability_deadline > now and (
            marks["availability"] is None or checked > _time(marks["availability"])
        ):
            previous = current["availability"]
            if not (
                previous
                and previous["data"].get("status") == "complete"
                and data["status"] == "partial"
            ):
                section = _section(_observation_policy(journal, checked), checked, data)
                section["expires_at"] = min(
                    _time(section["expires_at"]), availability_deadline
                ).isoformat()
                current["availability"] = _merge(previous, section)
    _save(path, current)
    return {"metadata": metadata_result}


def read_film(
    root: Path,
    policy: CachePolicy,
    tmdb_id: int,
    now: datetime,
    *,
    authority: Path,
) -> dict[str, Any] | None:
    """Return fresh sections only; this does not delete expired storage."""
    now = _time(now)
    journal = _bound_authority(root, authority, policy, now)
    if _policy(policy, now) != "retain":
        return None
    path = _path(root, tmdb_id)
    if not path.exists():
        return None
    record = _load(path, tmdb_id)
    marks = journal["films"].get(str(tmdb_id), {"metadata": None, "availability": None})
    for name in ("metadata", "availability"):
        section = record[name]
        if not section:
            continue
        deadline = min(
            _time(section["expires_at"]), _deadline(journal, _time(section["observed_at"]), now)
        )
        if not _time(section["observed_at"]) <= now < deadline or (
            marks[name] is not None and _time(section["observed_at"]) <= _time(marks[name])
        ):
            record[name] = None
        else:
            section["expires_at"] = deadline.isoformat()
    return record if record["metadata"] or record["availability"] else None


def inventory(root: Path) -> tuple[str, ...]:
    """List managed content and temporary names; the private authority is separate."""
    if not root.exists():
        return ()
    return tuple(
        sorted(
            path.name
            for path in root.iterdir()
            if NAME.fullmatch(path.name) and int(path.name.split(".", 1)[0]) <= 2_147_483_647
        )
    )


def purge_due(
    root: Path, policy: CachePolicy, now: datetime, *, authority: Path, execute: bool = False
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Preview or remove expired sections; run with all cache writers stopped."""
    now = _time(now)
    journal = _bound_authority(root, authority, policy, now)
    decision = _policy(policy, now)
    if decision == "blocked":
        return ()
    actions = []
    records = {}
    for name in inventory(root):
        path = root / name
        if path.is_symlink():
            raise ValueError("Managed cache path must not be a symlink")
        if name.endswith(".tmp"):
            sections = ("temporary",)
        else:
            try:
                record = _load(path, int(name[:-5]))
            except (ValueError, TypeError, KeyError, OverflowError):
                # An unreadable record is not evidence that it is expired.
                # Report it but still permit independently identified purges.
                sections = ("corrupt",) if decision == "purge_due" else ("corrupt_unresolved",)
            else:
                records[name] = record
                sections = tuple(
                    key
                    for key in ("metadata", "availability")
                    if record[key]
                    and (
                        decision == "purge_due"
                        or min(
                            _time(record[key]["expires_at"]),
                            _deadline(journal, _time(record[key]["observed_at"]), now),
                        )
                        <= now
                        or (
                            journal["films"].get(str(record["tmdb_id"]), {}).get(key) is not None
                            and _time(record[key]["observed_at"])
                            <= _time(journal["films"][str(record["tmdb_id"])][key])
                        )
                    )
                )
        if sections:
            actions.append((name, sections))
            if sections not in (("temporary",), ("corrupt",), ("corrupt_unresolved",)):
                marks = journal["films"].setdefault(
                    str(record["tmdb_id"]), {"metadata": None, "availability": None}
                )
                for key in sections:
                    observed = _time(record[key]["observed_at"])
                    if marks[key] is None or observed > _time(marks[key]):
                        marks[key] = observed.isoformat()
    if execute and actions:
        if any(
            sections not in (("temporary",), ("corrupt",), ("corrupt_unresolved",))
            for _, sections in actions
        ):
            _save(authority, journal)
        for name, sections in actions:
            path = root / name
            if sections == ("corrupt_unresolved",):
                continue
            if sections in (("temporary",), ("corrupt",)):
                path.unlink(missing_ok=True)
            else:
                record = records[name]
                for key in sections:
                    record[key] = None
                if record["metadata"] or record["availability"]:
                    _save(path, record)
                else:
                    path.unlink(missing_ok=True)
    return tuple(actions)
