# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from scripts import project_existing_oq313_datastore as subject
from scripts import project_oq313_risk_by_event_receipt as numerical_contract


def _receipt(row_count: int = 1) -> tuple[bytes, dict[str, Any]]:
    rows = [
        {
            "event_id": index + 1,
            "rup_id": index + 10_001,
            "rlz_id": index % 2,
            "loss_f32_be_hex": "3f800000",
            "variance_f32_be_hex": "00000000",
        }
        for index in range(row_count)
    ]
    return numerical_contract.project_oq313_risk_by_event_receipt(
        rows,
        portfolio_agg_id=7,
        structural_loss_id=0,
        concurrent_tasks=0,
    )


class ExistingOQ313DatastoreProjectionTests(unittest.TestCase):
    def test_small_receipt_binds_datastore_and_embeds_validated_document(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            datastore = Path(temporary) / "calc_1.hdf5"
            datastore.write_bytes(b"completed-datastore")
            payload, identity = _receipt()

            def projector(path: Path) -> tuple[bytes, dict[str, Any]]:
                self.assertEqual(path, datastore)
                return payload, identity

            result = subject.project_existing_datastore(
                datastore,
                project_datastore=projector,
            )

        self.assertEqual(result["projection_mode"], "full_receipt")
        self.assertEqual(
            result["datastore"],
            {
                "filename": "calc_1.hdf5",
                "byte_count": len(b"completed-datastore"),
                "sha256": hashlib.sha256(b"completed-datastore").hexdigest(),
            },
        )
        self.assertEqual(result["numerical_receipt_identity"], identity)
        self.assertEqual(
            result["numerical_receipt"]["schema_version"],
            numerical_contract.SCHEMA_VERSION,
        )
        self.assertIs(result["full_receipt_written"], False)
        self.assertIs(result["historical_reproduction_verified"], False)
        self.assertIs(result["scientific_validity_verified"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)

    def test_oversized_receipt_uses_bounded_commitment_without_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            datastore = Path(temporary) / "calc_9.hdf5"
            datastore.write_bytes(b"completed-datastore")
            payload, identity = _receipt(row_count=1_000)
            self.assertGreater(
                len(payload),
                subject.action.MAX_PUBLIC_NUMERICAL_RECEIPT_BYTES,
            )
            result = subject.project_existing_datastore(
                datastore,
                project_datastore=lambda path: (payload, identity),
            )

        self.assertEqual(result["projection_mode"], "commitment")
        self.assertNotIn("numerical_receipt", result)
        self.assertEqual(
            result["numerical_receipt_commitment"]["row_count"],
            1_000,
        )
        self.assertIs(
            result["numerical_receipt_commitment"]["full_receipt_published"],
            False,
        )
        self.assertNotIn('"rows"', json.dumps(result, sort_keys=True))

    def test_optional_full_receipt_is_written_exactly_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            datastore = root / "calc_2.hdf5"
            datastore.write_bytes(b"completed-datastore")
            output = root / "run" / "risk_by_event.receipt.json"
            payload, identity = _receipt()
            result = subject.project_existing_datastore(
                datastore,
                full_receipt_out=output,
                project_datastore=lambda path: (payload, identity),
            )
            self.assertEqual(output.read_bytes(), payload)
            self.assertIs(result["full_receipt_written"], True)
            with self.assertRaises(subject.ExistingOQ313DatastoreProjectionError):
                subject.project_existing_datastore(
                    datastore,
                    full_receipt_out=output,
                    project_datastore=lambda path: (payload, identity),
                )

    def test_rejects_wrong_datastore_filename_before_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            datastore = Path(temporary) / "old-run.hdf5"
            datastore.write_bytes(b"completed-datastore")
            called = False

            def projector(path: Path) -> tuple[bytes, dict[str, Any]]:
                nonlocal called
                called = True
                return _receipt()

            with self.assertRaises(subject.ExistingOQ313DatastoreProjectionError):
                subject.project_existing_datastore(
                    datastore,
                    project_datastore=projector,
                )
            self.assertIs(called, False)

    def test_rejects_datastore_mutation_during_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            datastore = Path(temporary) / "calc_3.hdf5"
            datastore.write_bytes(b"completed-datastore")
            payload, identity = _receipt()

            def projector(path: Path) -> tuple[bytes, dict[str, Any]]:
                path.write_bytes(b"mutated-datastore-with-different-size")
                return payload, identity

            with self.assertRaisesRegex(
                subject.ExistingOQ313DatastoreProjectionError,
                "changed while numerical receipt was projected",
            ):
                subject.project_existing_datastore(
                    datastore,
                    project_datastore=projector,
                )

    def test_rejects_projected_digest_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            datastore = Path(temporary) / "calc_4.hdf5"
            datastore.write_bytes(b"completed-datastore")
            payload, identity = _receipt()
            bad_identity = dict(identity)
            bad_identity["sha256"] = "0" * 64
            with self.assertRaisesRegex(
                subject.ExistingOQ313DatastoreProjectionError,
                "failed current validation",
            ):
                subject.project_existing_datastore(
                    datastore,
                    project_datastore=lambda path: (payload, bad_identity),
                )


if __name__ == "__main__":
    unittest.main()
