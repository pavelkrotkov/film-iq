# 2023 NBR section fixture

`nbr-2023.wiki` is a purported unmodified excerpt of the “Top 10 Films” section of
[Wikipedia revision 1370562803](https://en.wikipedia.org/w/index.php?title=National_Board_of_Review_Awards_2023&oldid=1370562803),
accessed 2026-10-29. The rest of the page was omitted. Wikipedia contributors
are credited through that revision link; this excerpt is licensed under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), separate from
this repository's MIT-licensed code. See Wikimedia's [reuse terms](https://foundation.wikimedia.org/wiki/Terms_of_Use).
No page images or quoted third-party articles are included.

The [original NBR announcement](https://nationalboardofreview.org/2023/12/national-board-of-review-names-2023-honorees/)
identifies *Killers of the Flower Moon* as Best Film and lists nine Top Films
alphabetically. The Wikipedia section combines the winner and those nine;
this is derivative evidence of NBR, not another independent vote. The nine
positions are display order, not ranks. The fixture represents the complete
published Top 10 section, not a full ballot; NBR's underlying voting and detailed
eligibility are unknown. All ten titles were checked against the current
Wikipedia page and the original announcement. The linked historical revision
could not be retrieved during this audit, so the exact excerpt and revision
association remain unverified and require review before accepting this fixture.

The adapter accepts only this frozen, provisional excerpt and fails on any byte change;
a new document or parser revision requires a fresh audit. It does not fetch,
persist, infer identity, or establish rights to retain the original NBR page.
Deterministic repeated extraction is not a persistence or repeat-fetch test.

# Library of Congress annual selections: normalized transcriptions

The `registry/*.txt` files are manually transcribed title and release-date facts
from these Library of Congress announcements, accessed via a rendered web search
view on 2026-10-29. They are **not raw source pages**: bullets, numbering and
spacing were normalized, and the rest of each announcement is omitted. The
transcriptions have not had a separate independent auditor and do not yet meet
the issue's independently audited page requirement. The SHA-256 values in the
adapter freeze these transcriptions, not the original page revisions.

| Edition | Primary source | Expected selection | Order |
| --- | --- | --- | --- |
| 2020 | [LOC press release](https://www.loc.gov/item/prn-20-082/) | 25, Suspense through Freedom Riders | release chronology |
| 2022 | [LOC announcement](https://blogs.loc.gov/now-see-hear/2022/12/announcing-the-2022-national-film-registry/) | 25, Mardi Gras Carnival through Pariah | release chronology |
| 2025 | [LOC press release](https://newsroom.loc.gov/news/library-names-25-films-to-the-national-film-registry-for-preservation/s/54d2521d-cc42-4987-9c75-4a08d2d901e1) | 25, The Tramp and the Dog through The Grand Budapest Hotel | release chronology |

The lists are facts transcribed from federal announcements; no photographs,
film content, prose, or other potentially third-party material is copied. The
Library [warns that its collections can contain third-party copyrights](https://www.loc.gov/legal/security-copyright-and-privacy/understanding-copyright/);
this does not establish blanket rights to reuse whole pages. The National Film
Registry selection is a primary Library decision, not an independent critical
ballot. Films must be American and at least ten years old and are selected for
cultural, historical or aesthetic significance; nomination and selection details
are not complete ballots. Equal release years are not tied ranks, and ordinal
positions are not ranks. Completeness applies only to the published 25 selections,
not the underlying nominations or the rest of the page. The parser rejects changed
or incomplete transcriptions. It neither fetches nor persists records.

An independent reviewer must compare every line against each source, verify the
exact original capture and retention rights, and add genuine ranked, tied and
partial-ballot examples before the issue's fixture gate can be considered met.
