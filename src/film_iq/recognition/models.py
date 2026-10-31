"""Typed original facts; an institutional selection is never a critic ballot."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

from film_iq.recognition.awards import AwardOutcome as AwardOutcome
from film_iq.recognition.checks import day, names
from film_iq.recognition.metrics import ReceptionMetric as ReceptionMetric

SELECTIONS = {"unknown", "critic_selection", "institutional_selection", "registry_selection"}


@dataclass(frozen=True)
class Selection:
    kind: Literal["unknown", "critic_selection", "institutional_selection", "registry_selection"]
    event: str
    edition: str
    effective_on: date | None = None

    def __post_init__(self) -> None:
        if self.kind not in SELECTIONS:
            raise ValueError("unsupported selection kind")
        names(self.event, self.edition)
        day(self.effective_on)
