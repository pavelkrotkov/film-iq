"""Descriptive, revision-reported reception comparisons; never a 2008 backtest."""

import json
from pathlib import Path

from docs.research.scoring.real_evaluation import ranking, summarize
from docs.research.scoring.reception_baselines import (
    METRICS,
    WEIGHTS,
    coverage,
    groups,
    observation,
    weighted,
)

ROOT = Path(__file__).parent


def load_rows() -> tuple[list[dict], int]:
    ballots = json.loads((ROOT / "real_2008.json").read_text())["sources"]
    receptions = json.loads((ROOT / "reception_2008.json").read_text())["sources"]
    assert [(s["film"], s["revision"]) for s in ballots] == [
        (s["film"], s["revision"]) for s in receptions
    ]
    count_cap = max(summarize(source)["training_count"] or 0 for source in ballots)
    rows = [
        observation(ballot, reception, count_cap)
        for ballot, reception in zip(ballots, receptions, strict=True)
    ]
    return rows, count_cap


def evaluate() -> dict:
    rows, count_cap = load_rows()
    keys = (
        "training_count",
        "training_rank_sum",
        "rank_plus_named_award",
        "named_award",
        *METRICS,
        "full_weighted",
        "audience_omitted",
        "list_critic_only",
    )
    return {
        "count_normalizer_training_only": count_cap,
        "coverage": coverage(rows),
        "rankings": {key: ranking(rows, key) for key in keys},
        "formats": groups([{**row, "formats": [row["format_group"]]} for row in rows], "formats"),
        "countries_nonadditive": groups(rows, "countries"),
        "components": [
            {
                key: row[key]
                for key in (
                    "film",
                    *WEIGHTS,
                    "full_weighted",
                    "audience_omitted",
                    "list_critic_only",
                )
            }
            for row in rows
        ],
        "no_weights": rows,
    }


def main() -> None:
    result = evaluate()
    assert result["coverage"] == {
        "films": 10,
        "known_list": 3,
        "known_reception": 10,
        "known_full_weighted": 0,
    }
    assert len(result["rankings"]["named_award"]["groups"][1]["films"]) == 9
    assert result["rankings"]["rt_average_10"]["unknown"] == ["Kung Fu Panda (film)"]
    assert weighted({"x": None}, {"x": 1.0}) is None
    assert weighted({"x": 1.0, "y": 0.0}, {"x": 0.45, "y": 0.30}) == 0.6
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
