"""Opt-in search experiment; no resolver decisions or absent-catalog inference."""

import argparse
import hashlib
import json
from pathlib import Path

from .lookup import lookup

ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=Path, default=Path(__file__).with_name("sample.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--retention-note", default="")
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(ROOT / ".cache"):
        parser.error("output must be within this worktree's .cache directory")
    if args.max_pages < 1 or (args.live and not args.retention_note.strip()):
        parser.error("positive page limit and a live retention basis are required")
    if args.output.exists():
        parser.error("choose a new observation filename; existing evidence is preserved")
    sample_bytes = args.sample.read_bytes()
    sample = json.loads(sample_bytes)
    records = [lookup(film, args.live, args.max_pages) for film in sample]
    report = {
        "sample_sha256": hashlib.sha256(sample_bytes).hexdigest(),
        "retention_note": args.retention_note,
        "observations": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as output:
        json.dump(report, output, indent=2, ensure_ascii=False)
    print(f"{len(records)} cases; {sum(row['requests'] for row in records)} requests")


if __name__ == "__main__":
    main()
