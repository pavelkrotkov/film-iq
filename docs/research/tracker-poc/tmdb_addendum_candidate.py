"""Offline candidate for a separately authorized, on-demand TMDb addendum.

This module cannot make requests or create approvals. Both bridges can opt in
to its per-request loader; they keep their existing behavior by default. An
operator must obtain authorization for the exact preview before creating an
addendum; a matching hash alone is not consent.
"""

import hashlib
import re
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path

approval = import_module("live_bridge")

POLICY_DEADLINE = datetime(2026, 12, 6, tzinfo=UTC)
PREVIEW_ENTRY = re.compile(r"^([12])\. .+ — TMDb ID `([1-9][0-9]*)`$", re.MULTILINE)


def on_demand_allowlist(
    original: bytes,
    manifest: bytes,
    watched_preview: bytes,
    addendum: bytes,
    addendum_preview: bytes,
    *,
    now: datetime,
) -> dict:
    """Validate both scopes, returning an in-memory allowlist for an on-demand caller.

    This is deliberately not a scheduler or an approval-artifact writer.
    The caller must ensure execution is actually user-initiated.
    """
    base = approval.validate_collection_approval(original, manifest, watched_preview)
    document = approval.decode_allowlist(addendum.decode("utf-8"))
    if not isinstance(document, dict) or set(document) != {
        "version",
        "scope",
        "allowed_ids",
        "preview_sha256",
        "expires_at",
    }:
        raise ValueError("Invalid addendum")
    ids = document["allowed_ids"]
    entries = PREVIEW_ENTRY.findall(addendum_preview.decode("utf-8"))
    preview_ids = [int(value) for _, value in entries]
    if (
        type(document["version"]) is not int
        or document["version"] != 1
        or document["scope"] != "on-demand"
        or not isinstance(ids, list)
        or len(ids) != 2
        or any(type(value) is not int or not 0 < value <= 2147483647 for value in ids)
        or len(set(ids)) != 2
        or len(preview_ids) != 2
        or [number for number, _ in entries] != ["1", "2"]
        or set(ids) != set(preview_ids)
        or not set(ids).isdisjoint(base)
        or document["preview_sha256"] != hashlib.sha256(addendum_preview).hexdigest()
    ):
        raise ValueError("Invalid addendum")
    try:
        expiry = datetime.fromisoformat(document["expires_at"].replace("Z", "+00:00"))
        if now.utcoffset() is None or expiry.utcoffset() is None:
            raise ValueError
        if not now < expiry <= POLICY_DEADLINE:
            raise ValueError
    except (AttributeError, TypeError, ValueError):
        raise ValueError("Invalid addendum expiry") from None
    return {
        "version": 1,
        "allowed_ids": sorted(base | set(ids)),
        "destinations": sorted(approval.DESTINATIONS),
    }


def load_on_demand_allowlist(original_path: Path, directory: Path) -> object:
    """Revalidate the addendum for each request; an invalid addendum adds no IDs.

    The existing 130-ID loader still applies when the optional scope is missing,
    invalid or expired. The configured process must only be used on demand.
    """
    original = original_path.read_bytes()
    base = approval.decode_allowlist(original.decode("utf-8"))
    approval.parse_allowlist(base)
    try:
        return on_demand_allowlist(
            original,
            (directory / "film-input.json").read_bytes(),
            (directory / "tmdb-watched-lookup-preview.md").read_bytes(),
            (directory / "tmdb-addendum-approval.json").read_bytes(),
            (directory / "tmdb-watchlist-two-id-lookup-preview-20261106.md").read_bytes(),
            now=datetime.now(UTC),
        )
    except (OSError, ValueError, TypeError):
        return base
