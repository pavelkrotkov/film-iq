"""Awards retain category and recipient type; a performance prize is not Best Film."""

from dataclasses import dataclass
from datetime import date
from typing import ClassVar, Literal

from film_iq.recognition.checks import award_recipient, day, names


@dataclass(frozen=True)
class AwardOutcome:
    kind: ClassVar[str] = "award_outcome"
    event: str
    edition: str | None
    category: str | None
    outcome: Literal["selection", "competition", "nomination", "prize"] | None
    effective_on: date | None = None
    recipient: str | None = None
    recipient_kind: Literal["film", "person", "ensemble"] | None = None

    def __post_init__(self) -> None:
        names(self.event)
        if self.edition is not None:
            names(self.edition)
        if self.category is not None:
            names(self.category)
        if self.outcome not in {None, "selection", "competition", "nomination", "prize"}:
            raise ValueError("award selection, competition, nomination and prize are distinct")
        day(self.effective_on)
        award_recipient(self.recipient, self.recipient_kind)
