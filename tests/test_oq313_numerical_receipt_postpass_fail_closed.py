# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import os
import sys
import types
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313_action as subject

EXECUTION_SHA = "a" * 40


class OQ313NumericalReceiptPostPassFailClosedTests(unittest.TestCase):
    def test_pass_terminalizes_datastore_discovery_io_failure(self) -> None:
        original_iterdir = Path.iterdir
        calls = 0

        def flaky_iterdir(path: Path):
            nonlocal calls
            calls += 1
            if calls == 1:
                return original_iterdir(path)
            raise PermissionError("sensitive datastore discovery detail")

        def native_pass(*args: Any, **kwargs: Any) -> dict[str, object]:
            del args, kwargs
            datadir = Path(os.environ[subject.OQ_DATADIR_ENV])
            (datadir / "calc_1.hdf5").write_bytes(b"fixture")
            return {"status": "pass"}

        with (
            mock.patch.object(subject, "run_action", side_effect=native_pass),
            mock.patch.object(Path, "iterdir", autospec=True, side_effect=flaky_iterdir),
        ):
            result = subject.run_action_with_numerical_receipt(
                execution_sha=EXECUTION_SHA,
                source_group1_config=b"source",
                runtime_identity={},
                resolved_runtime={},
            )

        self.assertEqual(result["status"], "blocked")
        self.assertIs(result["numerical_receipt_emitted"], False)
        self.assertEqual(
            result["numerical_receipt_failure_stage"],
            "risk_by_event_receipt",
        )
        self.assertEqual(
            result["numerical_receipt_failure_code"],
            "calculation_datastore_discovery_failed",
        )
        self.assertNotIn("sensitive datastore discovery detail", json.dumps(result))

    def test_pass_terminalizes_datastore_close_failure(self) -> None:
        class FakeDatastore:
            def __getitem__(self, key: str) -> object:
                if key != "oqparam":
                    raise KeyError(key)
                return object()

            def close(self) -> None:
                raise RuntimeError("sensitive hdf5 close detail")

        def read_datastore(path: str, mode: str = "r") -> FakeDatastore:
            del path, mode
            return FakeDatastore()

        oq_datastore = types.ModuleType("openquake.commonlib.datastore")
        oq_datastore.read = read_datastore  # type: ignore[attr-defined]
        commonlib = types.ModuleType("openquake.commonlib")
        commonlib.datastore = oq_datastore  # type: ignore[attr-defined]
        openquake = types.ModuleType("openquake")
        openquake.commonlib = commonlib  # type: ignore[attr-defined]

        def native_pass(*args: Any, **kwargs: Any) -> dict[str, object]:
            del args, kwargs
            datadir = Path(os.environ[subject.OQ_DATADIR_ENV])
            (datadir / "calc_1.hdf5").write_bytes(b"fixture")
            return {"status": "pass"}

        with (
            mock.patch.object(subject, "run_action", side_effect=native_pass),
            mock.patch.object(
                subject.datastore_selector,
                "select_oq313_risk_by_event_receipt",
                return_value=(b"unused", {}),
            ),
            mock.patch.dict(
                sys.modules,
                {
                    "openquake": openquake,
                    "openquake.commonlib": commonlib,
                    "openquake.commonlib.datastore": oq_datastore,
                },
            ),
        ):
            result = subject.run_action_with_numerical_receipt(
                execution_sha=EXECUTION_SHA,
                source_group1_config=b"source",
                runtime_identity={},
                resolved_runtime={},
                project_datastore=subject._project_exact_datastore,
            )

        self.assertEqual(result["status"], "blocked")
        self.assertIs(result["numerical_receipt_emitted"], False)
        self.assertEqual(
            result["numerical_receipt_failure_stage"],
            "risk_by_event_receipt",
        )
        self.assertEqual(
            result["numerical_receipt_failure_code"],
            "risk_by_event_selection_failed",
        )
        self.assertNotIn("sensitive hdf5 close detail", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
