"""Offline checks for the source-specific gallery benchmark."""

import unittest
from hashlib import sha256

from docs.research.extraction.loc_baseline import evaluate
from docs.research.extraction.loc_parser import extract_titles


class GalleryChecks(unittest.TestCase):
    def test_gallery_titles_ignore_other_spans_and_decode_entities(self) -> None:
        html = (
            '<span class="navigation">Ignore</span>'
            '<span class="masonry-gallery-item-title extra">One &amp; Two</span>'
            '<span class="masonry-gallery-item-title">Three</span>'
        )
        self.assertEqual(extract_titles(html), ["One & Two", "Three"])

    def test_revision_and_completeness_are_checked(self) -> None:
        body = b'<span class="masonry-gallery-item-title">One</span>'
        revision = sha256(body).hexdigest()
        result = evaluate(body, ["One", "Two"], revision)
        self.assertEqual(result["recall"], 0.5)
        self.assertFalse(result["complete"])
        with self.assertRaisesRegex(ValueError, "revision changed"):
            evaluate(body, ["One"], "wrong revision")


if __name__ == "__main__":
    unittest.main()
