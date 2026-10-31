"""Legacy keys remain frozen and public/account/source scopes never cross-compare."""

from dataclasses import replace

import pytest
from offer_store_support import fetch

from film_iq.availability.reconcile import changes


def test_public_scope_cannot_compare_a_different_context():
    difference = "legacy_unscoped"
    public = replace(fetch(), plan_scope=None, catalog_scope="public_country")
    other = {
        "legacy_unscoped": replace(public, catalog_scope=None),
        "account_plan": replace(public, catalog_scope=None, plan_scope="Standard"),
        "source": replace(public, source="other", assertions=()),
    }[difference]
    with pytest.raises(ValueError, match="scopes differ"):
        changes(public, other)
