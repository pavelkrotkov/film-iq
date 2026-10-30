"""Conditional comparisons on observed Wikipedia-derived 2008 critic selections."""

import json
from pathlib import Path

HOLDOUT = {"David Denby", "Anthony Lane"}


def measure(rows: list[dict]) -> tuple[int | None, float | None]:
    if not rows:
        return None, None
    people = {row["critic"]: row["rank"] for row in rows if row["critic"] is not None}
    ranked = [rank for rank in people.values() if rank is not None]
    return len(people), sum(1 / rank for rank in ranked) if ranked else None


def summarize(source: dict) -> dict:
    """Unknown selections remain unknown; count each identified person once."""
    rows = source["records"]
    count, ranks = measure([r for r in rows if r["critic"] not in HOLDOUT])
    held_count, held_ranks = measure([r for r in rows if r["critic"] in HOLDOUT])
    return {
        "film": source["film"],
        "observed_records": len(rows),
        "training_count": count,
        "training_rank_sum": ranks,
        "rank_plus_named_award": ranks + 0.25 * source["named_award_win"]
        if ranks is not None
        else None,
        "heldout_count": held_count,
        "heldout_rank_sum": held_ranks,
        "unidentified_records": sum(r["critic"] is None for r in rows),
    }


def conditional_orders(comparable: list[dict]) -> dict:
    return {
        key: [row["film"] for row in sorted(comparable, key=lambda row: -row[key])]
        for key in (
            "training_count",
            "training_rank_sum",
            "rank_plus_named_award",
            "heldout_rank_sum",
        )
    }


def validate(rows: list[dict]) -> None:
    # Missing observations are not relevance judgments.
    assert len(rows) == 10 and sum(row["observed_records"] for row in rows) == 61
    assert sum(row["training_count"] is None for row in rows) == 7
    assert rows[0]["training_count"] == 31  # Denby's held-out selection is excluded.
    assert (rows[2]["training_count"], rows[2]["training_rank_sum"]) == (4, 0.875)
    assert measure([{"critic": "unranked", "rank": None}]) == (1, None)


def main() -> None:
    data = json.loads(Path(__file__).with_name("real_2008.json").read_text())
    rows = [summarize(source) for source in data["sources"]]
    comparable = [row for row in rows if row["heldout_count"] is not None]
    validate(rows)
    assert len(comparable) == 2
    sample = data["sources"][0]["records"]
    assert measure(sample) == measure(sample * 2)
    print(
        json.dumps(
            {"observations": rows, "conditional_orders": conditional_orders(comparable)}, indent=2
        )
    )


if __name__ == "__main__":
    main()
