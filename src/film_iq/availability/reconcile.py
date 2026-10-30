"""Pure source-snapshot comparison; no polling, provider history or alerts."""

from .fetch import Fetch
from .opportunity import Change, Opportunity


def changes(previous: Fetch, current: Fetch) -> tuple[Change, ...]:
    """Compare only reviewed complete same-plan scopes; absence is source-specific."""
    if previous.scope != current.scope or previous.plan_scope != current.plan_scope:
        raise ValueError("fetch scopes differ")
    if current.checked_at < previous.checked_at:
        raise ValueError("fetch time moved backwards")
    if not _comparable(previous, current):
        return ()
    old = _offered(previous)
    new = _offered(current)
    events = [("source_first_seen", item) for item in new - old]
    events += [("source_absent", item) for item in old - new]
    return tuple(
        Change(kind, item, current.source, current.checked_at)
        for kind, item in sorted(events, key=repr)
    )


def _comparable(previous: Fetch, current: Fetch) -> bool:
    return (
        previous.status == current.status == "complete"
        and _reviewed(previous)
        and _reviewed(current)
        and current.plan_scope is not None
    )


def _offered(fetch: Fetch) -> set[Opportunity]:
    return {item.opportunity for item in fetch.assertions}


def _reviewed(fetch: Fetch) -> bool:
    return fetch.work_reviewed and all(item.work_status == "reviewed" for item in fetch.assertions)
