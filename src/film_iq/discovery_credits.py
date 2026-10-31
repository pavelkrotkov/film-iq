"""Visible provider credits do not grant rights or expose private review notes."""

TMDB_LOGO = "https://www.themoviedb.org/assets/v4/logos/v2/blue_long_2-9665a76b1ae401a510ec1e0ca40ddcb3b0cfe45f1d51b77a308fea0845885648.svg"
CANONICAL = {
    "tmdb": f'<a href="https://www.themoviedb.org/"><img src="{TMDB_LOGO}" alt="TMDB" width="120"></a> This product uses the TMDB API but is not endorsed or certified by TMDB.',
    "motn": "[Streaming Availability API by Movie of the Night](https://www.movieofthenight.com/about/api)",
}


def visible_credits(report: dict) -> list[str]:
    sources, texts, watch_sources = _inputs(report)
    texts.update(CANONICAL[source] for source in sources if source in CANONICAL)
    if "tmdb" in watch_sources:
        texts.add("Watch-provider data: [JustWatch](https://www.justwatch.com/)")
    return ["Credits: " + "; ".join(sorted(texts))] if texts else []


def _inputs(report: dict) -> tuple[set[str], set[str], set[str]]:
    states = [state for item in report["candidates"] for state in item.get("offer_states", [])]
    sources = {state["latest_attempt"]["source"] for state in states}
    watch_sources = sources.copy()
    texts = {state["attribution"] for state in states}
    catalog = report.get("display_catalog", {})
    if catalog.get("status") == "fresh":
        texts.add(catalog["attribution"])
        if "tmdb" in catalog["attribution"].lower():
            sources.add("tmdb")
    return sources, texts, watch_sources
