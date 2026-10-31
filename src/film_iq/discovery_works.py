"""Coalesce reviewed work cards while retaining flat source facts and unknown entries."""


def coalesce_works(items) -> list[dict]:
    works, selected = {}, []
    for item in items:
        key = item["tmdb_id"] if item["identity_status"] == "reviewed" else None
        if key is None:
            selected.append(item)
            continue
        if key not in works:
            works[key] = {**item, "source_reasons": []}
            selected.append(works[key])
        work = works[key]
        work["source_reasons"].extend(_reasons(item))
    return selected


def _reasons(item):
    return [
        {key: value for key, value in reason.items() if key != "source_reasons"}
        for reason in item.get("source_reasons", [item])
    ]
