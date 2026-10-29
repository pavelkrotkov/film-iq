"""Planner input and result types."""

from dataclasses import dataclass
from datetime import date
from typing import Literal


@dataclass(frozen=True)
class Film:
    id: int
    title: str
    minutes: int
    score: float
    watched: bool = False
    utility_assumption: str = ""


@dataclass(frozen=True)
class Access:
    film_id: int
    provider_id: int
    kind: Literal["subscription", "free", "ads", "rent", "buy", "add-on"]
    entitlement: Literal["confirmed", "unconfirmed", "unavailable_on_plan"]
    price_cents: int | None = None
    expires: date | None = None


@dataclass(frozen=True)
class Choice:
    film: Film
    offer: Access
    viewing_date: date


@dataclass(frozen=True)
class Plan:
    option: str
    choices: tuple[Choice, ...]
    total_minutes: int
    cost_cents: int
    utility: float
    assumptions: str
