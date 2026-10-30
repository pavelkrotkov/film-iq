# Corpus attribution and reuse

The `*.wikitext.json` and `*.text.json` files contain Wikipedia contributor
text under Creative Commons Attribution-ShareAlike 4.0. The exact publisher
declaration and request receipt are in `rights.json` and
`rights-receipt.json`. Preserve this license and attribution when redistributing
or adapting the text and the derived audit records. Research code is MIT.

Each `*.receipt.json` identifies the article, section and revision. Contributor
attribution is provided by the pinned article URL
`https://en.wikipedia.org/w/index.php?oldid=REVISION` and its linked history;
all 32 concrete article/history links are enumerated in [ATTRIBUTION.md](ATTRIBUTION.md).
the original API request and exact response hashes are recorded alongside it.
The source responses are unmodified section-only API captures. Rendered
templates can change independently of an article revision; the recorded body
hash freezes the observed rendering. Image references may occur in markup;
no image, audio or video bytes are acquired.

The CC license applies to the retained Wikipedia text and derivative audit
records, not to images or the original NBR, BFI, BBC, Academy or festival
publications. These are derivative observations, never additional independent
critical votes. Wikipedia's reuse terms are at
https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use#7._Licensing_of_Content
and the license is https://creativecommons.org/licenses/by-sa/4.0/.

`selection.json` records section scope and the development/holdout assignment.
These captures cover static lists/tables only; they are not a representative
test of PDF programmes, source spreadsheets, browser-dependent pages, individual
partial ballots or difficult prose. Missing formats remain untested.
