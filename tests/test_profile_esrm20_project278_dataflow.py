# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest

from scripts import profile_esrm20_project278_dataflow as subject


_SOURCE = b'''import numpy as np

def preprocess(frame):
    frame = frame.to_crs("EPSG:3035")
    return frame

def emit_site(frame, value):
    output = frame.to_crs("EPSG:4326")
    longitude = output.longitude
    latitude = output.latitude
    vs30 = value
    if np.isnan(vs30):
        vs30 = -999
    payload = {"longitude": longitude, "latitude": latitude, "vs30": vs30}
    write_xml(payload)
    return payload

def classify(value):
    if value is None:
        return "Unknown"
    return value

def outer(frame):
    def inner():
        output = frame.to_crs("EPSG:4326")
        write_xml(output)
        return output
    return frame
'''

_NODE = b'''def make_node(longitude, latitude):
    node = {"lon": longitude, "lat": latitude}
    return node
'''


def _identity(data: bytes) -> dict[str, object]:
    return {
        "byte_count": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "git_blob_sha1": subject._git_blob_sha1(data),
    }


class Project278DataflowProfileTests(unittest.TestCase):
    def _profile(self) -> dict[str, object]:
        return subject._profile_sources_for_test(
            {
                "exposure2site/exposure_to_site_tools.py": _SOURCE,
                "exposure2site/node_handler.py": _NODE,
            },
            identities={
                "exposure2site/exposure_to_site_tools.py": _identity(_SOURCE),
                "exposure2site/node_handler.py": _identity(_NODE),
            },
        )

    def test_profile_finds_crs_writer_and_sentinel_relations(self) -> None:
        profile = self._profile()
        functions = {
            (item["repository_path"], item["function"]): item
            for item in profile["candidate_functions"]
        }

        emit = functions[("exposure2site/exposure_to_site_tools.py", "emit_site")]
        self.assertIn("epsg_4326", emit["crs_markers"])
        self.assertIn("write_xml", emit["writer_calls"])
        self.assertIn("negative_999", emit["sentinel_markers"])
        self.assertIn("nan", emit["sentinel_markers"])
        self.assertEqual(
            {"longitude", "latitude", "vs30"} - set(emit["site_fields"]),
            set(),
        )
        self.assertIn("crs_and_writer_same_function", emit["relations"])
        self.assertIn("sentinel_and_writer_same_function", emit["relations"])

        preprocess = functions[("exposure2site/exposure_to_site_tools.py", "preprocess")]
        self.assertIn("epsg_3035", preprocess["crs_markers"])
        self.assertEqual(preprocess["writer_calls"], [])
        self.assertNotIn("crs_and_writer_same_function", preprocess["relations"])

    def test_profile_emits_bounded_structural_facts_not_source_text(self) -> None:
        profile = self._profile()
        self.assertIs(profile["raw_source_returned"], False)
        self.assertIs(profile["crs_coordinate_semantics_verified"], False)
        self.assertIs(profile["missingness_semantics_verified"], False)
        self.assertIn(
            "exposure2site/exposure_to_site_tools.py:emit_site",
            profile["crs_writer_candidate_functions"],
        )
        serialized = json.dumps(profile, sort_keys=True)
        self.assertNotIn("frame = frame.to_crs", serialized)
        self.assertNotIn("payload = {", serialized)
        self.assertNotIn('return "Unknown"', serialized)

    def test_statement_records_distinguish_markers_from_writer_calls(self) -> None:
        profile = self._profile()
        emit_records = [
            record
            for record in profile["statement_records"]
            if record["function"] == "emit_site"
        ]
        self.assertTrue(any("epsg_4326" in record["markers"] for record in emit_records))
        self.assertTrue(any("negative_999" in record["markers"] for record in emit_records))
        self.assertTrue(any("write_xml" in record["writer_calls"] for record in emit_records))

    def test_nested_scope_does_not_contaminate_parent_function(self) -> None:
        profile = self._profile()
        functions = {
            (item["repository_path"], item["function"]): item
            for item in profile["candidate_functions"]
        }
        self.assertNotIn(("exposure2site/exposure_to_site_tools.py", "outer"), functions)
        inner = functions[("exposure2site/exposure_to_site_tools.py", "inner")]
        self.assertIn("epsg_4326", inner["crs_markers"])
        self.assertIn("write_xml", inner["writer_calls"])
        self.assertIn("crs_and_writer_same_function", inner["relations"])

    def test_identity_drift_fails_before_ast_semantics(self) -> None:
        identities = {
            "exposure2site/exposure_to_site_tools.py": _identity(_SOURCE),
            "exposure2site/node_handler.py": _identity(_NODE),
        }
        identities["exposure2site/exposure_to_site_tools.py"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(subject.Project278DataflowProfileError, "SHA-256 drifted"):
            subject._profile_sources_for_test(
                {
                    "exposure2site/exposure_to_site_tools.py": _SOURCE,
                    "exposure2site/node_handler.py": _NODE,
                },
                identities=identities,
            )

    def test_production_entrypoint_rejects_non_frozen_bytes(self) -> None:
        with self.assertRaises(subject.Project278DataflowProfileError):
            subject.profile_verified_project278_sources(
                {
                    "exposure2site/exposure_to_site_tools.py": _SOURCE,
                    "exposure2site/node_handler.py": _NODE,
                }
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
