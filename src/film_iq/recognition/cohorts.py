"""Bounded release context never substitutes source edition for a film release."""


def release_context(item: dict, display: dict | None) -> dict:
    released = display.get("release_date") if display else None
    return {
        "source_listed_year": item["year"],
        "source_eligibility": item["source_eligibility"],
        "catalog_release_year": int(released[:4]) if released else None,
        "catalog_evidence": display["evidence"] if display else [],
        "catalog_reviewer": display["reviewer"] if display else None,
    }


def release_cohorts(items: list[dict]) -> dict:
    groups, unknown = {}, set()
    for item in items:
        if item["identity_status"] != "reviewed":
            continue
        year = item["release_cohort"]["catalog_release_year"]
        if year is None:
            unknown.add(item["tmdb_id"])
        else:
            groups.setdefault(str(year), set()).add(item["tmdb_id"])
    return {
        "reviewed_catalog_years": {year: sorted(ids) for year, ids in sorted(groups.items())},
        "unknown_catalog_year": sorted(unknown),
        "unresolved_source_entries": sum(item["identity_status"] != "reviewed" for item in items),
        "basis": "Fresh reviewed catalog release dates only; source years/eligibility remain separate",
    }
