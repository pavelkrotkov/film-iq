"""Run the isolated extraction research checks in the project test suite."""

import subprocess
import sys
from pathlib import Path


def test_research_checks() -> None:
    subprocess.run(
        [sys.executable, "-m", "unittest", "docs.research.extraction.test_benchmark"],
        cwd=Path(__file__).resolve().parent.parent,
        check=True,
    )
