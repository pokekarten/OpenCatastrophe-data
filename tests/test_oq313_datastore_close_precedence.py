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


class OQ313DatastoreClosePrecedenceTests(unittest.TestCase):
    def test_selection_failure_remains_primary_when_close_also_fails(self) -> None:
        class FakeDatastore:
            def __getitem__(self, key: str) -> object:
                if key != "oqparam":
                    raise KeyError(key)
                return object()

            def close(self) -> None:
                raise RuntimeError("injected cleanup detail")

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

        captured: list[subject.KosovoResidentialOQ313ActionError] = []

        def project_datastore(path: Path) -> tuple[bytes, dict[str, Any]]:
            try:
                return subject._project_exact_datastore(path)
            except subject.KosovoResidentialOQ313ActionError as exc:
                captured.append(exc)
                raise

        with (
            mock.patch.object(subject, "run_action", side_effect=native_pass),
            mock.patch.object(
                subject.datastore_selector,
                "select_oq313_risk_by_event_receipt",
                side_effect=subject.datastore_selector.OQ313DatastoreSelectionError(
                    "injected selector detail"
                ),
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
                project_datastore=project_datastore,
            )

        self.assertEqual(len(captured), 1)
        self.assertEqual(
            str(captured[0]),
            "completed OpenQuake datastore failed numerical receipt selection",
        )
        self.assertIsInstance(
            captured[0].__cause__,
            subject.datastore_selector.OQ313DatastoreSelectionError,
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
        rendered = json.dumps(result)
        self.assertNotIn("injected selector detail", rendered)
        self.assertNotIn("injected cleanup detail", rendered)


if __name__ == "__main__":
    unittest.main()
