"""C3 snapshots retain the declared policy and historical rank semantics."""

import json
import sqlite3
from dataclasses import asdict, replace
from fractions import Fraction

from test_scoring_priority import ballot

from film_iq.scoring import LEGACY_VERSION, VERSION, score
from film_iq.scoring.policy import ScoringPolicy
from film_iq.scoring.snapshot import initialize, replay, save


def test_policy_and_source_exclusion_are_versioned_in_replay():
    entries = [ballot("first", 8, person_id="critic"), ballot("other", 1, person_id="critic")]
    policy = ScoringPolicy(source_priority=("first", "other"), excluded_sources=("absent",))
    with sqlite3.connect(":memory:") as db:
        initialize(db)
        identifier = save(db, entries, "now", policy=policy)
        assert save(db, entries[::-1] * 2, "later", policy=policy) == identifier
        assert replay(db, identifier) == score(entries, policy=policy)
        assert save(db, entries, "now") != identifier
        result = replay(db, identifier)[0]
        assert result.version == VERSION and result.rank_score == Fraction(1, 8)


def test_v1_best_rank_replay_stays_frozen_after_v2():
    entries = [ballot("first", 8), ballot("other", 1)]
    entries = [replace(item, independence_group="critic") for item in entries]
    with sqlite3.connect(":memory:") as db:
        initialize(db)
        db.execute(
            "INSERT INTO scoring_snapshot VALUES (?, ?, ?, ?)",
            ("old", LEGACY_VERSION, "before", json.dumps([asdict(item) for item in entries])),
        )
        old = replay(db, "old")[0]
        current = replay(db, save(db, entries, "now"))[0]
        assert (old.version, old.rank_score) == (LEGACY_VERSION, 1)
        assert (current.version, current.rank_score) == (VERSION, Fraction(1, 8))
        assert (old.excluded, current.excluded) == ((entries[0],), (entries[1],))
