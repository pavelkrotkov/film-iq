"""Replay explicit source-reviewed repairs without retuning the held-out baseline."""

import hashlib
import json
import unittest
from copy import deepcopy

from docs.research.extraction.corpus_capture import ROOT
from docs.research.extraction.corpus_metrics import measure
from docs.research.extraction.corpus_verify import load_oracles


class CorrectionChecks(unittest.TestCase):
    def test_correction_inputs_preserve_frozen_baseline_and_audits(self):
        protocol = json.loads((ROOT / "correction-protocol.json").read_text())
        for name, expected_hash in protocol["inputs"].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected_hash)

    def test_recorded_post_holdout_edits_repair_only_the_reviewed_failures(self):
        original = json.loads((ROOT / "static-results.json").read_text())["cases"]
        failed = {case["key"]: case for case in original if not case["metrics"]["complete"]}
        corrections = json.loads((ROOT / "correction-results.json").read_text())["cases"]
        self.assertEqual({case["key"] for case in corrections}, set(failed))
        oracles = load_oracles()
        for case in corrections:
            rows = deepcopy(failed[case["key"]]["actual"])
            for edit in case["field_edits"]:
                for position in edit["positions"]:
                    self.assertEqual(rows[position - 1][edit["field"]], edit["before"])
                    rows[position - 1][edit["field"]] = edit["after"]
            rows.extend(case["inserted_rows"])
            self.assertEqual(rows, oracles[case["key"]]["records"])
            self.assertEqual(measure(oracles[case["key"]]["records"], rows), case["after_metrics"])
            self.assertEqual(failed[case["key"]]["metrics"], case["before_metrics"])


if __name__ == "__main__":
    unittest.main()
