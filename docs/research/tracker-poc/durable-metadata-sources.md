# Possible sources for durable film metadata

Research as of November 6, 2026 UTC. This is a source assessment, not a
license certification, identity match or authorization to request personal
film data from another service. The general source research sent no personal
titles or IDs. A separately authorized, limited eight-film Wikidata lookup is
described below. The POCs currently use a temporary TMDB cache; these
alternatives have not been integrated into the trackers.

## Wikidata: structured facts

[Wikidata's structured data](https://www.wikidata.org/wiki/Wikidata:Licensing)
is released under CC0; attribution is encouraged. It can contain titles, release
dates, directors and genre statements with references and qualifiers. Its
[TMDB movie ID property](https://www.wikidata.org/wiki/Property:P4947) offers a
possible crosswalk, but is documented as incomplete and subject to change.
One identifier match is a lead, not proof: retain the Wikidata item and
revision, references, alternatives and uncertainty; do not assume a claim
derived from TMDB is independent corroboration. Missing or conflicting values
must remain unknown or reviewable. This source does not by itself supply a
full film synopsis.

[Documented access](https://www.wikidata.org/wiki/Wikidata:Data_access) includes
the query service for narrowly scoped discovery and entity APIs for known
items. Wikimedia's [current API limits](https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits)
list 10 requests/minute for unidentified clients and 200 for unauthenticated
clients with a compliant User-Agent; limits can change. Use an identifying
User-Agent, low concurrency and Retry-After handling; endpoint-specific limits
also apply. Coverage, correct matching and runtime performance for this film
collection remain unmeasured.

For the eight watched-film IDs separately approved for Wikidata research, two
entity-API requests used the same eight public Wikidata item IDs. No film
titles, TMDB IDs, ratings, watched flags, notes or dates were sent. The second
response included entity revisions and selected full claims with ranks,
qualifiers and references, stored in an owner-only ignored project-local file.
All eight items asserted the prior TMDB crosswalk. Publication dates appeared
for eight, director claims for seven and genre claims for eight; six items had
more than one distinct nondeprecated publication year and three had multiple
director claims. Director and genre values are item IDs, not resolved names.
These are Wikidata assertions, not independently verified film identities or
canonical years. No claims were imported into either tracker or Movary.
The [private review report](../../../.cache/tracker-poc/private/watched-wikidata-review-20261106.md)
is local and ignored by Git; its claim-level links, qualifiers and references
can be inspected without changing a tracker record. A fictional check exercises
the report renderer and its approved-scope validation.

A later bounded public-source review of the same eight films opened seven
stronger source pages. Six pages named the expected title and at least one
director label resolved from the associated Wikidata item; for five films a
source-listed year also appeared among that item's nondeprecated publication
date claims. Two director comparisons remained unresolved because some person
pages could not be read, and one distributor page was inaccessible. Similar
titles and differing dates occurred. These observations support further review;
they do not establish an independent TMDB-to-film match, independent data
lineage, or one canonical release year. The detailed evidence remains in the
ignored private project cache.

## Wikipedia: separately licensed prose

Wikipedia article text is distinct from Wikidata structured data. The
[Wikimedia terms](https://foundation.wikimedia.org/wiki/Terms_of_Use?useformat=mobile)
generally make project text available under CC BY-SA 4.0, with attribution,
license and modification notices and share-alike requirements for relevant
reuse; imported text or media may have additional terms. Keep the source page,
revision and applicable attribution with any copied passage, and assess the
terms for the intended use before adopting it. API extracts are available via
[TextExtracts](https://www.mediawiki.org/wiki/Extension:TextExtracts), but an
article lead is not necessarily a synopsis, a plot can reveal spoilers, and
neither article nor text coverage is assured. A sitelink is an identity lead,
not independent verification of the intended film.

## IMDb: limited personal-use factual datasets

IMDb's [non-commercial datasets](https://www.imdb.com/interfaces/) provide
daily refreshed TSV files with title, original title, release year, up to three
genres, directors and names. They do not include a synopsis in the documented
files. The [IMDb usage conditions](https://help.imdb.com/article/imdb/general-information/can-i-use-imdb-data-in-my-software/G5JTRESSHJBBHTGX)
permit restricted personal, non-commercial use of the published datasets,
require IMDb attribution and reserve withdrawal of permission; they prohibit
website scraping and repurposing the datasets as a movie database except for
individual personal use. Review the actual license and intended distribution
before using or persisting the data. A TMDB-to-IMDb crosswalk is itself unverified and
may have originated from TMDB. The commercial API is a separate
[AWS Data Exchange subscription](https://data.imdb.com/documentation/api-documentation/getting-access/).

## Existing TMDB path and a possible next step

TMDB's [FAQ](https://developer.themoviedb.org/docs/faq) describes free
non-commercial use with required attribution, and its
[provider endpoint](https://developer.themoviedb.org/reference/movie-watch-providers)
requires JustWatch attribution. The project’s dated
[source review](../availability/rights-20261030.md#public-browser-follow-up-tmdb-terms-now-readable)
recorded a six-month cache ceiling and termination purge requirement; the
canonical terms were not accessible to the web reader during this research.
Do not treat a working API key as permission for indefinite copies in issue
history. The current pilot has a stricter seven-day local cache and its own
[scope and deletion rules](tmdb-private-pilot-policy.md).

A possible next experiment is a fictional, offline adapter for attributed
Wikidata facts and a separately attributed Wikipedia excerpt, preserving
conflicts and user edits. Validate licenses, identity, coverage, completeness,
failure handling and privacy before any real import. In particular, sending
watched-film titles or IDs to another service needs the applicable existing
authorization; the TMDB approval does not itself authorize a Wikimedia lookup.
