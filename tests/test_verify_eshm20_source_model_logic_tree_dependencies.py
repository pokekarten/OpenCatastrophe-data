# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import verify_eshm20_source_model_logic_tree_dependencies as bridge


SYNTHETIC = b"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<nrml xmlns=\"http://openquake.org/xmlns/nrml/0.5\">
  <logicTree logicTreeID=\"lt\">
    <logicTreeBranchSet branchSetID=\"source\" uncertaintyType=\"sourceModel\">
      <logicTreeBranch branchID=\"src-a\">
        <uncertaintyModel>source_models/a.xml source_models/b.xml</uncertaintyModel>
      </logicTreeBranch>
    </logicTreeBranchSet>
    <logicTreeBranchSet branchSetID=\"extend\" uncertaintyType=\"extendModel\">
      <logicTreeBranch branchID=\"ext-a\">
        <uncertaintyModel>source_models/a.xml source_models/c.xml</uncertaintyModel>
      </logicTreeBranch>
    </logicTreeBranchSet>
  </logicTree>
</nrml>
"""


def synthetic_inventory(*, include_c: bool = True) -> frozenset[str]:
    paths = {
        bridge.PREFIX + "source_models/a.xml",
        bridge.PREFIX + "source_models/b.xml",
    }
    if include_c:
        paths.add(bridge.PREFIX + "source_models/c.xml")
        filler_count = 59
    else:
        filler_count = 60
    paths.update(
        bridge.PREFIX + f"source_models/filler_{index:02d}.xml"
        for index in range(filler_count)
    )
    if len(paths) != bridge.FROZEN_INVENTORY_COUNT:
        raise AssertionError("synthetic inventory must preserve the frozen count contract")
    return frozenset(paths)


class VerifiedEshm20SourceModelLogicTreeDependencyTests(unittest.TestCase):
    def test_frozen_receipt_constants_match_canonical_handoff(self) -> None:
        self.assertEqual(bridge.EXPECTED_BYTE_COUNT, 17579)
        self.assertEqual(
            bridge.EXPECTED_SHA256,
            "97a37911f9eae73766f386686b112e5a4e111965da3e4e1543627c28d4201867",
        )
        self.assertEqual(bridge.RECEIPT_COMMENT_ID, 5301858821)
        self.assertEqual(bridge.RECEIPT_RUN_ID, 31880089623)
        self.assertEqual(
            bridge.RECEIPT_EXECUTION_SHA,
            "ab66e3e4c58c9b8f18587f1a8a51cf67cf9851b1",
        )
        self.assertEqual(bridge.SELECTION_RESULT_COMMENT_ID, 5301726249)
        self.assertEqual(bridge.INVENTORY_RECEIPT_COMMENT_ID, 5290449064)

    def test_verified_payload_uses_existing_parser_and_preserves_origins(self) -> None:
        inventory = synthetic_inventory()
        with mock.patch.object(bridge, "EXPECTED_BYTE_COUNT", len(SYNTHETIC)), mock.patch.object(
            bridge, "EXPECTED_SHA256", hashlib.sha256(SYNTHETIC).hexdigest()
        ), mock.patch.object(bridge, "FROZEN_INVENTORY_PATHS", inventory):
            result = bridge.extract_verified_source_model_dependencies(SYNTHETIC)

        self.assertEqual(
            [item["resolved_path"] for item in result["dependencies"]],
            [
                bridge.PREFIX + "source_models/a.xml",
                bridge.PREFIX + "source_models/b.xml",
                bridge.PREFIX + "source_models/c.xml",
            ],
        )
        self.assertEqual(
            result["dependencies"][0]["origins"],
            [
                {"uncertainty_type": "extendModel", "branch_id": "ext-a"},
                {"uncertainty_type": "sourceModel", "branch_id": "src-a"},
            ],
        )
        self.assertTrue(
            all(not item["is_hdf5_companion"] for item in result["dependencies"])
        )
        self.assertFalse(result["dependency_inventory_authorized"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])

    def test_wrong_hash_fails_before_parser_invocation(self) -> None:
        bad = b"X" + SYNTHETIC[1:]
        with mock.patch.object(bridge, "EXPECTED_BYTE_COUNT", len(SYNTHETIC)), mock.patch.object(
            bridge, "EXPECTED_SHA256", hashlib.sha256(SYNTHETIC).hexdigest()
        ), mock.patch.object(bridge, "extract_source_model_logic_tree_dependencies") as parser:
            with self.assertRaisesRegex(
                bridge.VerifiedSourceModelLogicTreeError, "SHA-256 mismatch"
            ):
                bridge.extract_verified_source_model_dependencies(bad)
        parser.assert_not_called()

    def test_wrong_byte_count_fails_before_parser_invocation(self) -> None:
        with mock.patch.object(bridge, "EXPECTED_BYTE_COUNT", len(SYNTHETIC)), mock.patch.object(
            bridge, "EXPECTED_SHA256", hashlib.sha256(SYNTHETIC).hexdigest()
        ), mock.patch.object(bridge, "extract_source_model_logic_tree_dependencies") as parser:
            with self.assertRaisesRegex(
                bridge.VerifiedSourceModelLogicTreeError, "byte count mismatch"
            ):
                bridge.extract_verified_source_model_dependencies(SYNTHETIC + b"x")
        parser.assert_not_called()

    def test_non_utf8_verified_bytes_fail_before_parser(self) -> None:
        payload = b"\xff\xfe"
        with mock.patch.object(bridge, "EXPECTED_BYTE_COUNT", len(payload)), mock.patch.object(
            bridge, "EXPECTED_SHA256", hashlib.sha256(payload).hexdigest()
        ), mock.patch.object(bridge, "extract_source_model_logic_tree_dependencies") as parser:
            with self.assertRaisesRegex(
                bridge.VerifiedSourceModelLogicTreeError, "strict UTF-8"
            ):
                bridge.extract_verified_source_model_dependencies(payload)
        parser.assert_not_called()

    def test_parser_failure_is_fail_closed(self) -> None:
        payload = b"<nrml><logicTree>"
        with mock.patch.object(bridge, "EXPECTED_BYTE_COUNT", len(payload)), mock.patch.object(
            bridge, "EXPECTED_SHA256", hashlib.sha256(payload).hexdigest()
        ), mock.patch.object(
            bridge, "FROZEN_INVENTORY_PATHS", synthetic_inventory()
        ):
            with self.assertRaisesRegex(
                bridge.VerifiedSourceModelLogicTreeError, "dependency parse failed"
            ):
                bridge.extract_verified_source_model_dependencies(payload)

    def test_out_of_inventory_dependency_fails_closed(self) -> None:
        inventory = synthetic_inventory(include_c=False)
        with mock.patch.object(bridge, "EXPECTED_BYTE_COUNT", len(SYNTHETIC)), mock.patch.object(
            bridge, "EXPECTED_SHA256", hashlib.sha256(SYNTHETIC).hexdigest()
        ), mock.patch.object(bridge, "FROZEN_INVENTORY_PATHS", inventory):
            with self.assertRaisesRegex(
                bridge.VerifiedSourceModelLogicTreeError, "absent from frozen inventory"
            ):
                bridge.extract_verified_source_model_dependencies(SYNTHETIC)

    def test_non_bytes_payload_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            bridge.VerifiedSourceModelLogicTreeError, "immutable bytes"
        ):
            bridge.extract_verified_source_model_dependencies(bytearray())  # type: ignore[arg-type]

    def test_local_reader_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "payload.xml"
            target.write_bytes(SYNTHETIC)
            link = root / "link.xml"
            try:
                link.symlink_to(target.name)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with mock.patch.object(bridge, "EXPECTED_BYTE_COUNT", len(SYNTHETIC)):
                with self.assertRaisesRegex(
                    bridge.VerifiedSourceModelLogicTreeError, "non-symlink regular file"
                ):
                    bridge._read_regular_file(link)

    def test_local_reader_returns_exact_regular_file_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "payload.xml"
            path.write_bytes(SYNTHETIC)
            with mock.patch.object(bridge, "EXPECTED_BYTE_COUNT", len(SYNTHETIC)):
                self.assertEqual(bridge._read_regular_file(path), SYNTHETIC)


if __name__ == "__main__":
    unittest.main()
