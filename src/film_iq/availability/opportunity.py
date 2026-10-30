"""Provider-neutral opportunity identity; source assertions are stored separately."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from .validation import code, optional_names, positive_id, required

OfferKind = Literal["subscription", "rent", "buy", "free", "ads", "add-on", "library"]
KINDS = {"subscription", "rent", "buy", "free", "ads", "add-on", "library"}


@dataclass(frozen=True)
class Opportunity:
    film_id: int
    service: str
    kind: OfferKind
    country: str
    plan: str | None = None
    add_on: str | None = None
    quality: str | None = None
    cut: str | None = None

    def __post_init__(self) -> None:
        positive_id(self.film_id)
        required(self.service)
        code(self.country, 2)
        optional_names((self.plan, self.add_on, self.quality, self.cut))
        if self.kind not in KINDS:
            raise ValueError("unsupported opportunity kind")


@dataclass(frozen=True)
class Change:
    kind: str
    opportunity: Opportunity
    source: str
    observed_at: datetime
