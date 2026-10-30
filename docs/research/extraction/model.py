"""Synthetic source entries and evaluation results."""

from dataclasses import dataclass
from typing import TypedDict


@dataclass(frozen=True)
class Entry:
    key: str
    title: str
    rank: int | None
    tie: str | None
    category: str
    lineage: str


class Evaluation(TypedDict):
    precision: float | None
    recall: float
    fields: dict[str, float | None]
    complete: bool
