"""Sparse held-out evidence and an unseen writer cannot leak into training."""

import json
from copy import deepcopy
from pathlib import Path

from docs.research.scoring.period_holdout import evaluate, summarize


def sample():
    return json.loads(Path("docs/research/scoring/holdout-2024/observations.json").read_text())


def test_frozen_coverage_preserves_unknown_shorts_and_selection_categories():
    data = sample()
    assert len(data["rows"]) == 12
    inclusive = evaluate(data)
    assert inclusive["coverage"] == {
        "films": 12,
        "known_training": 5,
        "known_heldout": 3,
        "paired": 3,
    }
    assert inclusive["formats"]["short"]["known_training"] == 0
    assert evaluate(data, True)["coverage"]["paired"] == 1
    assert all(row["training_rank_sum"] is None for row in inclusive["observations"])


def test_provisional_rank_and_duplicate_carriers_cannot_change_verified_votes():
    data = sample()
    nickel = data["rows"][3]
    assert (summarize(nickel)["training_count"], summarize(nickel)["training_rank_sum"]) == (
        1,
        None,
    )
    duplicate = deepcopy(nickel)
    duplicate["records"] *= 2
    assert summarize(duplicate)["training_count"] == 1


def test_new_family_writer_is_held_out_without_using_2008_author_names():
    source = deepcopy(sample()["rows"][3])
    source["records"] = [
        {
            "critic": "New writer",
            "family": "new_yorker",
            "rank": 2,
            "category": "main",
            "status": "verified_automated",
        }
    ]
    result = summarize(source)
    assert result["training_count"] is None
    assert (result["heldout_count"], result["heldout_rank_sum"]) == (1, 0.5)
