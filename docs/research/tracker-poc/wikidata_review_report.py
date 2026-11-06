"""Render the approved eight-film Wikidata evidence as a private review report.

Reads project-local input only; never opens links, calls a service, or edits a
tracker. Wikidata claims remain assertions and are not identity decisions.
"""

import json
import os
import re
from pathlib import Path
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[3]
PRIVATE = ROOT / ".cache/tracker-poc/private"
CLAIMS = PRIVATE / "watched-wikidata-entity-revisioned-20261106.json"
PREVIEW = PRIVATE / "watched-research-preview.md"
INPUT = PRIVATE / "film-input.json"
REPORT = PRIVATE / "watched-wikidata-review-20261106.md"


def plain(value: object) -> str:
    """Escape untrusted source text for a Markdown document."""
    text = str(value).replace("\n", " ").replace("\r", " ")
    return re.sub(r"([\\`*_{}\[\]<>()#!|])", r"\\\1", text)


def link(url: str, label: str) -> str:
    try:
        parsed = urlsplit(url)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or any(ord(char) < 32 for char in url)
        ):
            raise ValueError
        return f"[{plain(label)}]({quote(url, safe=':/?#%=&+-._~')})"
    except ValueError:
        return f"{plain(label)} (invalid link)"


def entity_link(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"Q[1-9]\d*", value):
        return "Unknown or invalid Wikidata entity"
    return link("https://www.wikidata.org/wiki/" + value, value)


def snak_value(snak: object) -> str:
    if not isinstance(snak, dict):
        return "Unknown (malformed assertion)"
    snak_type = snak.get("snaktype")
    if snak_type != "value":
        return f"Unknown ({plain(snak_type or 'missing value type')})"
    data = snak.get("datavalue")
    if not isinstance(data, dict) or "value" not in data:
        return "Unknown (missing value)"
    value = data["value"]
    if isinstance(value, dict):
        if data.get("type") == "wikibase-entityid":
            return entity_link(value.get("id"))
        if data.get("type") == "time":
            time = value.get("time")
            precision = value.get("precision")
            calendar = value.get("calendarmodel")
            calendar_id = calendar.rsplit("/", 1)[-1] if isinstance(calendar, str) else None
            return (
                f"{plain(time) if isinstance(time, str) else 'Unknown time'}; "
                f"precision {plain(precision) if type(precision) is int else 'unknown'}; "
                f"calendar {entity_link(calendar_id)}; timezone "
                f"{plain(value.get('timezone')) if type(value.get('timezone')) is int else 'unknown'}; "
                f"before {plain(value.get('before')) if type(value.get('before')) is int else 'unknown'}; "
                f"after {plain(value.get('after')) if type(value.get('after')) is int else 'unknown'}"
            )
        if data.get("type") == "monolingualtext":
            return f"{plain(value.get('text', 'Unknown text'))} ({plain(value.get('language', 'unknown language'))})"
    if isinstance(value, str):
        return link(value, value) if snak.get("datatype") == "url" else plain(value)
    return f"Other value: {plain(json.dumps(value, ensure_ascii=False, sort_keys=True))}"


def snaks(values: object) -> str:
    if not isinstance(values, dict):
        return "Unknown (malformed context)"
    result = []
    for prop, entries in values.items():
        if not isinstance(prop, str) or not re.fullmatch(r"P[1-9]\d*", prop):
            result.append("Unknown property")
            continue
        label = link("https://www.wikidata.org/wiki/Property:" + prop, prop)
        if not isinstance(entries, list) or not entries:
            result.append(f"{label}: unknown")
            continue
        result.extend(f"{label}: {snak_value(entry)}" for entry in entries)
    return "; ".join(result) if result else "None supplied"


def render_claims(claims: object, kind: str) -> tuple[list[str], int]:
    if not isinstance(claims, list):
        return [f"- Unknown ({kind} claims missing or malformed)."], 0
    rows = []
    count = 0
    for claim in claims:
        if not isinstance(claim, dict):
            rows.append("- Unknown (malformed claim).")
            continue
        rank = claim.get("rank")
        if rank == "deprecated":
            continue
        count += 1
        rank_text = rank if rank in ("normal", "preferred") else "unknown rank"
        rows.append(f"- {snak_value(claim.get('mainsnak'))} — rank: {plain(rank_text)}")
        if "qualifiers" in claim:
            rows.append(f"  - Qualifiers: {snaks(claim['qualifiers'])}")
        references = claim.get("references")
        if isinstance(references, list) and references:
            for reference in references:
                values = reference.get("snaks") if isinstance(reference, dict) else None
                rows.append(f"  - Reference: {snaks(values)}")
        elif references not in (None, []):
            rows.append("  - References: unknown (malformed).")
        else:
            rows.append("  - References: none supplied.")
    if not rows:
        rows.append(f"- Unknown (no nondeprecated {kind} claims).")
    return rows, count


