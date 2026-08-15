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
    from scripts import verify_eshm20_root_config_dependencies as module
except ModuleNotFoundError:
    import verify_eshm20_root_config_dependencies as module


SYNTHETIC = b"""[general]\nsite_model_file = sites.csv\n\n[logic]\nsource_model_logic_tree_file = source.xml\ngsim_logic_tree_file = gmpe.xml\n"""


class VerifiedEshm20RootConfigDependenciesTests(unittest.TestCase):
    def frozen_to(self, payload: bytes):
        return mock.patch.multiple(
            module,
            EXPECTED_BYTE_COUNT=len(payload),
            EXPECTED_SHA256=hashlib.sha256(payload).hexdigest(),
        )

    def test_verified_bytes_are_parsed_deterministically(self) -> None:
        with self.frozen_to(SYNTHETIC):
            result = module.extract_verified_root_dependencies(SYNTHETIC)
        self.assertEqual(result["byte_count"], len(SYNTHETIC))
        self.assertEqual(result["sha256"], hashlib.sha256(SYNTHETIC).hexdigest())
        self.assertEqual(
            [item["resolved_path"] for item in result["dependencies"]],
            [
                "oq_computational/oq_configuration_eshm20_v12e_region_main/gmpe.xml",
                "oq_computational/oq_configuration_eshm20_v12e_region_main/sites.csv",
                "oq_computational/oq_configuration_eshm20_v12e_region_main/source.xml",
            ],
        )
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertNotIn(SYNTHETIC.decode("utf-8"), json.dumps(result, sort_keys=True))

    def test_public_parser_bridge_has_no_receipt_identity_override(self) -> None:
        self.assertEqual(
            list(inspect.signature(module.extract_verified_root_dependencies).parameters),
            ["payload"],
        )

    def test_byte_count_mismatch_blocks_before_parser(self) -> None:
        with mock.patch.object(module, "extract_openquake_config_references") as parser:
            with self.assertRaisesRegex(module.VerifiedRootConfigError, "byte count mismatch"):
                module.extract_verified_root_dependencies(SYNTHETIC)
            parser.assert_not_called()

    def test_digest_mismatch_blocks_before_parser(self) -> None:
        payload = b"x" * module.EXPECTED_BYTE_COUNT
        self.assertNotEqual(hashlib.sha256(payload).hexdigest(), module.EXPECTED_SHA256)
        with mock.patch.object(module, "extract_openquake_config_references") as parser:
            with self.assertRaisesRegex(module.VerifiedRootConfigError, "SHA-256 mismatch"):
                module.extract_verified_root_dependencies(payload)
            parser.assert_not_called()

    def test_non_utf8_verified_bytes_fail_after_identity_check(self) -> None:
        payload = b"\xff\xfe"
        with self.frozen_to(payload):
            with self.assertRaisesRegex(module.VerifiedRootConfigError, "not strict UTF-8"):
                module.extract_verified_root_dependencies(payload)

    def test_parser_failure_is_rewrapped_without_payload(self) -> None:
        payload = b"[general]\nsite_model_file = ../../../../../../outside.csv\n"
        with self.frozen_to(payload):
            with self.assertRaisesRegex(
                module.VerifiedRootConfigError,
                "verified root dependency parse failed",
            ) as caught:
                module.extract_verified_root_dependencies(payload)
        self.assertNotIn(payload.decode("utf-8"), str(caught.exception))

    def test_frozen_receipt_identity_is_exact(self) -> None:
        self.assertEqual(module.EXPECTED_BYTE_COUNT, 2719)
        self.assertEqual(
            module.EXPECTED_SHA256,
            "f1f4dabc48e1b8a478dbdb96b01c8f58cc68c98abd6f9004671c5fba9eb7e714",
        )
        self.assertEqual(module.SOURCE_ISSUE, 281)
        self.assertEqual(module.PROJECT_ID, 197)
        self.assertEqual(
            module.COMMIT_SHA,
            "fbd334de68f85d72669f73fc5a314a113db67317",
        )

    def test_regular_file_read_is_bounded_and_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.ini"
            target.write_bytes(SYNTHETIC)
            with self.frozen_to(SYNTHETIC):
                self.assertEqual(module._read_regular_file(target), SYNTHETIC)
                link = root / "root.ini"
                link.symlink_to(target)
                with self.assertRaisesRegex(
                    module.VerifiedRootConfigError,
                    "non-symlink regular file",
                ):
                    module._read_regular_file(link)


if __name__ == "__main__":
    unittest.main()
