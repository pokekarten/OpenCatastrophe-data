# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from unittest import mock

from scripts import run_esrm20_event_hazard_group1_imt_profile_action as action

EXECUTION_SHA = "b" * 40


class Group1ImtProfileTerminalSizeTests(unittest.TestCase):
    def _assert_rejected_before_json(self, body: str, message: str) -> None:
        with mock.patch.object(
            action.json,
            "loads",
            side_effect=AssertionError("JSON parser must not receive unbounded terminal text"),
        ) as loads:
            with self.assertRaisesRegex(action.Group1ImtProfileActionError, message):
                action._parse_trusted_terminal_result(body, execution_sha=EXECUTION_SHA)
            loads.assert_not_called()

    def test_oversized_multibyte_terminal_is_rejected_before_json_parse(self) -> None:
        multibyte = "é"
        payload = multibyte * (
            action.MAX_RESULT_UTF8_BYTES // len(multibyte.encode("utf-8")) + 1
        )
        self.assertGreater(len(payload.encode("utf-8")), action.MAX_RESULT_UTF8_BYTES)
        body = action.RESULT_MARKER + "\n" + payload

        self._assert_rejected_before_json(body, "exceeds publication limit")

    def test_non_utf8_encodable_terminal_is_rejected_before_json_parse(self) -> None:
        body = action.RESULT_MARKER + "\n" + chr(0xD800)

        self._assert_rejected_before_json(body, "not valid UTF-8")


if __name__ == "__main__":
    unittest.main()
