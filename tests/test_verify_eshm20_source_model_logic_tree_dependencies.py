# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

try:
    from scripts import verify_eshm20_source_model_logic_tree_dependencies as module
except ModuleNotFoundError:
    import verify_eshm20_source_model_logic_tree_dependencies as module

SYNTHETIC = b"""<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">
  <logicTree logicTreeID="lt1">
    <logicTreeBranchingLevel branchingLevelID="bl1">
      <logicTreeBranchSet branchSetID="bs1" uncertaintyType="sourceModel">
        <logicTreeBranch branchID="b1">
          <uncertaintyModel>source_models/a.xml source_models/b.xml</uncertaintyModel>
        </logicTreeBranch>
      </logicTreeBranchSet>
    </logicTreeBranchingLevel>
  </logicTree>
</nrml>
"""


def inventory_with(*paths: str) -> frozenset[str]:
    values = {module.REPOSITORY_PATH, *paths}
    index = 0
    while len(values) < 62:
        values.add(module.PREFIX + f"unused/filler-{index}.xml")
        index += 1
    return frozenset(values)


class VerifiedEshm20SourceModelLogicTreeDependenciesTests(unittest.TestCase):
    def frozen_to(self, payload: bytes, *, inventory: frozenset[str]):
        return mock.patch.multiple(
            module,
            EXPECTED_BYTE_COUNT=len(payload),
            EXPECTED_SHA256=hashlib.sha256(payload).hexdigest(),
            FROZEN_INVENTORY_PATHS=inventory,
        )

    def test_verified_bytes_are_parsed_deterministically(self) -> None:
        a = module.PREFIX + "source_models/a.xml"
        b = module.PREFIX + "source_models/b.xml"
        inventory = inventory_with(a, b)
        with self.frozen_to(SYNTHETIC, inventory=inventory):
            result = module.extract_verified_source_model_dependencies(SYNTHETIC)
        self.assertEqual(result["byte_count"], len(SYNTHETIC))
        self.assertEqual(result["sha256"], hashlib.sha256(SYNTHETIC).hexdigest())
        self.assertEqual(
            [item["resolved_path"] for item in result["dependencies"]],
            [a, b],
        )
        self.assertEqual(
            result["dependencies"][0]["origins"],
            [{"uncertainty_type": "sourceModel", "branch_id": "b1"}],
        )
        self.assertFalse(result["dependency_inventory_authorized"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertNotIn(SYNTHETIC.decode("utf-8"), json.dumps(result, sort_keys=True))

    def test_hdf5_companion_is_metadata_candidate_not_authority(self) -> None:
        source = module.PREFIX + "source_models/a.xml"
        companion = module.PREFIX + "source_models/a.hdf5"
        payload = SYNTHETIC.replace(
            b"source_models/a.xml source_models/b.xml",
            b"source_models/a.xml",
        )
        inventory = inventory_with(source, companion)
        with self.frozen_to(payload, inventory=inventory):
            result = module.extract_verified_source_model_dependencies(payload)
        self.assertEqual(
            [(item["resolved_path"], item["is_hdf5_companion"]) for item in result["dependencies"]],
            [(companion, True), (source, False)],
        )
        self.assertFalse(result["dependency_inventory_authorized"])

    def test_public_bridge_has_no_receipt_or_inventory_override(self) -> None:
        self.assertEqual(
            list(inspect.signature(module.extract_verified_source_model_dependencies).parameters),
            ["payload"],
        )

    def test_byte_count_mismatch_blocks_before_parser(self) -> None:
        with mock.patch.object(module, "extract_source_model_logic_tree_dependencies") as parser:
            with self.assertRaisesRegex(
                module.VerifiedSourceModelLogicTreeError,
                "byte count mismatch",
            ):
                module.extract_verified_source_model_dependencies(SYNTHETIC)
            parser.assert_not_called()

    def test_digest_mismatch_blocks_before_parser_without_observed_digest(self) -> None:
        payload = b"x" * module.EXPECTED_BYTE_COUNT
        observed = hashlib.sha256(payload).hexdigest()
        self.assertNotEqual(observed, module.EXPECTED_SHA256)
        with mock.patch.object(module, "extract_source_model_logic_tree_dependencies") as parser:
            with self.assertRaisesRegex(
                module.VerifiedSourceModelLogicTreeError,
                "SHA-256 mismatch",
            ) as caught:
                module.extract_verified_source_model_dependencies(payload)
            parser.assert_not_called()
        self.assertNotIn(observed, str(caught.exception))

    def test_non_utf8_verified_bytes_fail_after_identity_check(self) -> None:
        payload = b"\xff\xfe"
        inventory = inventory_with()
        with self.frozen_to(payload, inventory=inventory):
            with self.assertRaisesRegex(
                module.VerifiedSourceModelLogicTreeError,
                "not strict UTF-8",
            ):
                module.extract_verified_source_model_dependencies(payload)

    def test_parser_failure_does_not_echo_payload(self) -> None:
        payload = b"<not-the-provider-logic-tree>secret</not-the-provider-logic-tree>"
        inventory = inventory_with()
        with self.frozen_to(payload, inventory=inventory):
            with self.assertRaisesRegex(
                module.VerifiedSourceModelLogicTreeError,
                "dependency parse failed",
            ) as caught:
                module.extract_verified_source_model_dependencies(payload)
        self.assertNotIn("secret", str(caught.exception))

    def test_dependency_absent_from_frozen_inventory_fails_closed(self) -> None:
        absent = module.PREFIX + "source_models/absent.xml"
        payload = SYNTHETIC.replace(
            b"source_models/a.xml source_models/b.xml",
            b"source_models/absent.xml",
        )
        inventory = inventory_with()
        with self.frozen_to(payload, inventory=inventory):
            with self.assertRaisesRegex(
                module.VerifiedSourceModelLogicTreeError,
                "absent from frozen inventory",
            ) as caught:
                module.extract_verified_source_model_dependencies(payload)
        self.assertNotIn(absent, str(caught.exception))

    def test_frozen_receipt_identity_is_exact(self) -> None:
        self.assertEqual(module.EXPECTED_BYTE_COUNT, 17579)
        self.assertEqual(
            module.EXPECTED_SHA256,
            "97a37911f9eae73766f386686b112e5a4e111965da3e4e1543627c28d4201867",
        )
        self.assertEqual(module.SOURCE_ISSUE, 281)
        self.assertEqual(module.RECEIPT_ISSUE, 361)
        self.assertEqual(module.PROJECT_ID, 197)
        self.assertEqual(
            module.COMMIT_SHA,
            "fbd334de68f85d72669f73fc5a314a113db67317",
        )
        self.assertEqual(module.RECEIPT_RESULT_COMMENT_ID, 5301858821)
        self.assertEqual(module.RECEIPT_RUN_ID, 31880089623)
        self.assertEqual(
            module.RECEIPT_EXECUTION_SHA,
            "ab66e3e4c58c9b8f18587f1a8a51cf67cf9851b1",
        )
        self.assertEqual(module.INVENTORY_RECEIPT_COMMENT_ID, 5290449064)
        self.assertEqual(len(module.FROZEN_INVENTORY_PATHS), 62)
        self.assertIn(module.REPOSITORY_PATH, module.FROZEN_INVENTORY_PATHS)

    def test_regular_file_read_is_bounded_and_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.xml"
            target.write_bytes(SYNTHETIC)
            inventory = inventory_with(
                module.PREFIX + "source_models/a.xml",
                module.PREFIX + "source_models/b.xml",
            )
            with self.frozen_to(SYNTHETIC, inventory=inventory):
                self.assertEqual(module._read_regular_file(target), SYNTHETIC)
                link = root / "logic-tree.xml"
                link.symlink_to(target)
                with self.assertRaisesRegex(
                    module.VerifiedSourceModelLogicTreeError,
                    "non-symlink regular file",
                ):
                    module._read_regular_file(link)


if __name__ == "__main__":
    unittest.main()
