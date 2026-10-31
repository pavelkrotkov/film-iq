import pytest

from film_iq.identity import Candidate, Observation, resolve, review


def test_resolution() -> None:
    short = Candidate(1, ("Synthetic Short", "Titre Alternatif"), "A Director", 2020, "tt001")
    remake = Candidate(2, ("Synthetic Short",), "B Director", 2020, "tt002")
    duplicate = Candidate(3, ("Synthetic Short",), "A Director", 2020, "tt003")
    candidates = (short, remake, duplicate)

    raw = Observation("Titre Alternatif", "A Director", 2020)
    decision = resolve(raw, candidates)
    assert decision.match == 1
    assert decision.candidates == (1, 2, 3)
    assert resolve(Observation("Wrong title", tmdb_id=2), candidates).match == 2
    assert resolve(Observation("Wrong title", imdb_id="tt001"), candidates).match == 1
    assert resolve(Observation("Synthetic Short", "A Director", 2020), candidates).match is None
    assert resolve(Observation("Synthetic Short", year=2020), candidates).match is None
    assert (
        resolve(Observation("Synthetic Short", tmdb_id=1, imdb_id="tt002"), candidates).match
        is None
    )


def test_reversible_review() -> None:
    raw = Observation("Titre Alternatif", "A Director", 2020)
    decision = resolve(
        raw,
        (
            Candidate(1, ("Titre Alternatif",), "A Director", 2020),
            Candidate(2, ("Other",), "B Director", 2020),
        ),
    )
    corrected = review((decision,), 2, "reviewer", "The source refers to another film")
    assert corrected[0] == decision
    assert corrected[-1].observation == raw
    assert corrected[-1].candidate_evidence == decision.candidate_evidence
    assert corrected[-1].match == 2
    assert review(corrected, 1, "reviewer", "Reinstated after checking")[-1].match == 1
    with pytest.raises(ValueError):
        review(corrected, 999, "reviewer", "Not a recorded candidate")
    with pytest.raises(ValueError):
        review(corrected, None, "", "Missing reviewer")
