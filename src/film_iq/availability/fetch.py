"""An explicitly scoped provider observation, including failed/partial attempts."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from .assertion import Assertion
from .validation import aware, source_scope


@dataclass(frozen=True)
class Fetch:
    source: str
    film_id: int
    country: str
    checked_at: datetime
    status: Literal["complete", "partial", "unknown"]
    assertions: tuple[Assertion, ...] = ()
    plan_scope: str | None = None
    work_reviewed: bool = False

    def __post_init__(self) -> None:
        aware(self.checked_at)
        if self.status not in {"complete", "partial", "unknown"}:
            raise ValueError("unsupported fetch status")
        source_scope(self.source, self.film_id, self.country, self.plan_scope)
        if self.plan_scope is not None and any(
            item.opportunity.kind in {"subscription", "add-on"}
            and item.opportunity.plan != self.plan_scope
            for item in self.assertions
        ):
            raise ValueError("assertion plan does not match the explicit fetch plan scope")
        if any(self.scope != scope(item) for item in self.assertions):
            raise ValueError("assertion outside fetch source/work/country scope")

    @property
    def scope(self) -> tuple[str, int, str]:
        return self.source, self.film_id, self.country


def scope(item: Assertion) -> tuple[str, int, str]:
    return item.source, item.opportunity.film_id, item.opportunity.country
