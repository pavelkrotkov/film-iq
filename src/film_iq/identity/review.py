"""Keep review corrections alongside the original decision."""

from .models import Decision


def review(
    history: tuple[Decision, ...], match: int | None, reviewer: str, evidence: str
) -> tuple[Decision, ...]:
    """Append a manual correction while retaining the original decision and observation."""
    if not history or not reviewer.strip() or not evidence.strip():
        raise ValueError("History, reviewer and evidence are required")
    previous = history[-1]
    if match is not None and match not in previous.candidates:
        raise ValueError("Reviewed match must be a recorded candidate")
    return (
        *history,
        Decision(
            previous.observation,
            previous.candidates,
            match,
            "manual",
            evidence,
            reviewer,
            candidate_evidence=previous.candidate_evidence,
        ),
    )
