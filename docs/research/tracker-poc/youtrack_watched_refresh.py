"""Preview or apply a newer complete local Movary snapshot to YouTrack.

This does not read Movary itself or update tracker issues. The v3 handler is a
candidate: do not run --apply until the matching app and rollback limitations
have been reviewed and tested. All source files remain private project data.
"""

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from youtrack_client import ROOT, YouTrackClient
from youtrack_watched_refresh_proposal import _time, current_observation, prior_evidence, propose

ENDPOINT = "extensionEndpoints/filmiq-poc/movary/"


def plan(snapshot: dict, status: dict, issues: list[dict], previous: dict) -> tuple[dict, dict]:
    """Build the server request and expected visible readback, without writing."""
    current, by_issue = current_observation(snapshot, status, issues)
    prior, history = prior_evidence(previous, by_issue)
    new_at = _time(current["observed_at"])
    old_at = _time(previous["observed_at"])
    if new_at > old_at:
        candidate = propose(snapshot, status, issues, previous)
        expected = {
            key: candidate[key]
            for key in ("status", "source", "observed_at", "films", "historical")
        }
    elif new_at == old_at and "historical" in previous and current["films"] == prior:
        # The handler must still check the full stored property's visibility.
        expected = {
            "status": "available",
            "source": "Movary",
            "observed_at": previous["observed_at"],
            "films": deepcopy(prior),
            "historical": history,
        }
    else:
        raise ValueError("Source observation is older or differs at the same time")
    payload = {
        "version": "youtrack-poc-movary-watched-v3",
        "project": "FILMREAL",
        "source": "Movary",
        "complete": True,
        "observed_at": current["observed_at"],
        "films": current["films"],
    }
    return payload, expected


def run(client: Any, snapshot: dict, status: dict, *, apply: bool = False) -> dict:
    """Use only the caller's supplied snapshot and existing tracker API client."""
    me = client.request("users/me", query={"fields": "id,login"})
    if me.get("login") != "admin":
        raise ValueError("The local tracker account is not the POC administrator")
    issues = client.pages(
        "issues",
        query={
            "fields": "id,idReadable,customFields(name,value)",
            "query": "project: {FILMREAL} sort by: {issue id} asc",
        },
    )
    previous = client.request(ENDPOINT + "watched", query={"project": "FILMREAL"})
    if not isinstance(previous, dict):
        raise ValueError("Prior watched snapshot unavailable")
    payload, expected = plan(snapshot, status, issues, previous)
    counts = {"films": len(payload["films"]), "historical": len(expected["historical"])}
    if not apply:
        return {"status": "preview", **counts}
    try:
        result = client.request(ENDPOINT + "refresh", body=payload)
    except Exception:
        raise RuntimeError("Refresh outcome unconfirmed; inspect before retrying") from None
    if (
        result.get("status") not in ("imported", "unchanged")
        or result.get("films") != counts["films"]
    ):
        raise RuntimeError("Refresh outcome unconfirmed; inspect before retrying")
    try:
        after = client.request(ENDPOINT + "watched", query={"project": "FILMREAL"})
    except Exception:
        raise RuntimeError("Refresh readback unavailable; inspect before retrying") from None
    if after != expected:
        raise RuntimeError("Refresh readback differs; inspect before retrying")
    return {"status": result["status"], **counts}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    snapshot = args.snapshot.resolve()
    project_root = ROOT.parent.parent if ROOT.parent.name == ".worktrees" else ROOT
    if not snapshot.is_relative_to(project_root):
        raise ValueError("Snapshot must be inside the selected project")
    data = json.loads(snapshot.read_text(encoding="utf-8"))
    status = json.loads(
        snapshot.with_suffix(snapshot.suffix + ".status").read_text(encoding="utf-8")
    )
    print(json.dumps(run(YouTrackClient(), data, status, apply=args.apply), sort_keys=True))


if __name__ == "__main__":
    main()
