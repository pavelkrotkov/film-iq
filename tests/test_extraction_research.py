"""Run the isolated extraction research checks in the project test suite."""

import subprocess
import sys
from pathlib import Path


def test_research_checks() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "docs.research.extraction.test_benchmark",
            "docs.research.extraction.test_loc_baseline",
            "docs.research.extraction.test_corpus",
        ],
        cwd=Path(__file__).resolve().parent.parent,
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "docs.research.extraction.formats.pdf_baseline", "--snapshot"],
        cwd=Path(__file__).resolve().parent.parent,
        check=True,
    )
