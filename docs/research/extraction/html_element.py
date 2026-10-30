"""Read visible text and descendants from frozen HTML elements."""

from collections.abc import Iterator
from dataclasses import dataclass, field


@dataclass
class Element:
    tag: str
    attrs: dict[str, str | None] = field(default_factory=dict)
    children: list["Element | str"] = field(default_factory=list)

    def elements(self, tag: str) -> Iterator["Element"]:
        for child in self.children:
            if isinstance(child, Element):
                if child.tag == tag:
                    yield child
                yield from child.elements(tag)

    def text(self) -> str:
        parts = [
            c.text() if isinstance(c, Element) else c
            for c in self.children
            if not isinstance(c, Element) or c.tag != "sup"
        ]
        return " ".join("".join(parts).split())