def build(preview: str, source: dict, input_data: dict) -> tuple[str, dict[str, int]]:
    ids = []
    for line in preview.splitlines():
        fields = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(fields) == 2 and re.fullmatch(r"[1-9]\d*", fields[1]):
            ids.append(fields[1])
    entities = source.get("entities")
    films = input_data.get("films")
    if (
        len(ids) != 8
        or len(set(ids)) != 8
        or not isinstance(entities, dict)
        or len(entities) != 8
        or not isinstance(films, list)
    ):
        raise ValueError("Expected the approved eight-film source scope")
    by_id = {}
    for film in films:
        if not isinstance(film, dict):
            raise ValueError("Malformed input film")
        ident = str(film.get("tmdb_id"))
        if ident in ids:
            if ident in by_id or not isinstance(film.get("title"), str):
                raise ValueError("Missing or duplicate input identity")
            by_id[ident] = film
    matches = {}
    for qid, record in entities.items():
        if (
            not isinstance(qid, str)
            or not re.fullmatch(r"Q[1-9]\d*", qid)
            or not isinstance(record, dict)
            or type(record.get("lastrevid")) is not int
            or record["lastrevid"] <= 0
            or record.get("crosswalk_tmdb_id") not in ids
            or record["crosswalk_tmdb_id"] in matches
            or not isinstance(record.get("claims"), dict)
        ):
            raise ValueError("Malformed or out-of-scope entity")
        matches[record["crosswalk_tmdb_id"]] = (qid, record)
    if set(by_id) != set(ids) or set(matches) != set(ids):
        raise ValueError("Approved input and entities do not match")
    if source.get("source") != "Wikidata wbgetentities" or source.get("license") != "CC0":
        raise ValueError("Missing expected source provenance")
    lines = [
        "# Private Wikidata evidence for review",
        "",
        "Identity links are unverified leads, not independently confirmed film matches. "
        "Do not treat any publication date as a selected canonical release year. "
        "Item IDs do not establish entitlement, and missing or malformed values remain unknown.",
        "",
        f"Source: {link(str(source.get('endpoint', '')), 'Wikidata entity API')}; "
        f"retrieved {plain(source.get('retrieved_at', 'unknown'))}; "
        f"license {link('https://www.wikidata.org/wiki/Wikidata:Licensing', 'CC0')}. "
        "Date precision follows Wikidata's numeric precision; qualifiers and references "
        "below retain their property IDs. Links open only when selected.",
    ]
    counts = {"films": 0, "date_claims": 0, "director_claims": 0, "genre_claims": 0}
    for ident in ids:
        qid, record = matches[ident]
        rev = record["lastrevid"]
        revision = link(
            f"https://www.wikidata.org/w/index.php?title={qid}&oldid={rev}",
            f"{qid}, revision {rev}",
        )
        lines.extend(
            [
                "",
                f"## {plain(by_id[ident]['title'])}",
                "",
                f"Saved input TMDb ID: {plain(ident)}. Source: {revision}.",
                "",
            ]
        )
        for prop, label, key in (
            ("P577", "Publication date claims", "date_claims"),
            ("P57", "Director item claims", "director_claims"),
            ("P136", "Genre item claims", "genre_claims"),
        ):
            lines.extend([f"### {label}", ""])
            rows, count = render_claims(
                record["claims"].get(prop), label.removesuffix(" claims").lower()
            )
            lines.extend(rows)
            lines.append("")
            counts[key] += count
        counts["films"] += 1
    return "\n".join(lines) + "\n", counts


def main() -> None:
    report, counts = build(
        PREVIEW.read_text(encoding="utf-8"),
        json.loads(CLAIMS.read_text(encoding="utf-8")),
        json.loads(INPUT.read_text(encoding="utf-8")),
    )
    fd = os.open(REPORT, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        output.write(report)
    print("Private project-local review report created; aggregate counts:", counts)


if __name__ == "__main__":
    main()
