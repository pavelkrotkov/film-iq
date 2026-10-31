"""Date-only slots use the caller's assessment calendar day, never today's clock."""

from datetime import date, datetime

from film_iq.availability.validation import aware


def planning_dates(inputs: dict) -> list[date]:
    assessment = datetime.fromisoformat(inputs.get("assessed_at", inputs["checked_at"]))
    aware(assessment)
    dates = [date.fromisoformat(value) for value in inputs["dates"]]
    if any(day < assessment.date() for day in dates):
        raise ValueError("viewing dates must be on or after the assessment calendar day")
    return dates
