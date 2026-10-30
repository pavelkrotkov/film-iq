"""Run the synthetic lineage check in the project test suite."""

import runpy
from pathlib import Path


def test_lineage_research() -> None:
    path = Path(__file__).resolve().parent.parent / "docs/research/scoring/lineage_demo.py"
    runpy.run_path(str(path), run_name="__main__")


def test_real_scoring_research() -> None:
    path = Path(__file__).resolve().parent.parent / "docs/research/scoring/real_evaluation.py"
    runpy.run_path(str(path), run_name="__main__")
