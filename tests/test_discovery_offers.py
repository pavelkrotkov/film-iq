"""Imported source variants reach the actual reopened report without a viewing plan."""

from dataclasses import replace

from discovery_offer_support import configure, import_observation, observation, report
from offer_store_support import prepare


def test_import_reopen_discovery_preserves_all_price_quality_addon_cut_variants(
    evidence_db, tmp_path
):
    configure(evidence_db, tmp_path)
    prepare(evidence_db)
    source = observation()
    first = replace(
        source.assertions[0],
        price_minor=499,
        currency="USD",
        opportunity=replace(
            source.assertions[0].opportunity, kind="rent", quality="hd", cut="original"
        ),
    )
    second = replace(first, price_minor=299, opportunity=replace(first.opportunity, quality="sd"))
    addon = replace(
        first,
        price_minor=None,
        opportunity=replace(first.opportunity, kind="add-on", add_on="Fixture add-on"),
    )
    assert import_observation(tmp_path, replace(source, assertions=(first, second, addon))) == 0
    result = report(tmp_path)
    claims = result["suggested_unwatched"][0]["offer_states"][0]["latest_attempt"]["assertions"]
    assert [claim["price_minor"] for claim in claims] == [499, 299, None]
    assert [claim["opportunity"]["quality"] for claim in claims] == ["hd", "sd", "hd"]
    assert claims[2]["opportunity"]["add_on"] == "Fixture add-on"
    assert claims[0]["opportunity"]["cut"] == "original"
    output = report(tmp_path, output_format="markdown")
    assert "[Fixture cinema / Standard — rent](https://example.test/film)" in output
    assert "Reported options; verify with the service" in output
