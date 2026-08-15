# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
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
    def expected(self) -> tuple[int, str]:
        return len(SYNTHETIC), hashlib.sha256(SYNTHETIC).hexdigest()

    def test_verified_bytes_are_parsed_deterministically(self) -> None:
        byte_count, sha256 = self.expected()
        result = module.extract_verified_root_dependencies(
            SYNTHETIC,
            expected_byte_count=byte_count,
            expected_sha256=sha256,
        )
        self.assertEqual(result["byte_count"], byte_count)
        self.assertEqual(result["sha256"], sha256)
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
        encoded = json.dumps(result, sort_keys=True)
        self.assertNotIn(SYNTHETIC.decode("utf-8"), encoded)

    def test_byte_count_mismatch_blocks_before_parser(self) -> None:
        _, sha256 = self.expected()
        with mock.patch.object(module, "extract_openquake_config_references") as parser:
            with self.assertRaisesRegex(module.VerifiedRootConfigError, "byte count mismatch"):
                module.extract_verified_root_dependencies(
                    SYNTHETIC,
                    expected_byte_count=len(SYNTHETIC) + 1,
                    expected_sha256=sha256,
                )
            parser.assert_not_called()

    def test_digest_mismatch_blocks_before_parser(self) -> None:
        byte_count, _ = self.expected()
        with mock.patch.object(module, "extract_openquake_config_references") as parser:
            with self.assertRaisesRegex(module.VerifiedRootConfigError, "SHA-256 mismatch"):
                module.extract_verified_root_dependencies(
                    SYNTHETIC,
                    expected_byte_count=byte_count,
                    expected_sha256="0" * 64,
                )
            parser.assert_not_called()

    def test_non_utf8_verified_bytes_fail_after_identity_check(self) -> None:
        payload = b"\xff\xfe"
        with self.assertRaisesRegex(module.VerifiedRootConfigError, "not strict UTF-8"):
            module.extract_verified_root_dependencies(
                payload,
                expected_byte_count=len(payload),
                expected_sha256=hashlib.sha256(payload).hexdigest(),
            )

    def test_parser_failure_is_rewrapped_without_payload(self) -> None:
        payload = b"[general]\nsite_model_file = ../../../../../../outside.csv\n"
        with self.assertRaisesRegex(
            module.VerifiedRootConfigError,
            "verified root dependency parse failed",
        ) as caught:
            module.extract_verified_root_dependencies(
                payload,
                expected_byte_count=len(payload),
                expected_sha256=hashlib.sha256(payload).hexdigest(),
            )
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

    def test_cli_rejects_symlink_without_reading_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.ini"
            target.write_bytes(b"x" * module.EXPECTED_BYTE_COUNT)
            link = root / "root.ini"
            link.symlink_to(target)
            with self.assertRaisesRegex(module.VerifiedRootConfigError, "non-symlink regular file"):
                module._read_regular_file(link)


if __name__ == "__main__":
    unittest.main()
