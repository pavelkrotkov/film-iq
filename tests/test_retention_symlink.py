"""Named cache deletion preserves unselected symlink targets."""

from test_retention_operations import NOW, policy

from film_iq.cache_purge import purge


def test_selected_cache_symlink_does_not_delete_its_unselected_target(tmp_path):
    target = tmp_path / "unselected.json"
    target.write_text("retain this unselected file")
    selected = tmp_path / "selected.json"
    selected.symlink_to(target)
    expired = policy(allowed=True, expires_at=NOW)
    assert purge(tmp_path, [selected.name], expired, NOW) == (selected.name,)
    purge(tmp_path, [selected.name], expired, NOW, execute=True)
    assert not selected.is_symlink()
    assert target.read_text() == "retain this unselected file"
