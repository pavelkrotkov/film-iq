"""Adding optional provider dates must preserve old retained observation identity."""

from offer_store_support import fetch

from film_iq.availability.codec import decode_fetch, encode, key


def test_old_fetch_hash_and_roundtrip_are_unchanged():
    value = fetch()
    payload = encode(value)
    assert key(payload) == "fea9ed9b27a2a10ae70a604d09b76186662c3230c3ea3a90f33f49741ed8ce97"
    assert "provider_detected_at" not in payload and "provider_last_day_at" not in payload
    assert decode_fetch(payload) == value
