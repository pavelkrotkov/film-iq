# Annual film sources and critic coverage

Checked on November 20, 2026 for the private Kaneo suggestion-library expansion.
This report records acquisition evidence. Canonical work matching, independent
acceptance, import totals and live deployment are owned by the library importer.

The private factual bundles contain 1,100 published selections across 32 complete
declared source editions or participant lists. They contain 795 distinct
case-insensitive title labels before alias reconciliation and film identification.
A distinct source label is not a distinct verified film.

## Acquired source coverage

| Publisher or ballot | Complete declared coverage | Entries | Semantics and remaining limits |
| --- | --- | --- | --- |
| The Film Stage annual staff poll | Every annual top 50 from 2013 through 2025 | 650 | Explicit ranked aggregate. The contributing staff ballots remain the underlying evidence. Aggregate and individual votes must share lineage. |
| The Film Stage midyear list | Published 2026 midyear selection | 25 | Alphabetical and unranked. Supplies actual published 2026 evidence, with no assumed year-end poll. |
| BFI / Sight and Sound annual poll | 2010, 2011, 2012, and 2021 through 2025 | 284 | Complete published ranked sections, preserving ties. BFI 2013 through 2020 remain unimported in this pass. |
| Film Comment contributors poll | 2019, 2022, 2023, 2024, 2025 | 101 | US-release eligibility belongs to the poll edition. The 2022 nominal top 20 contains 21 films, with two at rank 20. Other historical editions remain unimported. |
| Senses of Cinema World Poll | Five complete first-selection lists in the 2025 Part 1 publication | 40 | Original named participant lists. The remainder of the poll is unimported. Bullets remain unranked. |

