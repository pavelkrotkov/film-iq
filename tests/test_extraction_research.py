"""Run the isolated extraction research checks in the project test suite."""

import subprocess
import sys
from pathlib import Path


def test_research_checks() -> None:
    for args in (
        [
            "-m",
            "unittest",
            "docs.research.extraction.test_benchmark",
            "docs.research.extraction.test_loc_baseline",
            "docs.research.extraction.test_corpus",
        ],
        ["-m", "docs.research.extraction.formats.pdf_baseline", "--snapshot"],
        ["-m", "docs.research.extraction.dynamic.check"],
    ):
        subprocess.run(
            [sys.executable, *args],
            cwd=Path(__file__).resolve().parent.parent,
            check=True,
        )
