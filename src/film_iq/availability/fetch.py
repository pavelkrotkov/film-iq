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
    # Public response context is not an account tier or an entitlement assertion.
    catalog_scope: Literal["public_country"] | None = None

    def __post_init__(self) -> None:
        aware(self.checked_at)
        if self.status not in {"complete", "partial", "unknown"}:
            raise ValueError("unsupported fetch status")
        source_scope(self.source, self.film_id, self.country, self.plan_scope)
        _comparison_context(self.plan_scope, self.catalog_scope)
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

    @property
    def has_comparison_scope(self) -> bool:
        return self.plan_scope is not None or self.catalog_scope == "public_country"


def scope(item: Assertion) -> tuple[str, int, str]:
    return item.source, item.opportunity.film_id, item.opportunity.country


def _comparison_context(plan: str | None, catalog: str | None) -> None:
    if catalog not in {None, "public_country"} or (catalog is not None and plan is not None):
        raise ValueError("choose one explicit public catalog or account-plan scope")
