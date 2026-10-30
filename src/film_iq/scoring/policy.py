"""Predeclared source/window preference; published ranks never set priority."""

from dataclasses import dataclass

from .models import Evidence


def _position(values: tuple[str, ...], value: str) -> int:
    return values.index(value) if value in values else len(values)


@dataclass(frozen=True)
class ScoringPolicy:
    """Lower source/window indexes win; remaining ties use canonical provenance.

    Source IDs fall back to list IDs for old fixtures. Windows are the exact
    eligibility strings: no release dates or eligible exposure are inferred.
    This default ordering is deterministic and uncalibrated, not optimal.
    """

    source_priority: tuple[str, ...] = ()
    window_priority: tuple[str, ...] = ()
    excluded_sources: tuple[str, ...] = ()
    excluded_families: tuple[str, ...] = ()

    def key(self, item: Evidence) -> tuple:
        source = item.source_id or item.list_id
        return (
            _position(self.source_priority, source),
            _position(self.window_priority, item.eligibility),
            source,
            item.eligibility,
            item.published.isoformat() if item.published else "",
            item.list_id,
            item.entry_id or "",
            item.document_id or "",
            item.revision_id or "",
        )

    def choose(
        self, items: set[Evidence], *, legacy: bool = False
    ) -> dict[tuple[str, str], Evidence]:
        from . import _evidence_key

        originals = [item for item in items if self.includes(item)]

        def key(item: Evidence) -> tuple:
            priority = (item.rank or float("inf"),) if legacy else self.key(item)
            return priority, _evidence_key(item)

        chosen: dict[tuple[str, str], Evidence] = {}
        for item in sorted(originals, key=key):
            group = (
                ("person", item.person_id)
                if item.person_id
                else ("evidence", item.independence_group)
            )
            previous = chosen.setdefault(group, item)
            if not legacy:
                self.check_conflict(previous, item)
        return chosen

    def includes(self, item: Evidence) -> bool:
        return (
            not item.derivative_of
            and item.lineage_kind != "derivative"
            and (item.source_id or item.list_id) not in self.excluded_sources
            and item.source_family not in self.excluded_families
        )

    def check_conflict(self, previous: Evidence, item: Evidence) -> None:
        if self.key(previous) == self.key(item) and previous.rank != item.rank:
            raise ValueError("Conflicting ranks at identical ballot priority need review")


DEFAULT_POLICY = ScoringPolicy()
