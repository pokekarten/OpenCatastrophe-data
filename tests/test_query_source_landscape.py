# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.query_source_landscape import (
    LandscapeQueryError,
    load_landscape,
    query_entries,
)

ROOT = Path(__file__).resolve().parents[1]


class SourceLandscapeQueryTests(unittest.TestCase):
    def test_current_registry_loads_and_remains_non_admission(self) -> None:
        entries = load_landscape()
        self.assertGreater(len(entries), 0)
        self.assertTrue(all(entry["admission_status"] == "not_admitted" for entry in entries))
        self.assertEqual(
            [entry["candidate_id"] for entry in entries],
            sorted(entry["candidate_id"] for entry in entries),
        )

    def test_cli_executes_directly_and_returns_stable_machine_json(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/query_source_landscape.py", "--id", "gfz.world-stress-map.2025"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["profile"], "opencatastrophe-source-landscape-query-v1")
        self.assertEqual(payload["scope"], "non_admission_discovery_only")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["results"][0]["candidate_id"], "gfz.world-stress-map.2025")

    def test_category_filter_is_exact_and_case_insensitive(self) -> None:
        entries = load_landscape()
        matches = query_entries(entries, categories=("WILDFIRE",))
        ids = {entry["candidate_id"] for entry in matches}
        self.assertIn("nasa.lance.firms.active-fire", ids)
        self.assertIn("nasa.modis.mcd64a1.v6.1", ids)
        self.assertNotIn("noaa.ncei.storm-events", ids)

    def test_multiple_filters_use_and_semantics(self) -> None:
        entries = load_landscape()
        matches = query_entries(
            entries,
            categories=("validation",),
            provider="NOAA",
            text="water level",
        )
        self.assertEqual([entry["candidate_id"] for entry in matches], ["noaa.coops.water-levels"])

    def test_role_and_exact_id_filters_are_machine_addressable(self) -> None:
        entries = load_landscape()
        role_matches = query_entries(entries, roles=("storm_surge_validation",))
        self.assertEqual([entry["candidate_id"] for entry in role_matches], ["noaa.coops.water-levels"])
        id_matches = query_entries(entries, candidate_id="gfz.world-stress-map.2025")
        self.assertEqual(len(id_matches), 1)
        self.assertEqual(id_matches[0]["name"], "World Stress Map Database Release 2025")

    def test_duplicate_candidate_id_across_shards_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            entry = self._entry("example.source")
            self._write_shard(directory / "sources-a.json", [entry])
            self._write_shard(directory / "sources-b.json", [entry])
            with self.assertRaisesRegex(LandscapeQueryError, "duplicate candidate_id"):
                load_landscape(directory)

    def test_duplicate_json_key_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources-bad.json"
            path.write_text(
                '{"schema_version":"1.0.0","schema_version":"1.0.0",'
                '"purpose":"Non-admission test","review_date":"2026-08-10","entries":[]}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(LandscapeQueryError, "duplicate JSON key"):
                load_landscape(path.parent)

    def test_non_finite_json_number_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources-bad.json"
            path.write_text(
                '{"schema_version":"1.0.0","purpose":"Non-admission test",'
                '"review_date":"2026-08-10","entries":[NaN]}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(LandscapeQueryError, "non-finite JSON number"):
                load_landscape(path.parent)

    def test_invalid_review_calendar_date_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            self._write_shard(directory / "sources-a.json", [self._entry("example.source")])
            payload = json.loads((directory / "sources-a.json").read_text(encoding="utf-8"))
            payload["review_date"] = "2026-02-30"
            (directory / "sources-a.json").write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(LandscapeQueryError, "valid calendar date"):
                load_landscape(directory)

    def test_admission_or_review_escalation_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            entry = self._entry("example.source")
            entry["admission_status"] = "admitted"
            self._write_shard(directory / "sources-a.json", [entry])
            with self.assertRaisesRegex(LandscapeQueryError, "admission_status must remain not_admitted"):
                load_landscape(directory)

    def test_embedded_url_credentials_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            entry = self._entry("example.source")
            entry["authoritative_url"] = "https://user:secret@example.invalid/source"
            self._write_shard(directory / "sources-a.json", [entry])
            with self.assertRaisesRegex(LandscapeQueryError, "must not embed credentials"):
                load_landscape(directory)

    def test_non_public_ip_url_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            entry = self._entry("example.source")
            entry["authoritative_url"] = "https://192.0.2.10/source"
            self._write_shard(directory / "sources-a.json", [entry])
            with self.assertRaisesRegex(LandscapeQueryError, "non-public IP address"):
                load_landscape(directory)

    def test_malformed_url_port_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            entry = self._entry("example.source")
            entry["authoritative_url"] = "https://example.invalid:not-a-port/source"
            self._write_shard(directory / "sources-a.json", [entry])
            with self.assertRaisesRegex(LandscapeQueryError, "authoritative_url is malformed"):
                load_landscape(directory)

    def test_signature_query_parameter_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            entry = self._entry("example.source")
            entry["authoritative_url"] = "https://example.invalid/source?signature=synthetic"
            self._write_shard(directory / "sources-a.json", [entry])
            with self.assertRaisesRegex(LandscapeQueryError, "signature query parameters"):
                load_landscape(directory)

    def test_gcs_signed_url_parameter_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            entry = self._entry("example.source")
            entry["authoritative_url"] = "https://example.invalid/source?X-Goog-Signature=synthetic"
            self._write_shard(directory / "sources-a.json", [entry])
            with self.assertRaisesRegex(LandscapeQueryError, "signature query parameters"):
                load_landscape(directory)

    @staticmethod
    def _entry(candidate_id: str) -> dict[str, object]:
        return {
            "candidate_id": candidate_id,
            "name": "Example Source",
            "provider": "Example Provider",
            "categories": ["validation"],
            "spatial_scope": "global",
            "temporal_scope": "example",
            "resolution_or_granularity": "example",
            "potential_roles": ["example_validation"],
            "authoritative_url": "https://example.invalid/source",
            "access_class_hint": "unknown",
            "candidate_status": "evidence_checked",
            "rights_review_status": "not_reviewed",
            "scientific_review_status": "not_reviewed",
            "admission_status": "not_admitted",
            "note": "Synthetic test metadata only.",
        }

    @staticmethod
    def _write_shard(path: Path, entries: list[dict[str, object]]) -> None:
        payload = {
            "schema_version": "1.0.0",
            "purpose": "Non-admission synthetic test registry.",
            "review_date": "2026-08-10",
            "entries": entries,
        }
        path.write_text(json.dumps(payload), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
