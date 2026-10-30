"""Only explicit complete, reviewed same-plan source scopes support absence."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from film_iq.availability.assertion import Assertion
from film_iq.availability.fetch import Fetch
from film_iq.availability.opportunity import Opportunity
from film_iq.availability.reconcile import changes

NOW = datetime(2026, 10, 30, tzinfo=UTC)


def snapshots():
    offer = Opportunity(1, "service", "subscription", "US", "basic")
    item = Assertion(offer, "a", NOW, "https://example.test", work_status="reviewed")
    old = Fetch("a", 1, "US", NOW, "complete", (item,), "basic", True)
    new = replace(old, checked_at=NOW + timedelta(days=1), assertions=())
    return old, new


def test_complete_scope_absence_and_repeat_are_source_specific():
    old, new = snapshots()
    (event,) = changes(old, new)
    assert (event.kind, event.source) == ("source_absent", "a")
    assert changes(new, new) == ()
    assert changes(new, replace(new, assertions=old.assertions))[0].kind == "source_first_seen"


def test_failures_partial_unknown_plan_or_work_never_remove():
    old, new = snapshots()
    assert changes(old, replace(new, status="unknown")) == ()
    assert changes(old, replace(new, status="partial")) == ()
    assert changes(replace(old, plan_scope=None), replace(new, plan_scope=None)) == ()
    assert changes(old, replace(new, work_reviewed=False)) == ()
    uncertain = replace(old.assertions[0], work_status="cut_uncertain")
    assert changes(replace(old, assertions=(uncertain,)), new) == ()
