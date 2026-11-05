"""Preview/confirmation and truthful refresh state around supported Movary actions."""

import hashlib
import hmac
import os
import secrets
from datetime import date
from pathlib import Path

from film_iq.web_movary_forms import confirmation, notice, panel
from film_iq.web_movary_refresh import execute_result, refresh_result


class MovaryControls:
    def __init__(self, snapshot: Path | None, ratings_command=None, history_command=None):
        self.snapshot = snapshot
        self.exports = {"ratings_command": ratings_command, "history_command": history_command}
        self.settings = tuple(
            os.environ.get(name, "") for name in ("MOVARY_URL", "MOVARY_USERNAME", "MOVARY_TOKEN")
        )
        # The preview key stays server-side; the rendered CSRF token cannot sign it.
        self._key = secrets.token_bytes(32)

    def enabled(self) -> bool:
        return bool(self.snapshot and all(self.settings) and all(self.exports.values()))

    def panel(self, item: dict, csrf: str) -> str:
        return panel(item, self.snapshot, self.settings, self.enabled(), csrf)

    def signature(self, item: dict, action: str, day: str) -> str:
        value = f"{item['tmdb_id']}:{action}:{day}".encode()
        return hmac.new(self._key, value, hashlib.sha256).hexdigest()

    def submit(self, item: dict, route: str, values: dict, csrf: str):
        try:
            return self.action(item, route, values, csrf)
        except PermissionError:
            return "403 Forbidden", "Movary confirmation does not match its preview.", "text/plain"
        except ValueError:
            return "400 Bad Request", "Invalid Movary action or watch date.", "text/plain"

    def action(self, item: dict, route: str, values: dict, csrf: str):
        if not self.enabled():
            return (
                "503 Service Unavailable",
                notice(item, "Movary controls are not configured."),
                "text/html",
            )
        if route == "refresh":
            return refresh_result(item, self.settings, self.snapshot, self.exports)
        action, phase = route.split("/")
        if action not in {"watchlist", "watched"} or phase not in {"preview", "confirm"}:
            raise ValueError("Unknown Movary action")
        day = date.fromisoformat(values.get("date", "")).isoformat() if action == "watched" else ""
        signature = self.signature(item, action, day)
        if phase == "preview":
            return "200 OK", confirmation(item, action, day, signature, csrf), "text/html"
        if not hmac.compare_digest(signature.encode(), values.get("signature", "").encode()):
            raise PermissionError("Movary confirmation does not match its preview")
        return execute_result(item, action, day, self.settings, self.snapshot, self.exports)
