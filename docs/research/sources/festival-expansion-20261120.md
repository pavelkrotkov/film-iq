# Festival, documentary, animation and preservation source expansion

Checked November 20, 2026 for the user-authorized suggestion-library expansion.
The source records stay in this worktree's ignored `.cache/source-library/festivals/`
directory. These observations supply import candidates. Catalog identity approval
and the live Kaneo import are separate controller steps.

## Acquired factual records

| Bundle | Declared coverage | Observations | Completeness |
| --- | --- | ---: | --- |
| `national-film-registry.json` | All 37 Library of Congress annual classes, 1989–2025 | 925 | Exactly 25 records per class, including collections and unresolved titles |
| `festival-primary-awards.json` | Venice Golden Lion 2010–2026, Rotterdam Tiger 2010–2026, IDFA international top prize 2010–2026, Envision 2021–2026, short documentary 2021–2025, seven CPH:DOX 2026 prize winners | 81 | Complete for the explicitly named prize/edition slices, covering 69 slices |
| `festival-awards.json` | Date-qualified Wikidata claims across twelve named festival-award categories, 2010–November 20, 2026 | 135 | All returned claims retained. Original festival-edition coverage remains partial |
| `annecy-short-awards.json` | Eight date-qualified Annecy short-film Cristal winner claims | 8 | Partial historical festival coverage |

The festival bundles overlap. Their combined row count is an observation count,
and import must deduplicate works while retaining each source observation.

## National Film Registry

