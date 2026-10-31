"""Canonical local observation serialization, preserving explicit unknown fields."""

import json
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256

from film_iq.availability.assertion import Assertion
from film_iq.availability.fetch import Fetch
from film_iq.availability.opportunity import Opportunity
from film_iq.availability.validation import aware
from film_iq.retention import CachePolicy


def timestamp(value: datetime) -> str:
    aware(value)
    return value.astimezone(UTC).isoformat()


def encode(value) -> str:
    return json.dumps(asdict(value), sort_keys=True, ensure_ascii=False, default=timestamp)


def key(value: str) -> str:
    return sha256(value.encode()).hexdigest()


def scope_key(fetch: Fetch) -> str:
    return key(json.dumps((*fetch.scope, fetch.plan_scope)))


def decode_fetch(payload: str) -> Fetch:
    data = json.loads(payload)
    data["checked_at"] = datetime.fromisoformat(data["checked_at"])
    data["assertions"] = tuple(decode_assertion(item) for item in data["assertions"])
    return Fetch(**data)


def decode_assertion(data: dict) -> Assertion:
    data = dict(data)
    data["opportunity"] = Opportunity(**data["opportunity"])
    for field in ("checked_at", "asserted_added_on", "asserted_expires_at"):
        if data.get(field) is not None:
            data[field] = datetime.fromisoformat(data[field])
    return Assertion(**data)


def decode_policy(payload: str) -> CachePolicy:
    data = json.loads(payload)
    data["expires_at"] = datetime.fromisoformat(data["expires_at"])
    if type(data["allowed"]) is not bool or type(data.get("terminated", False)) is not bool:
        raise ValueError("policy allowed/terminated must be booleans")
    if data.get("version", "cache-policy-v1") != "cache-policy-v1":
        raise ValueError("unsupported cache policy version")
    return CachePolicy(**data)
