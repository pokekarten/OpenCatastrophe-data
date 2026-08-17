# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from scripts import run_esrm20_kosovo_site_openquake_runtime as subject

EXECUTION_SHA = "1" * 40
OTHER_SHA = "2" * 40
IMAGE_DIGEST = "sha256:" + "a" * 64


def request_body(*, sha: str = EXECUTION_SHA) -> str:
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.CONTROL_ISSUE,
        "target_sha": sha,
        "dataset_id": subject.DATASET_ID,
        "requester": "unit-test",
    }
    return subject.REQUEST_MARKER + "\n" + json.dumps(payload, sort_keys=True, separators=(",", ":"))


def runtime_payload() -> dict[str, object]:
    return {
        "openquake_reference": {"tag": subject.OPENQUAKE_TAG, "commit": subject.OPENQUAKE_COMMIT},
        "runtime_image_digest": IMAGE_DIGEST,
        "parser_path": "openquake.commonlib.readinput.get_site_model",
        "site_count": subject.EXPECTED_SITE_COUNT,
        "required_site_parameter_names": list(subject.EXPECTED_REQUIRED_PARAMETERS),
        "runtime_value_accept_count": subject.EXPECTED_SITE_COUNT,
        "raw_xml_returned": False,
        "raw_site_rows_returned": False,
        "raw_attribute_values_returned": False,
        "coordinates_returned": False,
        "openquake_runtime_value_acceptance_verified": True,
        "gsim_site_parameter_sufficiency_verified": True,
        "site_parameter_units_verified": False,
        "crs_coordinate_semantics_verified": False,
        "missingness_semantics_verified": False,
        "site_model_compatibility_verified": False,
        "site_adjusted_reference_authorized": False,
        "numerical_hazard_agreement_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class _FakeSiteModel:
    def __init__(self, count: int = subject.EXPECTED_SITE_COUNT, names: tuple[str, ...] | None = None):
        self._count = count
        self.dtype = SimpleNamespace(
            names=names
            or (
                "lon",
                "lat",
                "geology",
                "region",
                "slope",
                "vs30",
                "xvf",
            )
        )

    def __len__(self) -> int:
        return self._count


class _FakeReadInput:
    def __init__(self, *, required: set[str] | None = None, site_model: _FakeSiteModel | None = None):
        self.required = required or set(subject.EXPECTED_REQUIRED_PARAMETERS)
        self.site_model = site_model or _FakeSiteModel()
        self.seen_inputs: dict[str, object] | None = None

    def get_gsim_lt(self, oqparam: object) -> object:
        self.seen_inputs = dict(oqparam.inputs)
        return SimpleNamespace(req_site_params=set(self.required))

    def get_site_model(self, oqparam: object) -> _FakeSiteModel:
        assert self.seen_inputs is not None
        assert oqparam.inputs == self.seen_inputs
        return self.site_model


class SiteOpenQuakeRuntimeTests(unittest.TestCase):
    def test_validate_request_accepts_exact_envelope(self) -> None:
        request = subject.validate_request(
            request_body(),
            expected_issue=subject.CONTROL_ISSUE,
            execution_sha=EXECUTION_SHA,
        )
        self.assertEqual(request["target_sha"], EXECUTION_SHA)

    def test_validate_request_rejects_wrong_sha_and_duplicate_key(self) -> None:
        with self.assertRaisesRegex(subject.SiteOpenQuakeRuntimeError, "target_sha drifted"):
            subject.validate_request(
                request_body(sha=OTHER_SHA),
                expected_issue=subject.CONTROL_ISSUE,
                execution_sha=EXECUTION_SHA,
            )
        duplicate = (
            subject.REQUEST_MARKER
            + '\n{"schema_version":"%s","action":"%s","issue":291,'
            '"target_sha":"%s","dataset_id":"%s","requester":"x","requester":"y"}'
            % (subject.REQUEST_SCHEMA_VERSION, subject.ACTION, EXECUTION_SHA, subject.DATASET_ID)
        )
        with self.assertRaisesRegex(subject.SiteOpenQuakeRuntimeError, "duplicate JSON key"):
            subject.validate_request(
                duplicate,
                expected_issue=subject.CONTROL_ISSUE,
                execution_sha=EXECUTION_SHA,
            )

    def test_openquake_ingest_uses_real_api_shape_without_returning_values(self) -> None:
        fake = _FakeReadInput()
        result = subject._openquake_ingest(
            site_bytes=b"<siteModel/>",
            gmm_bytes=b"<logicTree/>",
            image_digest=IMAGE_DIGEST,
            readinput_module=fake,
        )
        self.assertEqual(result["site_count"], subject.EXPECTED_SITE_COUNT)
        self.assertEqual(result["required_site_parameter_names"], list(subject.EXPECTED_REQUIRED_PARAMETERS))
        self.assertTrue(result["openquake_runtime_value_acceptance_verified"])
        self.assertTrue(result["gsim_site_parameter_sufficiency_verified"])
        self.assertFalse(result["raw_xml_returned"])
        self.assertFalse(result["coordinates_returned"])

    def test_openquake_ingest_rejects_required_parameter_drift(self) -> None:
        fake = _FakeReadInput(required={"vs30"})
        with self.assertRaisesRegex(subject.SiteRuntimeIngestionError, "required-site parameter set drifted"):
            subject._openquake_ingest(
                site_bytes=b"x",
                gmm_bytes=b"y",
                image_digest=IMAGE_DIGEST,
                readinput_module=fake,
            )

    def test_openquake_ingest_rejects_missing_parsed_field(self) -> None:
        fake = _FakeReadInput(site_model=_FakeSiteModel(names=("lon", "lat", "vs30")))
        with self.assertRaisesRegex(subject.SiteRuntimeIngestionError, "parsed fields are insufficient"):
            subject._openquake_ingest(
                site_bytes=b"x",
                gmm_bytes=b"y",
                image_digest=IMAGE_DIGEST,
                readinput_module=fake,
            )

    def test_terminal_payload_preserves_scientific_ceilings(self) -> None:
        payload = runtime_payload()
        self.assertIs(subject._validate_runtime_payload(payload), payload)
        for field in (
            "crs_coordinate_semantics_verified",
            "missingness_semantics_verified",
            "site_model_compatibility_verified",
            "site_adjusted_reference_authorized",
            "numerical_hazard_agreement_verified",
            "publication_authorized",
            "model_use_authorized",
        ):
            mutated = dict(payload)
            mutated[field] = True
            with self.subTest(field=field):
                with self.assertRaises(subject.SiteOpenQuakeRuntimeError):
                    subject._validate_runtime_payload(mutated)

    def test_run_runtime_pass_is_bounded(self) -> None:
        result = subject._run_runtime(
            execution_sha=EXECUTION_SHA,
            image_digest=IMAGE_DIGEST,
            site_acquirer=lambda: b"site",
            gmm_acquirer=lambda: b"gmm",
            runtime_ingester=lambda **_: runtime_payload(),
        )
        self.assertEqual(result["status"], "pass")
        self.assertIsNone(result["failure_class"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["model_use_authorized"])

    def test_run_runtime_blocks_acquisition_and_runtime_failures(self) -> None:
        def fail_site() -> bytes:
            raise subject.SiteRuntimeAcquisitionError("site")

        site_block = subject._run_runtime(
            execution_sha=EXECUTION_SHA,
            image_digest=IMAGE_DIGEST,
            site_acquirer=fail_site,
            gmm_acquirer=lambda: b"gmm",
            runtime_ingester=lambda **_: runtime_payload(),
        )
        self.assertEqual(site_block["status"], "blocked")
        self.assertEqual(site_block["failure_class"], "site_acquisition_failure")
        self.assertIsNone(site_block["runtime"])

        def fail_runtime(**_: object) -> dict[str, object]:
            raise subject.SiteRuntimeIngestionError("runtime")

        runtime_block = subject._run_runtime(
            execution_sha=EXECUTION_SHA,
            image_digest=IMAGE_DIGEST,
            site_acquirer=lambda: b"site",
            gmm_acquirer=lambda: b"gmm",
            runtime_ingester=fail_runtime,
        )
        self.assertEqual(runtime_block["status"], "blocked")
        self.assertEqual(runtime_block["failure_class"], "runtime_ingestion_failure")
        self.assertIsNone(runtime_block["runtime"])

    def test_historical_terminal_result_only_dedups_same_execution_sha(self) -> None:
        result = subject._base_result(execution_sha=EXECUTION_SHA)
        result.update({"status": "pass", "failure_class": None, "runtime": runtime_payload()})
        body = subject.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":"))
        self.assertTrue(subject._parse_trusted_terminal_result(body, execution_sha=EXECUTION_SHA))
        self.assertFalse(subject._parse_trusted_terminal_result(body, execution_sha=OTHER_SHA))


if __name__ == "__main__":
    unittest.main()
