# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import verify_esrm20_event_hazard_dependencies as bridge


SYNTHETIC = b"[input]\nsource_model_logic_tree_file = ../Hazard/source.xml\ngsim_logic_tree_file = ../Hazard/gsim.xml\n"


def synthetic_spec(group: int = 1) -> bridge.RootSpec:
    return bridge.RootSpec(
        group=group,
        repository_path=f"Configuration_files/config_event_hazard_Group{group}.ini",
        operation_id=f"synthetic-group-{group}",
        byte_count=len(SYNTHETIC),
        sha256=hashlib.sha256(SYNTHETIC).hexdigest(),
        receipt_comment_id=1000 + group,
    )


class VerifiedEsrm20EventHazardDependencyTests(unittest.TestCase):
    def test_frozen_receipt_constants_match_canonical_handoffs(self) -> None:
        self.assertEqual(bridge.ROOT_SPECS[1].byte_count, 1766)
        self.assertEqual(
            bridge.ROOT_SPECS[1].sha256,
            "709168614dc4260a982fb4cc18956e1d4e236626efcc49bf1f1b9b4ff79969de",
        )
        self.assertEqual(bridge.ROOT_SPECS[1].receipt_comment_id, 5301296088)
        self.assertEqual(bridge.ROOT_SPECS[2].byte_count, 1673)
        self.assertEqual(
            bridge.ROOT_SPECS[2].sha256,
            "eb74edd2168bad20c23d4b0e1a99f5ed97ef28606a9ebfef6b8c8191d35dd34c",
        )
        self.assertEqual(bridge.ROOT_SPECS[2].receipt_comment_id, 5301299581)

    def test_group_identity_is_strict(self) -> None:
        for value in (0, 3, True, 1.0, "1"):
            with self.subTest(value=value):
                with self.assertRaises(bridge.VerifiedEventHazardConfigError):
                    bridge._root_spec(value)  # type: ignore[arg-type]

    def test_verified_payload_is_parsed_with_exact_group_path(self) -> None:
        specs = {1: synthetic_spec(1), 2: synthetic_spec(2)}
        with mock.patch.object(bridge, "ROOT_SPECS", specs):
            result1 = bridge.extract_verified_event_hazard_dependencies(1, SYNTHETIC)
            result2 = bridge.extract_verified_event_hazard_dependencies(2, SYNTHETIC)

        self.assertEqual(result1["group"], 1)
        self.assertEqual(result2["group"], 2)
        self.assertNotEqual(result1["repository_path"], result2["repository_path"])
        self.assertEqual(
            [item["resolved_path"] for item in result1["dependencies"]],
            ["Hazard/gsim.xml", "Hazard/source.xml"],
        )
        self.assertFalse(result1["dependency_inventory_authorized"])
        self.assertFalse(result1["external_bytes_persisted"])
        self.assertFalse(result1["publication_authorized"])

    def test_wrong_bytes_fail_before_parser_invocation(self) -> None:
        spec = synthetic_spec(1)
        bad = b"X" + SYNTHETIC[1:]
        with mock.patch.object(bridge, "ROOT_SPECS", {1: spec}), mock.patch.object(
            bridge, "extract_openquake_config_references"
        ) as parser:
            with self.assertRaisesRegex(bridge.VerifiedEventHazardConfigError, "SHA-256 mismatch"):
                bridge.extract_verified_event_hazard_dependencies(1, bad)
        parser.assert_not_called()

    def test_wrong_byte_count_fails_before_parser_invocation(self) -> None:
        spec = synthetic_spec(1)
        with mock.patch.object(bridge, "ROOT_SPECS", {1: spec}), mock.patch.object(
            bridge, "extract_openquake_config_references"
        ) as parser:
            with self.assertRaisesRegex(bridge.VerifiedEventHazardConfigError, "byte count mismatch"):
                bridge.extract_verified_event_hazard_dependencies(1, SYNTHETIC + b"x")
        parser.assert_not_called()

    def test_non_utf8_verified_bytes_fail_before_parser(self) -> None:
        payload = b"\xff\xfe"
        spec = bridge.RootSpec(
            group=1,
            repository_path="Configuration_files/config_event_hazard_Group1.ini",
            operation_id="synthetic",
            byte_count=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
            receipt_comment_id=1001,
        )
        with mock.patch.object(bridge, "ROOT_SPECS", {1: spec}), mock.patch.object(
            bridge, "extract_openquake_config_references"
        ) as parser:
            with self.assertRaisesRegex(bridge.VerifiedEventHazardConfigError, "strict UTF-8"):
                bridge.extract_verified_event_hazard_dependencies(1, payload)
        parser.assert_not_called()

    def test_parser_failures_are_fail_closed(self) -> None:
        payload = b"[input]\nsource_model_logic_tree_file = ../../outside.xml\n"
        spec = bridge.RootSpec(
            group=1,
            repository_path="Configuration_files/config_event_hazard_Group1.ini",
            operation_id="synthetic",
            byte_count=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
            receipt_comment_id=1001,
        )
        with mock.patch.object(bridge, "ROOT_SPECS", {1: spec}):
            with self.assertRaisesRegex(bridge.VerifiedEventHazardConfigError, "dependency parse failed"):
                bridge.extract_verified_event_hazard_dependencies(1, payload)

    def test_local_reader_rejects_symlinks(self) -> None:
        spec = synthetic_spec(1)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "payload.ini"
            target.write_bytes(SYNTHETIC)
            link = root / "link.ini"
            try:
                link.symlink_to(target.name)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with self.assertRaisesRegex(bridge.VerifiedEventHazardConfigError, "non-symlink regular file"):
                bridge._read_regular_file(link, spec)

    def test_local_reader_returns_exact_regular_file_bytes(self) -> None:
        spec = synthetic_spec(1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "payload.ini"
            path.write_bytes(SYNTHETIC)
            self.assertEqual(bridge._read_regular_file(path, spec), SYNTHETIC)


if __name__ == "__main__":
    unittest.main()
