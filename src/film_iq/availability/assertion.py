"""A source's claims, without converting public discovery into personal access."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from .opportunity import Opportunity
from .validation import aware, code, price, required


@dataclass(frozen=True)
class Assertion:
    opportunity: Opportunity
    source: str
    checked_at: datetime
    url: str
    price_minor: int | None = None
    currency: str | None = None
    entitlement: Literal["confirmed", "unconfirmed", "unavailable_on_plan"] = "unconfirmed"
    work_status: Literal["reviewed", "unresolved", "cut_uncertain"] = "unresolved"
    asserted_added_on: datetime | None = None
    asserted_expires_at: datetime | None = None

    def __post_init__(self) -> None:
        aware(self.checked_at)
        for value in (self.asserted_added_on, self.asserted_expires_at):
            if value is not None:
                aware(value)
        required(self.source, self.url)
        price(self.price_minor)
        if self.entitlement not in {"confirmed", "unconfirmed", "unavailable_on_plan"}:
            raise ValueError("unsupported entitlement")
        if self.work_status not in {"reviewed", "unresolved", "cut_uncertain"}:
            raise ValueError("unsupported work status")
        if self.currency is not None:
            code(self.currency, 3)
