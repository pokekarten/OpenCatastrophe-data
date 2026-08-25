# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from unittest import mock

from scripts import run_esrm20_kosovo_mapping_join_action as subject


EXECUTION_SHA = "7" * 40


class MappingJoinTerminalSizeTests(unittest.TestCase):
    def test_oversized_multibyte_terminal_fails_before_json_parse(self) -> None:
        payload = "é" * ((subject.MAX_RESULT_UTF8_BYTES // 2) + 1)
        self.assertLess(len(payload), subject.MAX_RESULT_UTF8_BYTES)
        self.assertGreater(len(payload.encode("utf-8")), subject.MAX_RESULT_UTF8_BYTES)
        body = subject.RESULT_MARKER + "\n" + payload

        with mock.patch.object(
            subject.json,
            "loads",
            side_effect=AssertionError("oversized trusted terminal reached JSON parser"),
        ) as loads:
            with self.assertRaisesRegex(
                subject.KosovoMappingJoinExecutionError,
                "publication limit",
            ):
                subject._parse_terminal_result(body, execution_sha=EXECUTION_SHA)

        loads.assert_not_called()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
