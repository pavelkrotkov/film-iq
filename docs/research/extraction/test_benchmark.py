"""Synthetic completeness and transactional recovery checks."""

import sqlite3
import unittest
from dataclasses import replace

from docs.research.extraction.benchmark import Entry, evaluate
from docs.research.extraction.sqlite_baseline import load_batch


class SyntheticChecks(unittest.TestCase):
    def setUp(self) -> None:
        self.gold = [
            Entry(f"entry-{n}", f"Fictional film {n}", n, None, "ballot", "original")
            for n in range(1, 51)
        ]
        self.gold[1] = replace(self.gold[1], tie="rank-2")
        self.gold[2] = replace(self.gold[2], rank=2, tie="rank-2")

    def test_complete_and_truncated(self) -> None:
        self.assertTrue(evaluate(self.gold, self.gold)["complete"])
        result = evaluate(self.gold, self.gold[:47])
        self.assertFalse(result["complete"])
        self.assertEqual(result["precision"], 1.0)
        self.assertEqual(result["recall"], 47 / 50)

    def test_wrong_semantics_are_not_a_complete_extraction(self) -> None:
        for field, value in (
            ("title", "Wrong title"),
            ("rank", 9),
            ("tie", None),
            ("category", "winner"),
            ("lineage", "derivative"),
        ):
            with self.subTest(field=field):
                actual = self.gold.copy()
                actual[1] = replace(actual[1], **{field: value})
                result = evaluate(self.gold, actual)
                self.assertFalse(result["complete"])
                self.assertEqual(result["recall"], 1.0)
                self.assertEqual(result["fields"][field], 49 / 50)

    def test_unranked_duplicates_and_empty_gold(self) -> None:
        unranked = replace(self.gold[0], rank=None, tie=None)
        self.assertTrue(evaluate([unranked], [unranked])["complete"])
        self.assertFalse(evaluate([unranked], [unranked, unranked])["complete"])
        with self.assertRaises(ValueError):
            evaluate([], [])

    def test_transactional_increment_and_rollback(self) -> None:
        with sqlite3.connect(":memory:") as db:
            db.execute("CREATE TABLE observation (id TEXT PRIMARY KEY, title TEXT NOT NULL)")
            initial: list[tuple[str, str | None]] = [("1", "Film A"), ("2", "Film B")]
            load_batch(db, initial)
            changes = db.total_changes
            load_batch(db, initial)
            self.assertEqual(db.total_changes, changes)
            with self.assertRaises(sqlite3.IntegrityError):
                load_batch(db, [("1", "Changed"), ("3", None)])
            self.assertEqual(
                db.execute("SELECT id, title FROM observation ORDER BY id").fetchall(), initial
            )
            load_batch(db, [("1", "Changed")])
            self.assertEqual(
                db.execute("SELECT title FROM observation WHERE id = '1'").fetchone(), ("Changed",)
            )


if __name__ == "__main__":
    unittest.main()
