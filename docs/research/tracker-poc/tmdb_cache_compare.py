"""Compare the two local film caches without refreshing provider data."""

import json
import sys
from datetime import UTC, datetime

import tmdb_cache_batch as batch


def metadata(value: dict) -> tuple:
    title = value.get("title")
    if not isinstance(title, str) or not title.strip():
        raise batch.BatchError("response")
    strings = []
    for name in ("original_title", "synopsis", "poster_url", "imdb_title_url"):
        item = value.get(name)
        if item is not None and not isinstance(item, str):
            raise batch.BatchError("response")
        strings.append(item)
    year = value.get("year")
    if year is not None and (type(year) is not int or year <= 0):
        raise batch.BatchError("response")
    lists = []
    for name in ("genres", "directors"):
        item = value.get(name)
        if item is not None and (
            not isinstance(item, list) or any(not isinstance(entry, str) for entry in item)
        ):
            raise batch.BatchError("response")
        lists.append(tuple(sorted(set(item))) if item is not None else None)
    return (title, *strings, year, *lists)


def offers(value: dict) -> frozenset[tuple[str, str]]:
    rows = value["availability"].get("offers")
    if not isinstance(rows, list):
        raise batch.BatchError("response")
    result = set()
    for row in rows:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("provider"), str)
            or not row["provider"].strip()
            or row.get("kind") not in {"subscription", "rent", "buy", "free", "ads"}
        ):
            raise batch.BatchError("response")
        result.add((row["provider"], row["kind"]))
    return frozenset(result)


def compare(kaneo, youtrack, allowed: set[int], report: dict) -> None:
    records = {
        "kaneo": batch.kaneo_records(kaneo, allowed),
        "youtrack": batch.youtrack_records(youtrack, allowed),
    }
    report["validated"] = len(allowed)
    for ident in sorted(allowed):
        left = batch.endpoint(kaneo, "kaneo", records["kaneo"][ident], refresh=False)
        right = batch.endpoint(youtrack, "youtrack", records["youtrack"][ident], refresh=False)
        now = datetime.now(UTC)
        if left is not batch.CACHE_MISS and right is not batch.CACHE_MISS:
            report["both_cached"] += 1
        validated = []
        for name, value in (("kaneo", left), ("youtrack", right)):
            if value is batch.CACHE_MISS:
                report[f"{name}_missing"] += 1
                validated.append(None)
                continue
            try:
                status = batch.validate_result(value, ident, now)
                facts = metadata(value)
                provider_set = offers(value) if status != "unknown" else None
                validated.append((status, facts, provider_set))
            except batch.BatchError:
                report[f"{name}_invalid"] += 1
                validated.append(None)
        left_record, right_record = validated
        if left_record is None or right_record is None:
            continue
        left_status, left_metadata, left_offers = left_record
        right_status, right_metadata, right_offers = right_record
        report["both_valid"] += 1
        if left_metadata != right_metadata:
            report["metadata_mismatches"] += 1
        if left_status != right_status:
            report["availability_status_mismatches"] += 1
        if "unknown" in (left_status, right_status):
            report["provider_sets_unknown"] += 1
            continue
        report["provider_sets_compared"] += 1
        if "partial" in (left_status, right_status):
            report["provider_sets_partial"] += 1
        if left_offers != right_offers:
            report["provider_set_mismatches"] += 1


def main() -> int:
    report = {
        "validated": 0,
        "kaneo_missing": 0,
        "youtrack_missing": 0,
        "kaneo_invalid": 0,
        "youtrack_invalid": 0,
        "both_cached": 0,
        "both_valid": 0,
        "metadata_mismatches": 0,
        "availability_status_mismatches": 0,
        "provider_sets_compared": 0,
        "provider_sets_partial": 0,
        "provider_sets_unknown": 0,
        "provider_set_mismatches": 0,
        "result": "error",
    }
    try:
        allowed = batch.identities()
        compare(batch.LocalHTTP("kaneo"), batch.LocalHTTP("youtrack"), allowed, report)
        report["result"] = "complete"
    except (Exception, KeyboardInterrupt):
        report["result"] = "error"
    print(json.dumps(report, sort_keys=True))
    return 0 if report["result"] == "complete" else 1


if __name__ == "__main__":
    sys.exit(main())
