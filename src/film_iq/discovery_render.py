"""Minimal private Markdown report; no comments, raw exports, or invented offers."""


def _value(value):
    return "unknown" if value is None else str(value).replace("|", "\\|").replace("\n", " ")


def _row(item: dict) -> str:
    recognition = item["external_critical_recognition"]
    public = recognition["independent_count"] if recognition else None
    fields = (
        item["raw_title"],
        item["tmdb_id"],
        item["identity_status"],
        item["extraction_status"],
        item["rank"],
        item["tie"],
        item["watched"],
        item["personal_enjoyment"],
        item["personal_artistic_merit"],
        item["merit_status"],
        public,
    )
    return "| " + " | ".join(map(_value, fields)) + " |"


def markdown(report: dict) -> str:
    lines = [
        "# Film IQ — private discovery report",
        "",
        f"Last successful personal refresh: {_value(report['last_successful_refresh'])}; stale/unknown: {report['personal_state_stale']}.",
        f"Candidates {report['total_candidates']}; accepted {report['accepted']}; unresolved {report['unresolved']}; watched excluded {report['watched_excluded']}.",
        f"Declared selection scope: {report['completeness']}. Declared lineage: {report['lineage']}",
        "",
        "| Title | TMDB | Identity | Extraction | Rank | Tie | Watched | Enjoyment | Artistic merit | Merit review | Public support |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend(_row(item) for item in report["candidates"])
    lines.extend(
        f"- {_value(item['raw_title'])}: [{_value(item['edition'])}]({item['source_url']}), {_value(item['ballot_scope'])}; locator {_value(item['locator'])}; published {_value(item['published_at'])}; eligibility date {_value(item['eligibility_date'])}; accepted source completeness {_value(item['source_completeness'])}, lineage {_value(item['source_lineage_kind'])}: {_value(item['source_lineage'])}; eligibility {_value(item['source_eligibility'])}. Access: {item['access']}."
        for item in report["candidates"]
    )
    lines.extend(["", "Suggested unwatched:"])
    lines.extend(f"- {_value(item['raw_title'])}" for item in report["suggested_unwatched"])
    lines.extend(["", *report["options"]])
    return "\n".join(lines) + "\n"
