"""Opt-in US cohort observation CLI, storing only local evidence."""

import argparse
import hashlib
import json
from pathlib import Path

from .observe import PROVIDERS, observe

ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, default=Path(__file__).with_name("cohort.json"))
    parser.add_argument("--provider", choices=PROVIDERS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--retention-note", default="")
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(ROOT / ".cache"):
        parser.error("output must be within this worktree's .cache directory")
    if args.live and not args.retention_note.strip():
        parser.error("record the applicable provider plan and verified retention basis")
    if args.output.exists():
        parser.error("choose a new observation filename; existing evidence is preserved")
    cohort = json.loads(args.cohort.read_text())
    records = [observe(film, args.provider, args.live) for film in cohort]
    report = {
        "retention_note": args.retention_note,
        "cohort_sha256": hashlib.sha256(args.cohort.read_bytes()).hexdigest(),
        "observations": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as output:
        json.dump(report, output, indent=2)
    print(f"{len(records)} candidates; {sum(row['requests'] for row in records)} requests")


if __name__ == "__main__":
    main()
