"""Legacy keys remain frozen and public/account/source scopes never cross-compare."""

from dataclasses import replace

import pytest
from offer_store_support import fetch

from film_iq.availability.codec import scope_key
from film_iq.availability.reconcile import changes


def test_legacy_comparison_keys_are_unchanged():
    legacy = fetch()
    assert scope_key(legacy) == "8e3fb1c59221f971adf4dde8a7731318b19f8e6e09704efea29cff34f360a423"
    unscoped = replace(legacy, plan_scope=None)
    assert scope_key(unscoped) == "0809f41fd4d6b4b63e213b54b5163a2f3cb547c26c4f4e6a50cdb247d507107b"
    assert scope_key(replace(unscoped, catalog_scope="public_country")) != scope_key(unscoped)


@pytest.mark.parametrize("difference", ["legacy_unscoped", "account_plan", "source"])
def test_public_scope_cannot_compare_a_different_context(difference):
    public = replace(fetch(), plan_scope=None, catalog_scope="public_country")
    other = {
        "legacy_unscoped": replace(public, catalog_scope=None),
        "account_plan": replace(public, catalog_scope=None, plan_scope="Standard"),
        "source": replace(public, source="other", assertions=()),
    }[difference]
    with pytest.raises(ValueError, match="scopes differ"):
        changes(public, other)


def test_ambiguous_public_and_account_scope_is_rejected():
    with pytest.raises(ValueError, match="one explicit"):
        replace(fetch(), catalog_scope="public_country")
