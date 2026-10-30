"""Frozen-period descriptive comparison; missing ballots are never negative votes."""

import json
from pathlib import Path

from docs.research.scoring.period_coverage import coverage, groups
from docs.research.scoring.real_evaluation import measure, ranking


def selected(source: dict, main_only: bool) -> list[dict]:
    """Exclude provisional evidence; supplementary categories remain explicit."""
    return [
        row
        for row in source["records"]
        if row["status"] == "verified_automated" and (not main_only or row["category"] == "main")
    ]


def summarize(source: dict, main_only: bool = False) -> dict:
    """Hold out a publication family, including writers absent from the old pilot."""
    records = selected(source, main_only)
    # Family identity survives writer changes between the 2008 and 2024 lists.
    training = [row for row in records if row["family"] != "new_yorker"]
    heldout = [row for row in records if row["family"] == "new_yorker"]
    count, rank_sum = measure(training)
    held_count, held_rank = measure(heldout)
    return {
        "film": source["film"],
        "countries": source["country_labels"],
        "periods": [str(source["source_film_year"])],
        "formats": ["short" if "short" in source["assigned_format"] else source["assigned_format"]],
        "training_count": count,
        "training_rank_sum": rank_sum,
        "heldout_count": held_count,
        "heldout_rank_sum": held_rank,
    }


def evaluate(data: dict, main_only: bool = False) -> dict:
    """Compare only observed overlaps, preserving ties and unknown ordinal scores."""
    rows = [summarize(source, main_only) for source in data["rows"]]
    paired = [
        row
        for row in rows
        if row["training_count"] is not None and row["heldout_count"] is not None
    ]
    return {
        "scope": "main_lists_only" if main_only else "all_typed_yearend_selections",
        "observations": rows,
        "coverage": coverage(rows),
        "formats": groups(rows, "formats"),
        "periods": groups(rows, "periods"),
        "countries_nonadditive": groups(rows, "countries"),
        "conditional_orders": {
            key: ranking(paired, key)
            for key in (
                "training_count",
                "training_rank_sum",
                "heldout_count",
                "heldout_rank_sum",
            )
        },
    }


def main() -> None:
    path = Path(__file__).with_name("holdout-2024")
    data = json.loads((path / "observations.json").read_text())
    print(json.dumps({"inclusive": evaluate(data), "main_only": evaluate(data, True)}, indent=2))


if __name__ == "__main__":
    main()
