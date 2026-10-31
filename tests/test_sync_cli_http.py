"""HTTP behavior with mocked urlopen only; no live calls or real credentials."""

from unittest.mock import MagicMock


def response(status, body):
    result = MagicMock()
    result.__enter__.return_value = result
    result.status = status
    result.read.return_value = body
    return result