The annual time range has at least one source edition for every year from 2010
through 2025, plus the published 2026 midyear list. This does not establish every
publisher's complete historical coverage. Original current examples are the
[Film Stage 2025 poll](https://thefilmstage.com/the-film-stages-top-50-films-of-2025/),
[BFI 2025 poll](https://www.bfi.org.uk/sight-and-sound/polls/50-best-films-2025),
[Film Comment 2025 poll](https://www.filmcomment.com/best-films-of-2025/) and
[Film Stage 2026 midyear list](https://thefilmstage.com/the-best-films-of-2026-so-far/).

## Private import bundles

The seven bundles are inside this worktree's ignored .cache/source-library/annual/
directory. Diagnostic probe files are outside the accepted source set.

| Bundle filename | Complete declared source editions | Entries |
| --- | --- | --- |
| annual-first-editions.json | Three 2025 publisher editions | 120 |
| film-stage-2013-2024.json | Ten historical 50-film editions | 500 |
| film-stage-recovered-2019-2022.json | Two recovered 50-film editions | 100 |
| bfi-filmcomment-2019-2024.json | Eight BFI or Film Comment editions | 281 |
| bfi-2010-2012.json | Three complete original ranked sections | 34 |
| senses-selected-ballots-2025.json | Five complete declared participant lists | 40 |
| film-stage-2026-midyear.json | One unranked midyear list | 25 |

The bundles retain publisher URL, edition, eligibility, lineage, author when
published, exact source title, position, actual rank or null, tie, director or
null, source-supplied film year or null, and a source locator. No inferred TMDB or
IMDb identifiers are supplied. Source article prose, images, personal ratings
and streaming catalogs are excluded from these factual records.

## Named participants and critic context

| Participant | Publisher-supplied context | First published list imported | What the context supports |
| --- | --- | --- | --- |
| Antti Alanen | Film historian, teacher, critic, blogger, advisor | Ten unranked films | His list includes 2024 and 2025 works. Poll year is a viewing-year assertion. |
| Hussain Al-Dubaisi | Cinephile in Qatif, Saudi Arabia | Five ranked 2025 films | Keep the stated participant role. His older-discovery category is outside this imported scope. |
| Algitya | Cinema projectionist in Indonesia | Five unranked new-film selections | Adds a named Indonesian participant. Film production geography requires title-level evidence. |
| Geoff Andrew | Critic, programmer and lecturer | Ten unranked films | Use the named ballot as evidence. Comments do not create additional votes. |
| Arta Barzanji | London-based Iranian critic, curator and filmmaker | Ten unranked films | Retain the stated background. His Godard selection needs explicit work-identification review. |

These descriptions come from the original [Senses of Cinema World Poll 2025
Part 1](https://www.sensesofcinema.com/2026/world-poll/world-poll-2025-part-1/).
Participant geography and role are separate from film-country metadata and do
not establish predictors of the user's enjoyment.

The next named-critic expansion should preserve one person's identity across
publishers. RogerEbert.com's roster includes Sheila O'Malley, Christy Lemire,
Odie Henderson, Ben Kenigsberg, Alisha Mughal and Carla Renata. Several write for
multiple publications. Link their ballots to those people before counting
independent breadth. [RogerEbert.com contributors](https://www.rogerebert.com/contributors)

For Spanish-language and Latin American coverage, La Internacional Cinéfila 2025
publishes 207 critics, filmmakers and programmers. Its numbered category
separators introduce recent-film, debut, local-film, discovery and other
responses. A separator labelled “1” is not a rank shared by every film that
follows. The original 2025 page is publicly reachable, but none of its ballots
were accepted into this pass. [La Internacional Cinéfila 2025](https://www.conlosojosabiertos.com/la-internacional-cinefila-2025/)

## Extraction findings requiring ongoing handling

- BFI's current HTML repeats its ranked list in three responsive renderings. Deduplicate exact rank/title replicas after confirming copies agree and the declared count is satisfied.
- BFI 2010 has a top 12. The 2011 nominal top 10 has 11 films. The 2012 ranked section has 11 films. Leading and trailing equals signs denote ties.
- Film Comment 2022 has two entries at rank 20. Keeping only 20 rows silently drops a published selection.
- Film Stage 2019 rank 35 supplies a title without a director in its ranked heading. Source director stays unknown.
- Film Stage 2022 uses a singular “stage” in its canonical URL path.
- Film Stage 2024 groups Youth (Hard Times and Homecoming) in one selection. Preserve the grouped observation and review the two-work identity explicitly.
- An italicized translated title can contain a comma, as in I, The Song. Split title and director using the markup and explicit validation.
- Participant Alanen's Highway 99 A Double Album credit is preserved as published. Its canonical identity requires review.
- The 2026 midyear list is alphabetical and unranked. Its position must not become a numerical endorsement strength.
- A failed fetch is an acquisition gap. An unresolved work remains visible in the source ledger.

## Access and remaining source work

| Source | Access observed in this pass | Next useful acquisition |
| --- | --- | --- |
| RogerEbert.com | Original annual and midyear pages are available in web search. Ordinary direct requests returned HTTP 403 for the checked 2025 article. | Read full original ballots through supported access and validate complete declared lists. |
| Slant | Original 2025 top 25, runners-up and individual-ballot sections are readable through the web source reader. | Import aggregate, named ballots and honorable mentions with distinct scopes. |
| Cahiers du cinéma | A complete original 2025 editorial ballot publication was not established. | Verify original public publication or authorized issue access, preserving French release eligibility. |
| La Internacional Cinéfila | Original 2025 page and annual index are reachable. | Audit category boundaries and contributor count before a complete poll import. |
| Senses of Cinema | Original 2025 Part 1 is reachable. Its index shows multiple parts. | Inventory all parts and participant lists, then backfill earlier polls. |
| BFI | Current and three checked older original pages are reachable through ordinary requests. Older URLs vary. | Fill 2013–2020 from original pages with layout-specific checks. |
| Film Comment | Imported editions are reachable. Other historical pages have different layouts, missing URLs or registration notices. | Check remaining editions individually and retain access failures as gaps. |

Senses of Cinema's About policy permits private study, research, criticism or
review, with written permission needed for other reproduction. Its factual
ballot records are retained for this user's private research. Broader
source-text copying and public corpus redistribution have separate rights
questions. Other bundles record private factual observations and make no
invented publisher license or redistribution grant.
[About Senses of Cinema](https://www.sensesofcinema.com/about/)

Scores and festival awards are separate evidence streams. RT critics,
Popcornmeter, Metascore, Metacritic user score, IMDb and a festival prize are
separate from named-critic ballots. Retain each metric's scale, date and sample
size, and connect derivative publisher aggregates to their underlying ballots.
