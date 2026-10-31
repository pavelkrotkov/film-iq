"""Typed sections do not blend unlike recognition or change JSON/source facts."""

import json
import re
from copy import deepcopy

from discovery_fixtures import accept_source, cohort, fresh_status, snapshot

from film_iq.discovery import build_discovery
from film_iq.discovery_render import markdown
from film_iq.discovery_sections import SECTIONS


def pick(base, identifier, kind):
    return {
        **deepcopy(base),
        "tmdb_id": identifier,
        "raw_title": f"Fixture {identifier}",
        "evidence_kind": kind,
    }


def test_distinct_sections_keep_every_pick_once_with_all_multi_type_reasons(evidence_db):
    accept_source(evidence_db)
    report = build_discovery(cohort(), snapshot(), db=evidence_db, refresh_status=fresh_status())
    base = report["suggested_unwatched"][0]
    award, critic, preservation, other = (
        pick(base, i, kind)
        for i, kind in enumerate(
            ("award_outcome", "critic_selection", "registry_selection", "unknown"), 1
        )
    )
    critic["source_reasons"] = [
        deepcopy(critic),
        {**deepcopy(award), "ballot_scope": "Additional award source"},
    ]
    critic["external_critical_recognition"] = {"independent_count": 2}
    second_critic = pick(base, 5, "critic_selection")
    report["suggested_unwatched"] = [award, critic, preservation, other, second_critic]
    report["candidates"] = report["suggested_unwatched"]
    report["ordering"] = {"policy": "public-support", "explanation": "Fixture ordering"}
    before = json.dumps(report, sort_keys=True, default=str)
    rendered = markdown(report)
    main = rendered.split("<details>", 1)[0]
    assert re.findall(r"#### \[Fixture (\d+)", main) == ["2", "5", "1", "3", "4"]
    assert [main.index(f"### {name}") for name in SECTIONS] == sorted(
        main.index(f"### {name}") for name in SECTIONS
    )
    assert "Additional award source" in main and "Critic-list choices use" in main
    assert json.dumps(report, sort_keys=True, default=str) == before
