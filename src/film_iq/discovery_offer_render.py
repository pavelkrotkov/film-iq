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
        f"- {role} by {record['source']} (attempt recorded {_when(record['checked_at'])}): {details}. Reported options; verify with the service."
    ]


def _reviewed(record: dict, item: dict) -> bool:
    return record["work_reviewed"] and item["work_status"] == "reviewed"


def _link(item: dict) -> str:
    offer = item["opportunity"]
    plan = offer["plan"]
    if plan is None and offer["kind"] in {"subscription", "add-on"}:
        plan = "tier unknown"
    service = item.get("service_name") or f"service ID {offer['service']}"
    addon = item.get("addon_name") or (f"add-on ID {offer['add_on']}" if offer["add_on"] else None)
    tier = " / ".join(filter(None, (service, plan, addon)))
    bounds = [f"claim checked {_when(item['checked_at'])}"]
    bounds.extend(
        f"{label} {item[key]}"
        for key, label in (
            ("asserted_added_on", "source says starts"),
            ("asserted_expires_at", "source says expires"),
            ("provider_detected_at", "provider detected"),
            ("provider_last_day_at", "provider says last day"),
        )
        if item.get(key) is not None
    )
    return f"[{tier} — {offer['kind']}]({item['url']}) ({'; '.join(bounds)})"


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


def _when(value: str) -> str:
    return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M %Z")
