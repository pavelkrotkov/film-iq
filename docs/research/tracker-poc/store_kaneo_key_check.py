"""Fictional checks for the local Kaneo key provisioning helper."""

import contextlib
import io
import json
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import store_kaneo_key as helper

KEY = "fictional-key-do-not-disclose"


class KeyProvisionCheck(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=helper.PRIVATE)
        self.addCleanup(self.temp.cleanup)
        self.private = Path(self.temp.name)
        self.destination = self.private / "kaneo-api-key"
        for name, value in {
            "kaneo-private-ids.json": {"project": "fictional-project"},
            "movary-watched.json": {
                "version": "tracker-poc-movary-watched-v1",
                "project_id": "fictional-project",
                "users": {"fictional-owner": {}},
            },
        }.items():
            path = self.private / name
            path.write_text(json.dumps(value))
            path.chmod(0o600)
        self.paths = []

    def api(self, _opener, _base, path):
        self.paths.append(path)
        return {
            "/user/me": {"id": "fictional-owner"},
            "/custom-field/project/fictional-project": [{"name": "POC TMDB ID", "type": "text"}],
            "/custom-field/project/fictional-project/values": [],
            "/task/tasks/fictional-project?limit=100&page=1": {"data": {}},
        }[path]

    def run_main(self, api=None):
        out = io.StringIO()
        with (
            patch.object(helper, "PRIVATE", self.private),
            patch.object(helper, "DESTINATION", self.destination),
            patch.object(helper.getpass, "getpass", return_value=KEY),
            patch.object(helper, "call", side_effect=api or self.api),
            contextlib.redirect_stdout(out),
        ):
            helper.main()
        self.assertNotIn(KEY, out.getvalue())

    def test_success_and_exclusive_storage(self):
        self.run_main()
        self.assertEqual(self.destination.read_text(), KEY)
        self.assertEqual(stat.S_IMODE(self.destination.stat().st_mode), 0o600)
        self.assertEqual(
            self.paths,
            [
                "/user/me",
                "/custom-field/project/fictional-project",
                "/custom-field/project/fictional-project/values",
                "/task/tasks/fictional-project?limit=100&page=1",
            ],
        )
        with self.assertRaises(SystemExit):
            self.run_main()
        self.assertEqual(self.destination.read_text(), KEY)
        with self.assertRaises(FileExistsError):
            helper.save("other-key", self.destination)

    def test_wrong_owner_or_failed_request_does_not_save_or_disclose(self):
        for failure in ({"id": "another-owner"}, RuntimeError(KEY)):

            def api(_opener, _base, _path, failure=failure):
                if isinstance(failure, Exception):
                    raise failure
                return failure

            with self.assertRaises(SystemExit) as error:
                self.run_main(api)
            self.assertNotIn(KEY, str(error.exception))
            self.assertFalse(self.destination.exists())

    def test_project_and_owner_context_and_permissions(self):
        self.assertEqual(helper.context(self.private), ("fictional-project", "fictional-owner"))
        sidecar = self.private / "movary-watched.json"
        sidecar.chmod(0o644)
        with self.assertRaises(ValueError):
            helper.context(self.private)
        sidecar.chmod(0o600)
        sidecar.write_text(
            json.dumps(
                {
                    "version": "tracker-poc-movary-watched-v1",
                    "project_id": "other",
                    "users": {"fictional-owner": {}},
                }
            )
        )
        with self.assertRaises(ValueError):
            helper.context(self.private)

    def test_project_read_failure_does_not_save(self):
        def api(_opener, _base, path):
            if path == "/user/me":
                return {"id": "fictional-owner"}
            raise PermissionError(KEY)

        with self.assertRaises(SystemExit) as error:
            self.run_main(api)
        self.assertNotIn(KEY, str(error.exception))
        self.assertFalse(self.destination.exists())


if __name__ == "__main__":
    unittest.main()
