"""Generate fictional tracker POC records; identifiers are not TMDB IDs.

Run: python fixture_data.py [count] > fixtures.json
Never send these synthetic identifiers to TMDB.
"""

import json
import sys


def generate(count: int) -> dict:
    if count < 1:
        raise ValueError("count must be positive")
    genres = ("Drama", "Comedy", "Documentary", "Animation", "Science fiction")
    providers = ("Netflix", "Hulu", "Criterion Channel", None)
    states = ("Discovery", "Evaluation", "Watchlist", "Archived")
    films, preferences = [], []
    for index in range(1, count + 1):
        key = f"fixture-{index:04d}"
        provider = providers[index % len(providers)]
        films.append(
            {
                "fixture_id": key,
                "title": f"Fictional Film {index:04d}",
                "release_year": 1950 + index % 75,
                "synopsis": f"Synthetic synopsis for fixture {index}.",
                "critic_score": 40 + index % 56,
                "critic_summary": f"Synthetic critic summary for fixture {index}.",
                "genres": [genres[index % len(genres)]],
                "streaming_providers": [provider] if provider else [],
                "rental_providers": ["Example Rental"] if index % 3 == 0 else [],
                "availability_checked_at": "2026-11-01T12:00:00Z" if index % 3 else None,
                "lifecycle_state": states[index % len(states)],
            }
        )
        for user_index, user in enumerate(("user-a", "user-b")):
            preferences.append(
                {
                    "user_id": user,
                    "fixture_id": key,
                    "interest_score": 1 + (index + user_index * 3) % 10,
                    "watchlist": (index + user_index) % 2 == 0,
                    "watched_at": "2026-10-01T12:00:00Z" if (index + user_index) % 4 == 0 else None,
                    "personal_notes": f"Synthetic note for {user}.",
                }
            )
    return {"synthetic": True, "films": films, "preferences": preferences}


if __name__ == "__main__":
    print(json.dumps(generate(int(sys.argv[1]) if len(sys.argv) > 1 else 30), indent=2))
