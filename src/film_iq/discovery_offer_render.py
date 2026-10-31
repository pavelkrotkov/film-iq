"""Compact source-labelled links; full variant assertions remain in the audit."""

import json
from datetime import datetime


def offer_lines(item: dict) -> list[str]:
    return [line for state in item.get("offer_states", []) for line in _state_lines(state)]


def _state_lines(state: dict) -> list[str]:
    latest, baseline = state["latest_attempt"], state["current"]
    # An incomplete latest check must not replace the earlier report's timestamp.
    records = [("Source reported" if latest == baseline else "Previously reported", baseline)]
    if latest != baseline:
        records.append(
            (
                {
                    "complete": "Latest source report",
                    "partial": "Latest check incomplete",
                    "unknown": "Latest check inconclusive",
                }[latest["status"]],
                latest,
            )
        )
    lines = []
    for role, record in records:
        if record:
            lines.extend(_record_lines(role, record))
    return lines


def _record_lines(role: str, record: dict) -> list[str]:
    links = dict.fromkeys(_link(item) for item in record["assertions"] if _reviewed(record, item))
    details = "; ".join(links) or "no reviewed links supplied; availability stays unknown"
    return [
        f"- {role} by {record['source']} (checked {datetime.fromisoformat(record['checked_at']).strftime('%Y-%m-%d %H:%M %Z')}): {details}. Reported options; verify with the service."
    ]


def _reviewed(record: dict, item: dict) -> bool:
    return record["work_reviewed"] and item["work_status"] == "reviewed"


def _link(item: dict) -> str:
    offer = item["opportunity"]
    plan = offer["plan"]
    if plan is None and offer["kind"] in {"subscription", "add-on"}:
        plan = "tier unknown"
    tier = " / ".join(filter(None, (offer["service"], plan, offer["add_on"])))
    bounds = "; ".join(
        f"{label} {item[key]}"
        for key, label in (
            ("asserted_added_on", "source says starts"),
            ("asserted_expires_at", "source says expires"),
        )
        if item.get(key) is not None
    )
    return f"[{tier} — {offer['kind']}]({item['url']})" + (f" ({bounds})" if bounds else "")


def audit_offers(items: list[dict]) -> list[str]:
    states = {
        json.dumps(state, sort_keys=True)
        for item in items
        for state in item.get("offer_states", [])
    }
    if not states:
        return []
    return [
        "",
        "Retained offer assertions (all source/quality/price/add-on/cut variants and uncertainties):",
        "```json",
        "[" + ",\n".join(sorted(states)) + "]",
        "```",
    ]


def access_note(report: dict) -> str:
    if "offer_assessed_at" in report:
        return "Source-reported access is exploratory: recheck price, freshness, expiry and applicable account plan. Your scores appear only where available."
    return "Rental and streaming availability, price and plan entitlement have not been verified. Your scores appear only where available."


def offer_credits(items: list[dict]) -> list[str]:
    credits = sorted(
        {state["attribution"] for item in items for state in item.get("offer_states", [])}
    )
    return ["Offer source credits: " + "; ".join(credits)] if credits else []
