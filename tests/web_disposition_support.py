"""The local shortlist steps in the existing browser integration journey."""

import json
from contextlib import closing
from urllib.parse import urlencode

from discovery_fixtures import fresh_status
from web_support import request

from film_iq.dispositions import read
from film_iq.recovery import backup, restore, validate
from film_iq.storage import connect, migrate
from film_iq.web import Application


def submit(app, state, *, token=None, headers=None, tmdb_id=123):
    body = urlencode({"state": state, "csrf_token": token or app.csrf_token})
    return request(app, f"/films/{tmdb_id}/disposition", "POST", body, headers)


def inspect_migration(app, db, root):
    # Start with real accepted schema11 records and a validated online backup.
    db.executescript("DROP TABLE recommendation_disposition; PRAGMA user_version=11;")
    before = app.report()
    backup(db, root / "before-shortlist.db")
    migrate(db)
    assert db.execute("PRAGMA user_version").fetchone() == (12,)
    assert app.report() == before
    # Restoring the pre-upgrade copy must still permit the same upgrade.
    restore(root / "before-shortlist.db", root / "restored-shortlist.db")
    with closing(connect(root / "restored-shortlist.db")) as recovered:
        migrate(recovered)
        validate(recovered)
        assert (
            recovered.execute("SELECT count(*) FROM entry_observation").fetchone()
            == db.execute("SELECT count(*) FROM entry_observation").fetchone()
        )
    assert read(root / "restored-shortlist.db") == {}


def inspect_boundaries(app):
    # Isolate the three actual write gates with otherwise valid native forms.
    assert submit(app, "saved", token="expired")["status"] == "403 Forbidden"
    assert (
        submit(app, "saved", headers={"HTTP_ORIGIN": "https://unrelated.test"})["status"]
        == "403 Forbidden"
    )
    assert (
        submit(app, "saved", headers={"HTTP_HOST": "unrelated.test"})["status"] == "403 Forbidden"
    )
    assert submit(app, "unsupported")["status"] == "400 Bad Request"
    assert submit(app, "saved", tmdb_id=999)["status"] == "404 Not Found"
    assert read(app.database) == {}


def inspect_saved(app):
    page = request(app)["body"]
    assert 'action="/films/123/disposition"' in page
    result = submit(app, "saved")
    assert result["status"] == "303 See Other"
    assert result["headers"]["Location"] == "/films/123"
    assert "0 films to explore" in request(app)["body"]
    assert "1 film to explore" in request(app, "/saved")["body"]
    assert "FilmIQ shortlist · Saved" in request(app, "/films/123")["body"]
    submit(app, "saved")


def inspect_reopened(app):
    # Restart rotates form tokens while retaining only the intended local state.
    reopened = Application(
        app.database,
        app.cohort,
        app.snapshot,
        app.catalog,
        public_origin="https://film.example.test:8450",
    )
    assert read(reopened.database) == {123: "saved"}
    assert submit(reopened, "dismissed", token=app.csrf_token)["status"] == "403 Forbidden"
    assert reopened.snapshot is not None
    # Saved choices stay visible when a later refresh marks the film watched.
    reopened.snapshot.with_suffix(".json.status").write_text(json.dumps(fresh_status()))
    assert "1 film to explore" in request(reopened, "/saved")["body"]
    assert 'name="watched"' in request(reopened, "/saved")["body"]
    submit(reopened, "dismissed")
    assert "0 films to explore" in request(reopened, "/saved")["body"]
    assert "1 film to explore" in request(reopened, "/dismissed")["body"]
    return reopened


def inspect_dispositions(app, db, root):
    inspect_migration(app, db, root)
    before = app.report()["candidates"]
    personal = app.snapshot.read_bytes()
    inspect_boundaries(app)
    inspect_saved(app)
    reopened = inspect_reopened(app)
    submit(reopened, "discover")
    assert read(app.database) == {}
    assert "1 film to explore" in request(reopened, "/?watched=all")["body"]
    assert "0 films to explore" in request(reopened, "/dismissed")["body"]
    # Local dispositions do not rewrite source or personal-state exports.
    assert app.report()["candidates"] == before
    assert app.snapshot.read_bytes() == personal
