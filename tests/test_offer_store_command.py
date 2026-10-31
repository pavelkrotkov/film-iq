"""The local command requires an explicit source policy before retaining offers."""

import json
from dataclasses import replace

import pytest
from offer_store_support import NOW, fetch, policy

from film_iq.availability.codec import encode, timestamp
from film_iq.availability.store_command import main


def test_command_policy_import_state_and_termination(tmp_path, capsys):
    database, inputs = tmp_path / "offers.db", tmp_path / "input.json"
    options = ["--database", str(database), "--input", str(inputs), "--now", timestamp(NOW)]
    inputs.write_text(encode(fetch()))
    with pytest.raises(SystemExit):
        main(["import", *options])
    inputs.write_text(encode(policy(allowed=True)))
    main(["policy", *options])
    capsys.readouterr()
    inputs.write_text(encode(fetch()))
    assert main(["import", *options]) == 0
    capsys.readouterr()
    assert main(["state", *options]) == 0
    state = json.loads(capsys.readouterr().out)
    assert state["current"]["plan_scope"] == "Standard"
    assert state["first_seen_by_us"][0]["first_seen_by_us"] == timestamp(NOW)
    assert state["current"]["assertions"][0]["asserted_added_on"] is None
    inputs.write_text(encode(replace(policy(allowed=True), terminated=True)))
    main(["policy", *options])
    capsys.readouterr()
    assert main(["purge", *options, "--source", "fixture", "--execute"]) == 0
    assert len(json.loads(capsys.readouterr().out)["purge"]) == 1
