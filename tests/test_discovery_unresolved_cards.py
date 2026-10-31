"""Provisional IDs never hide separate unresolved source selections."""

from copy import deepcopy

from discovery_fixtures import cohort, snapshot

from film_iq.discovery import build_discovery
from film_iq.discovery_render import markdown


def test_same_provisional_id_keeps_both_unresolved_cards():
    selection = cohort()
    first = selection["candidates"][0]
    second = {**deepcopy(first), "raw_title": "Different unresolved film", "position": 2}
    selection.update(candidates=[first, second], total_candidates=2)
    output = build_discovery(selection, snapshot())
    rendered = markdown(output).split("<details>")[0]
    assert "### Synthetic Film" in rendered and "### Different unresolved film" in rendered
    assert rendered.count("Film identity needs review") == 2
    first = output["candidates"][0]
    first["identity_status"] = "reviewed"
    output["suggested_unwatched"] = [first]
    rendered = markdown(output).split("<details>")[0]
    assert "### Different unresolved film" in rendered
    assert rendered.count("Film identity needs review") == 1
