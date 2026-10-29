"""Opt-in stdlib HTTP transport for the existing Movary write backend."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class MovaryHTTPTransport:
    """Construct without I/O; send credentials only when explicitly called."""

    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = token

    def __call__(self, method: str, path: str, body: object) -> tuple[int, object]:
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Authorization": f"Bearer {self._token}", "Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        try:
            request = Request(self.base_url + path, data=data, headers=headers, method=method)
            with urlopen(request, timeout=30) as response:
                return _decode(response.status, response.read())
        except HTTPError as error:
            error.close()
            raise ValueError(f"Movary HTTP status {error.code}") from None
        except (URLError, OSError):
            raise ValueError("Movary HTTP transport failed") from None


def _decode(status: int, body: bytes) -> tuple[int, object]:
    if not 200 <= status < 300:
        raise ValueError(f"Movary HTTP status {status}")
    if status == 204:
        return status, None
    try:
        return status, json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("Invalid Movary JSON response") from None