The Library's [current FAQ](https://www.loc.gov/programs/national-film-preservation-board/film-registry/frequently-asked-questions/)
states that the Registry contained 925 selections after the 2025 class, announced
January 29, 2026. Its [2025 announcement](https://blogs.loc.gov/now-see-hear/2026/01/announcing-the-2025-national-film-registry/)
identifies the same total. No 2026 Registry class was presumed.

The [official alphabetical PDF](https://www.loc.gov/static/programs/national-film-preservation-board/documents/Registry-Titles-alphabetically.pdf)
contains 725 selections through 2017. The current combined HTML table returned
HTTP 403. The source reconstruction uses the available government PDF and the
eight annual 2018–2025 official announcements, retaining the exact original
source URL and locator for every entry. The historical PDF's native text order
overlays several columns. Spatial PDFKit selections rectified the Buffalo Creek
Flood, Commandment Keeper Church, Cologne, Chinatown, Dickson Experimental Sound
Film, Curse of Quon Gwon and Middleton Family rows. Final checks require 925
distinct title/date records and exactly 25 entries in each of the 37 classes.

Registry source years remain separate from catalog years. The source labels
*Stop Making Sense* 1984, *Sullivan's Travels* 1941 and *Harold and Maude* 1972.
Catalogs sometimes use different release years. Collections, home movies,
serials and multi-year works remain in the source ledger even where a single
catalog film cannot be established.

The stable main bundle contains 785 candidate exact normalized-title/year
Wikidata crosswalks with TMDB and IMDb IDs. The separate
`registry-additional-identities.json` contains 39 additional exact-title/year
crosswalk candidates, 19 explicit source/catalog year-disagreement proposals,
and 82 records still unresolved. These are candidates for independent catalog
validation. In particular, *Dog Star Man* requires checking the whole-work
identity against its constituent parts.

## Complete named festival slices

- The [official Venice history](https://www.labiennale.org/en/history-venice-film-festival)
  gives all seventeen Golden Lion for Best Film winners from 2010 through 2026.
  The latest is *Kvinde Ukendt (Woman Unknown)* by May el-Toukhy. Lifetime honors
  and acting prizes are separately identified on the source and excluded from
  this declared film-prize slice.
- The [official Rotterdam Tiger archive](https://iffr.com/en/awards-competitions/tiger-competition)
  gives 29 Tiger-winning films across 2010–2026. Each 2010–2015 edition has three
  co-winners. Each 2016–2026 edition has one. Special Jury Awards retain their
  separate category and are outside this slice. Direct HTTP access returned 403,
  and the published page was inspected through its accessible indexed rendition.
- The [official IDFA historical archive](https://professionals.idfa.nl/program/awards-juries/winners-1988-2025/)
  provides the international feature top prize for 2010–2025, the Envision Best
  Film prize for 2021–2025 and short documentary winners for 2021–2025. The
  international award category changed in 2021, and that distinction is retained.
  Award-edition years are not silently assigned as film production years.
- [IDFA's 2026 winners](https://festival.idfa.nl/en/news/award-winners-idfa-2026/)
  were announced November 19. The International Competition Best Film is
  *The Year of the Ghost* by Louis HotHotHot, and Envision Best Film is
  *Memories of Lightning* by Riccardo Giacconi. The official individual film
  records corroborate production year 2026 for both. Their catalog IDs require
  review before enrollment.
- The [CPH:DOX 2026 announcement](https://cphdox.dk/here-are-all-the-award-winners-of-cphdox-2026/)
  supplies seven explicitly separated prize winners across DOX:AWARD, NEW:VISION,
  F:ACT, NEXT:WAVE, HUMAN:RIGHTS, NORDIC:DOX and FIPRESCI. Each corresponding film
  is explicitly labeled 2026 on the source. Special mentions and interactive
  works are outside these seven declared film-winner slices.

Five primary-source entries include explicit translated alternate titles.
Subtitles and unexplained title differences are not fabricated as translations.

## Structured festival crosswalk

The CC0 Wikidata bundle retains film-level winner statements for Cannes Palme
d'Or and short Palme, Venice Golden Lion, Berlin Golden Bear, Locarno Golden
Leopard, Rotterdam Tiger, Sundance's four principal jury categories, TIFF
People's Choice, and Annecy feature/short Cristals. Each observation preserves
its Wikidata statement URI, source references, award category, award year,
recipient kind and catalog-ID candidates. Claims are attributed to Wikidata.
An official festival URL recorded as a statement reference does not imply that
the agent independently rechecked every original festival page.

The first combined SPARQL request timed out. Smaller category-specific requests
and a bounded retry for Annecy shorts succeeded. Failed requests and absent or
undated statements were not converted into assertions that a prize was absent.
The partial source documents name their scope explicitly.

## Ranking, provenance and follow-up

Preservation selections, festival winners, audience prizes and individual critic
ballots provide different evidence. These bundles assign `registry_selection`
or `award_outcome`, preserve co-winners, and assign no numeric rank to an award.
Source display positions never establish quality rank. The same award reported
by Wikidata and by the festival must count as one outcome, with both provenance
paths retained. An audience prize does not become an individual critic vote.

The large preservation cohort is US-focused. Rotterdam, IDFA and specialist
documentary/animation evidence broaden geography and form, while the parallel
annual-critics work supplies additional editorial perspectives. Geographic
coverage still needs measurement after identity-approved enrollment.

Official [Annecy 2026 awards](https://www.annecyfestival.com/en/the-festival/2026-awards)
name *The Violinist* and *Paper Trail* as the feature and short Cristal winners.
Clermont-Ferrand, full IDFA historical side categories, CPH:DOX historical
editions and several missing date-qualified festival records remain explicit
expansion work. The current bundles make no claim of an exhaustive worldwide
film library.

## Retention and reuse

Only factual titles, years, credits, award outcomes, locators and source URLs
are imported. Government registry records are distinguished from the films and
third-party imagery they describe. Wikidata's [structured-data licensing](https://www.wikidata.org/wiki/Wikidata:Licensing)
is CC0. Publisher article bodies, jury statements, paywalled material, images,
full film copies and streaming catalog dumps are excluded from these datasets.
The one-time factual primary-source transcriptions do not assert a blanket
license for unattended copying or redistribution of publisher material.
