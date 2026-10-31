"""TMDB candidates reuse partial-safe normalization without inventing tier or price."""

from candidate_support import WORK, permit
from discovery_offer_support import configure, report
from offer_store_support import NOW, fetch

from film_iq.availability.candidate_tmdb import normalize
from film_iq.availability.codec import decode_fetch, encode, key, scope_key
from film_iq.availability.ledger import save_fetch


def payload(us):
    return {"id": 123, "results": {"US": us}}


def test_tmdb_valid_row_is_unconfirmed_and_price_plan_cut_unknown(evidence_db, tmp_path):
    configure(evidence_db, tmp_path)
    permit(evidence_db, "tmdb")
    result = normalize(
        WORK,
        payload(
            {
                "link": "https://example.test/watch",
                "flatrate": [{"provider_id": 7, "provider_name": "Fixture"}],
            }
        ),
        NOW,
    )
    item = result.assertions[0]
    assert result.status == "complete" and result.plan_scope is None
    assert item.opportunity.service == "tmdb:7"
    assert (item.price_minor, item.currency, item.opportunity.plan, item.opportunity.cut) == (
        None,
        None,
        None,
        None,
    )
    assert item.entitlement == "unconfirmed"
    save_fetch(evidence_db, result, NOW)
    assert (
        "[Fixture / tier unknown — subscription]"
        in report(tmp_path, output_format="markdown").split("<details>", 1)[0]
    )

    # New optional provider fields preserve identities of already retained observations.
    assert (
        key(encode(fetch())),
        decode_fetch(encode(fetch())),
        scope_key(fetch()),
        scope_key(fetch(plan=None)),
    ) == (
        "fea9ed9b27a2a10ae70a604d09b76186662c3230c3ea3a90f33f49741ed8ce97",
        fetch(),
        "8e3fb1c59221f971adf4dde8a7731318b19f8e6e09704efea29cff34f360a423",
        "0809f41fd4d6b4b63e213b54b5163a2f3cb547c26c4f4e6a50cdb247d507107b",
    )
