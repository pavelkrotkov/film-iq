"""Transparent public support ordering without imputing unknown evidence as zero."""

from typing import Literal

Order = Literal["source", "public-support"]


def public_support(item: dict) -> int | None:
    evidence = item["external_critical_recognition"]
    return evidence["independent_count"] if evidence is not None else None


def ordered_suggestions(items: list[dict], order: Order = "source") -> list[dict]:
    if order == "source":
        return list(items)
    if order != "public-support":
        raise ValueError("discovery order must be source or public-support")
    known = sorted(
        (item for item in items if public_support(item) is not None),
        key=lambda item: -item["external_critical_recognition"]["independent_count"],
    )
    ranked = iter(known)
    return [next(ranked) if public_support(item) is not None else item for item in items]


def ordering_note(order: Order) -> str:
    if order == "source":
        return "Source selection order; no fitted personal ranking."
    return (
        "Public-support-v1: reviewed evidence-group count only, highest first; ties retain "
        "source order. Unknown support keeps its source-order slot, never becomes zero. "
        "Ranks remain separate source reasons. Exposure, quality and personal fit are not calibrated."
    )
