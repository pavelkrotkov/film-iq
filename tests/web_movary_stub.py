"""Credential-free installed Movary API behavior for the single browser journey."""

import csv

from film_iq.personal_refresh import refresh


class MovaryStub:
    def __init__(self, root):
        self.root, self.calls = root, []
        self.movie = {"ids": {"tmdb": 123, "movary": 456}, "title": "Synthetic Film"}
        self.dates: list[dict] = [
            {"date": "2026-01-01", "plays": 2, "comment": "PRIVATE KEEP COMMENT"}
        ]
        self.watchlisted, self.uncertain = False, False
        self.rating = 7

    def read(self, collection):
        return {
            "played": [{"movie": self.movie, "watchDates": self.dates}],
            "history": [{"movie": self.movie}],
            "watchlist": [{"movie": self.movie}] if self.watchlisted else [],
        }[collection]

    def __call__(self, method, path, body):
        self.calls.append((method, path, body))
        if method == "GET":
            return self.get(path)
        if method == "PUT":
            watch = body[0]["watchDates"][0]
            assert "comment" not in watch
            self.dates.append(
                {"date": watch["watchedAt"], "plays": watch["plays"], "comment": None}
            )
            self.watchlisted = False  # Installed optional automatic-removal behavior.
        else:
            assert path.endswith("watchlist/movies")
            self.watchlisted = True
        if self.uncertain:
            raise ValueError("PRIVATE API RESPONSE")
        return 204, None

    def get(self, path):
        if "/movies/search?" in path:
            return 200, {"results": [self.movie], "currentPage": 1, "maxPage": 1}
        return 200, {"watchlist": self.read("watchlist"), "currentPage": 1, "maxPage": 1}

    def refresh(self, client, snapshot, **exports):
        assert all(exports.values())
        ratings, history = self.root / "ratings.csv", self.root / "history.csv"
        ratings.write_text(
            f"title,year,tmdbId,imdbId,userRating\nSynthetic Film,2025,123,,{self.rating}\n"
        )
        with history.open("w", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(
                ["title", "year", "tmdbId", "imdbId", "watchedAt", "comment", "location"]
            )
            writer.writerows(
                ["Synthetic Film", "2025", "123", "", row["date"], row["comment"] or "", ""]
                for row in self.dates
            )
        return refresh(client, snapshot, ratings_csv=ratings, history_csv=history)
