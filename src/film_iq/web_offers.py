"""Every retained viewing variant keeps its source dates and entitlement uncertainty."""

from decimal import Decimal

from film_iq.availability.candidate_fields import EXPONENTS
from film_iq.web_html import fields, link, text


def viewing(item: dict) -> str:
    states = item.get("offer_states", [])
    if not states:
        return "<p>Streaming, rental prices and your plan entitlement are unknown. No new service or purchase is required to use FilmIQ.</p>"
    return (
        "<p>Source-reported US options. Recheck price, dates and your account plan with the service; these are not verified playback or purchase advice.</p>"
        + "".join(state_view(state) for state in states)
    )


def state_view(state: dict) -> str:
    # Failed/partial attempts remain distinct from the prior comparable report.
    latest, current = state["latest_attempt"], state["current"]
    body = record_view("Source report", current) if current else ""
    if latest != current:
        body += record_view("Latest attempt", latest)
    return body + f'<p class="muted">Attribution: {text(state["attribution"])}</p>'


def record_view(role: str, record: dict) -> str:
    claims = (
        "".join(claim_view(claim) for claim in record["assertions"])
        if record["work_reviewed"]
        else ""
    )
    return f"""<article class="evidence"><h3>{text(role)} · {text(record["source"])}</h3>
<p>Status: {text(record["status"])}; attempt recorded {text(record["checked_at"])}.</p>
{claims or "<p>No reviewed viewing links supplied. Availability remains unknown.</p>"}</article>"""


def claim_view(claim: dict) -> str:
    offer = claim["opportunity"]
    service = claim.get("service_name") or offer["service"]
    label = f"{service} · {offer['kind']}"
    heading = link(claim["url"], label) if claim["work_status"] == "reviewed" else text(label)
    facts = [
        ("Plan", offer["plan"]),
        ("Add-on", claim.get("addon_name") or offer["add_on"]),
        ("Price", price(claim)),
        ("Entitlement", claim["entitlement"]),
        ("Quality", offer["quality"]),
        ("Cut", offer["cut"]),
        ("Film/cut identity", claim["work_status"]),
    ]
    # Claim-check, effective-window and provider-detection dates are different.
    facts.extend(
        (label, claim.get(key))
        for label, key in (
            ("Claim checked", "checked_at"),
            ("Source says starts", "asserted_added_on"),
            ("Source says expires", "asserted_expires_at"),
            ("Provider detected", "provider_detected_at"),
            ("Provider says last day", "provider_last_day_at"),
        )
    )
    return f'<section class="offer"><h4>{heading}</h4>{fields(facts)}</section>'


def price(claim: dict) -> str:
    amount, currency = claim["price_minor"], claim["currency"]
    # Zero is a real observed amount; unknown prices remain explicitly unknown.
    if amount is None:
        return "unknown"
    if currency not in EXPONENTS:
        return f"{amount} minor units ({currency or 'currency unknown'})"
    exponent = EXPONENTS[currency]
    return f"{currency} {Decimal(amount).scaleb(-exponent):.{exponent}f}"
