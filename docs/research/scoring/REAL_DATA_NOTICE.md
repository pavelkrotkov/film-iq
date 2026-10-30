# Real 2008 sample: attribution and limits

`real_2008.json` contains factual selection transcriptions and short wikitext
excerpts by **Wikipedia contributors**, distributed under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
The JSON records the exact requested API URLs, revision IDs, response hashes,
acquisition window and line locators. Attribution and contributor histories:

- [Milk](https://en.wikipedia.org/w/index.php?oldid=1379683314) / [history](https://en.wikipedia.org/w/index.php?title=Milk_(2008_American_film)&action=history)
- [The Wrestler](https://en.wikipedia.org/w/index.php?oldid=1381358616) / [history](https://en.wikipedia.org/w/index.php?title=The_Wrestler_(2008_film)&action=history)
- [The Reader](https://en.wikipedia.org/w/index.php?oldid=1378967681) / [history](https://en.wikipedia.org/w/index.php?title=The_Reader_(2008_film)&action=history)

Only these three pages contribute copied selection text; the other seven
entries record requests and unknown outcomes. Preserve attribution and the
share-alike license for these excerpts and adaptations. Code remains MIT.
No images, publisher reviews or original publication bodies are retained.
This license applies to the Wikipedia material, not its external references.

Changes: full API responses were inspected in memory and hashed; only factual
critic-selection lines and one factual selection paragraph were retained.
Wiki links/formatting were removed for structured names; ordinal ranks became
integers. Audit added the selector's omitted unranked Milk/Ebert membership;
the dataset retains this correction. The Reader's four observations were transcribed from its paragraph,
including Roger Ebert's unranked top-20 membership. Other pages used an ordinal
bullet selector. Source list completeness and external primary accuracy were
not established; omission stays unknown. The raw response hash is provenance,
not a claim that this JSON retains the full response for hash reproduction.

Milk and The Reader cite Metacritic's archived 2008 list compilation;
The Wrestler includes Metacritic-derived and individually referenced rows.
Its section includes a citation labeled 2007 despite its 2008 heading; edition
lineage is unresolved, and not every row has an individual citation.
Wikipedia and the intermediary are derivative carriers, never extra critics.
Names are source-attributed identities, without independent identity audit.
One publication-only Premiere row has unknown critic identity and is excluded
from identified-person counts. Each named person is counted once per film.

## Reception and context supplement

`reception_2008.json` adapts factual reception, country and runtime text from
the **same ten** Wikipedia revisions under the same CC BY-SA 4.0 terms. In
addition to the three articles above, attribution is to Wikipedia contributors
of these pinned articles and their accessible Page history tabs:

- [The Curious Case of Benjamin Button](https://en.wikipedia.org/w/index.php?oldid=1379730511)
- [Frost/Nixon](https://en.wikipedia.org/w/index.php?oldid=1380568022)
- [Slumdog Millionaire](https://en.wikipedia.org/w/index.php?oldid=1379601586)
- [The Visitor](https://en.wikipedia.org/w/index.php?oldid=1370281508)
- [Bolt](https://en.wikipedia.org/w/index.php?oldid=1380813477)
- [Kung Fu Panda](https://en.wikipedia.org/w/index.php?oldid=1381957478)
- [WALL-E](https://en.wikipedia.org/w/index.php?oldid=1380240647)

Changes: numerical and categorical facts were manually transcribed; factual
wikitext spans and line locators were retained, excluding critic-consensus
quotations. Short template prefixes preserve literal numerical parameters;
unexpanded dynamic values remain unknown. Citation access dates are separately
transcribed metadata, not dates when those scores were measured. The full
source response hashes and actual acquisition timestamps are receipts, not
live original-provider verification. No provider bodies, critic reviews or
media are redistributed. Original API responses retained only in the local
ignored audit cache are separately identified in the audit report.

Country is the article's reported production-country field, not story
location, language, nationality of a critic or viewer exposure. A runtime
over 40 minutes is classified operationally as feature length here; the three
Animated Feature nominees additionally have an explicitly named animation
group. `other_feature` does not establish the absence of animation. Runtime,
country and reception facts are derivative source assertions, not independent
primary-source adjudications. Source access and template dependencies can
still differ even with a fixed article revision.
