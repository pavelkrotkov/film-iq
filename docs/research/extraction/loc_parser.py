"""Extract titles from the Library of Congress public-domain gallery."""

from html.parser import HTMLParser


class GalleryTitles(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.active = False
        self.parts: list[str] = []
        self.titles: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = dict(attrs).get("class") or ""
        if tag == "span" and "masonry-gallery-item-title" in classes.split():
            self.active = True
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.active:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "span" and self.active:
            self.titles.append("".join(self.parts).strip())
            self.active = False


def extract_titles(html: str) -> list[str]:
    parser = GalleryTitles()
    parser.feed(html)
    parser.close()
    return parser.titles
