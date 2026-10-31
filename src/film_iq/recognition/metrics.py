"""Reception values preserve population, original units and observed sample sizes."""

from dataclasses import dataclass
from datetime import date
from typing import ClassVar, Literal

from film_iq.recognition.checks import count, day, names
from film_iq.recognition.metric_checks import measurement


@dataclass(frozen=True)
class ReceptionMetric:
    kind: ClassVar[str] = "reception_metric"
    measure: str
    population: Literal["critics", "audience"]
    metric: Literal["positivity", "mean", "count", "grade"]
    value: int | float | str | None
    unit: str | None
    sample_count: int | None = None
    observed_on: date | None = None

    def __post_init__(self) -> None:
        names(self.measure)
        if self.population not in {"critics", "audience"}:
            raise ValueError("reception population must be critics or audience")
        measurement(self.metric, self.value, self.unit)
        count(self.sample_count)
        day(self.observed_on)
