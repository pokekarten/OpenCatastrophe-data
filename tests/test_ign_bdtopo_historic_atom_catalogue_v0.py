# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic Atom-only tests; no third-party source bytes or network traffic."""

import sys
from pathlib import Path
import unittest
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research_runners"))
from ign_bdtopo_historic_atom_catalogue_v0 import (
    CatalogueError, catalogue_url, inspect_pages, parse_atom_page,
)


def feed(entries, total, *, namespace=True):
    if namespace:
        head = ('<feed xmlns="http://www.w3.org/2005/Atom" '
                'xmlns:gpf_dl="urn:sample:ign-download">')
        body = "".join(
            f"<entry><id>{escape(eid)}</id><title>{escape(title)}</title></entry>"
            for eid, title in entries
        )
    else:
        head = "<feed>"
        body = "".join(
            f"<entry><id>{escape(eid)}</id><title>{escape(title)}</title></entry>"
            for eid, title in entries
        )
    return (head + f"<gpf_dl:totalentries>{total}</gpf_dl:totalentries>" + body + "</feed>").encode()


class HistoricalIGNCatalogueTests(unittest.TestCase):
    def test_official_query_exact_department_date_and_page(self):
        url = catalogue_url(page=2)
        self.assertIn("zone=D077", url)
        self.assertIn("editionDateFrom=2015-01-01", url)
        self.assertIn("editionDateTo=2016-12-31", url)
        self.assertIn("page=2", url)
        self.assertTrue(url.startswith("https://data.geopf.fr/telechargement/resource/BD-TOPO?"))

    def test_reject_unreviewed_scope(self):
        with self.assertRaises(CatalogueError):
            catalogue_url(zone="D075")
        with self.assertRaises(CatalogueError):
            catalogue_url(resource="../secrets")
        with self.assertRaises(CatalogueError):
            catalogue_url(page=101)

    def test_complete_atom_page_is_discovery_not_building_admission(self):
        data = feed([("e1", "BD TOPO 2016 D077"), ("e2", "Other theme")], 2)
        report = inspect_pages([data], page_size=2)
        self.assertTrue(report["catalogue_pagination_complete"])
        self.assertEqual(report["distinct_entries_seen"], 2)
        self.assertEqual(report["title_matched_candidate_count"], 1)
        self.assertEqual(report["candidate_titles"][0]["candidate_title_years_not_verified_edition_dates"], "2016")
        self.assertFalse(report["2016_archive_download_verified"])
        self.assertFalse(report["historical_building_geometry_verified"])
        self.assertFalse(report["model_input_approved"])

    def test_two_pages_detected(self):
        one = feed([("e1", "BD-TOPO v2 2015"), ("e2", "Other")], 3)
        two = feed([("e3", "BDTOPO D077 2016")], 3)
        report = inspect_pages([one, two], page_size=2)
        self.assertEqual(report["distinct_entries_seen"], 3)
        self.assertTrue(report["catalogue_pagination_complete"])

    def test_partial_pagination_stays_partial(self):
        one = feed([("e1", "BD-TOPO v2 2015"), ("e2", "Other")], 3)
        report = inspect_pages([one], page_size=2)
        self.assertFalse(report["catalogue_pagination_complete"])

    def test_403_html_does_not_become_zero_entries(self):
        with self.assertRaisesRegex(CatalogueError, "Atom"):
            parse_atom_page(b"<html><h1>403 Forbidden</h1></html>")

    def test_duplicate_across_pages_fails(self):
        a = feed([("e1", "BD TOPO 2015")], 2)
        b = feed([("e1", "BD TOPO 2016")], 2)
        with self.assertRaisesRegex(CatalogueError, "repeated"):
            inspect_pages([a, b], page_size=1)

    def test_invalid_count_fails_closed(self):
        with self.assertRaisesRegex(CatalogueError, "invalid totalentries"):
            parse_atom_page(feed([], "NaN"))

    def test_missing_count_fails_closed(self):
        atom = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>a</id><title>BD TOPO</title></entry></feed>'
        with self.assertRaisesRegex(CatalogueError, "totalentries"):
            inspect_pages([atom], page_size=1)

    def test_doctype_and_entities_rejected(self):
        with self.assertRaises(CatalogueError):
            parse_atom_page(b'<!DOCTYPE feed [<!ENTITY x "y">]><feed/>')

    def test_wrong_atom_namespace_rejected(self):
        with self.assertRaises(CatalogueError):
            parse_atom_page(b'<feed><entry><id>e</id><title>BD TOPO</title></entry></feed>')

    def test_short_page_before_last_is_unsafe(self):
        one = feed([("e1", "BD TOPO 2015")], 3)
        two = feed([("e2", "BD TOPO 2016")], 3)
        with self.assertRaisesRegex(CatalogueError, "short page"):
            inspect_pages([one, two], page_size=2)

    def test_changing_reported_total_fails(self):
        one = feed([("e1", "BD TOPO 2015")], 2)
        two = feed([("e2", "BD TOPO 2016")], 3)
        with self.assertRaisesRegex(CatalogueError, "changing totalentries"):
            inspect_pages([one, two], page_size=1)


if __name__ == "__main__":
    unittest.main()
