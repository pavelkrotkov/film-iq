"""Protect measured semantic failures and changed-source unknown outcomes."""

import tempfile
import unittest
from pathlib import Path

from docs.research.extraction.corpus_run import run
from docs.research.extraction.corpus_verify import checked
from docs.research.extraction.llm_check import run as check_llm


class CorpusChecks(unittest.TestCase):
    def test_independent_oracles_preserve_known_complete_document_failures(self):
        cases = run()["cases"]
        self.assertEqual(len(cases), 32)
        self.assertEqual(sum(c["metrics"]["complete"] for c in cases), 26)
        poll = next(c for c in cases if c["key"] == "poll-0")["metrics"]
        self.assertEqual((poll["expected"], poll["extracted"], poll["complete"]), (11, 10, False))
        academy = next(c for c in cases if c["key"] == "shorts-0")["metrics"]
        self.assertEqual(academy["entry_recall"], 1)
        self.assertEqual(academy["fields"]["category"], 0)
        self.assertFalse(academy["complete"])

    def test_valid_llm_spans_do_not_establish_scoped_completeness(self):
        result = check_llm()
        self.assertEqual((result["valid_spans"], result["total_spans"]), (12, 12))
        self.assertEqual(result["metrics"]["entry_recall"], 1)
        self.assertLess(result["metrics"]["entry_precision"], 1)
        self.assertFalse(result["metrics"]["complete"])

    def test_changed_capture_is_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changed.json"
            path.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "status unknown"):
                checked(path, {"bytes": 7, "sha256": "not-the-recorded-hash"})


if __name__ == "__main__":
    unittest.main()
