# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import unittest
from unittest import mock

from scripts import acquire_eshm20_gsim_resource_profile as worker


INVENTORY_RESOURCE = "eshm20_site_model_v06d.csv"
OUTSIDE_RESOURCE = "tables/example_coeffs.csv"


def gmm_xml(*, second_resource: bool = True) -> bytes:
    extra = (
        f"secondary_table = '{OUTSIDE_RESOURCE}'\nignored_file_extra = 'not-a-resource.csv'"
        if second_resource
        else "ignored_file_extra = 'not-a-resource.csv'"
    )
    return (
        "<nrml><logicTree>"
        "<logicTreeBranchSet branchSetID='bs2' uncertaintyType='gmpeModel'>"
        "<logicTreeBranch branchID='b2'><uncertaintyModel>"
        "[ExampleGsim]\n"
        f"coeff_file = '{INVENTORY_RESOURCE}'\n"
        f"{extra}"
        "</uncertaintyModel><uncertaintyWeight>0.4</uncertaintyWeight></logicTreeBranch>"
        "<logicTreeBranch branchID='b3'><uncertaintyModel>"
        "[OtherGsim]\n"
        f"coeff_file = '{INVENTORY_RESOURCE}'"
        "</uncertaintyModel><uncertaintyWeight>0.6</uncertaintyWeight></logicTreeBranch>"
        "</logicTreeBranchSet>"
        "</logicTree></nrml>"
    ).encode("utf-8")


class FakeResponse:
    def __init__(
        self,
        raw: bytes,
        url: str,
        *,
        final_url: str | None = None,
        status: int = 200,
    ) -> None:
        self.status = status
        self.headers = {"Content-Length": str(len(raw))}
        self._raw = raw
        self._offset = 0
        self._url = final_url or url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, amount: int = -1) -> bytes:
        if self._offset >= len(self._raw):
            return b""
        if amount < 0:
            amount = len(self._raw) - self._offset
        chunk = self._raw[self._offset : self._offset + amount]
        self._offset += len(chunk)
        return chunk


class Eshm20GsimResourceProfileTests(unittest.TestCase):
    def patched_identity(self, raw: bytes):
        return (
            mock.patch.object(worker, "EXPECTED_BYTE_COUNT", len(raw)),
            mock.patch.object(worker, "EXPECTED_SHA256", hashlib.sha256(raw).hexdigest()),
        )

    def opener_for(self, raw: bytes, captured: list[str]):
        def opener(request, timeout):
            self.assertGreater(timeout, 0)
            captured.append(request.full_url)
            return FakeResponse(raw, request.full_url)

        return opener

    def synthetic_result(self) -> dict[str, object]:
        raw = gmm_xml()
        return {
            "schema_version": worker.SCHEMA_VERSION,
            "source_issue": worker.SOURCE_ISSUE,
            "control_issue": worker.CONTROL_ISSUE,
            "dataset_id": worker.DATASET_ID,
            "project_id": worker.PROJECT_ID,
            "project_path": worker.PROJECT_PATH,
            "commit_sha": worker.COMMIT_SHA,
            "repository_path": worker.REPOSITORY_PATH,
            "byte_count": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "openquake_reference": worker.OPENQUAKE_REFERENCE,
            "inventory_receipt_comment_id": worker.INVENTORY_RECEIPT_COMMENT_ID,
            "root_dependency_result_comment_id": worker.ROOT_DEPENDENCY_RESULT_COMMENT_ID,
            "root_dependency_section": worker.ROOT_DEPENDENCY_SECTION,
            "root_dependency_option": worker.ROOT_DEPENDENCY_OPTION,
            "first_order_receipt_request_comment_id": worker.FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID,
            "first_order_receipt_result_comment_id": worker.FIRST_ORDER_RECEIPT_RESULT_COMMENT_ID,
            "first_order_receipt_run_id": worker.FIRST_ORDER_RECEIPT_RUN_ID,
            "first_order_receipt_execution_sha": worker.FIRST_ORDER_RECEIPT_EXECUTION_SHA,
            "first_order_receipt_retrieved_at": worker.FIRST_ORDER_RECEIPT_RETRIEVED_AT,
            "branch_set_count": 1,
            "branch_count": 2,
            "resource_reference_count": 0,
            "resources": [],
            "dependency_inventory_authorized": False,
            "dependency_receipt_authorized": False,
            "external_bytes_persisted": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        }

    def test_public_worker_has_no_target_or_semantic_selector(self) -> None:
        signature = inspect.signature(worker.acquire_eshm20_gsim_resource_profile)
        self.assertEqual(set(signature.parameters), {"opener", "monotonic"})
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            )
        )

    def test_exact_receipt_constants_are_frozen(self) -> None:
        self.assertEqual(worker.SOURCE_ISSUE, 281)
        self.assertEqual(worker.CONTROL_ISSUE, 374)
        self.assertEqual(worker.PROJECT_ID, 197)
        self.assertEqual(
            worker.COMMIT_SHA,
            "fbd334de68f85d72669f73fc5a314a113db67317",
        )
        self.assertTrue(worker.REPOSITORY_PATH.endswith("gmpe_complete_logic_tree_5br.xml"))
        self.assertEqual(worker.EXPECTED_BYTE_COUNT, 33760)
        self.assertEqual(
            worker.EXPECTED_SHA256,
            "e2c53f11174b8cd4de1f65af4dafc5af2e7a6848563e8a4c0ada44a54f22ff62",
        )
        self.assertEqual(worker.FIRST_ORDER_RECEIPT_RESULT_COMMENT_ID, 5301858821)
        self.assertEqual(worker.FIRST_ORDER_RECEIPT_RUN_ID, 31880089623)

    def test_receipt_identity_precedes_utf8_and_xml_inspection(self) -> None:
        raw = gmm_xml()
        count_patch, hash_patch = self.patched_identity(raw)
        with (
            count_patch,
            hash_patch,
            mock.patch.object(worker, "_parse_xml", wraps=worker._parse_xml) as parse,
        ):
            worker.extract_verified_gsim_resource_profile(raw)
            parse.assert_called_once()
            parse.reset_mock()
            tampered = raw[:-1] + bytes([raw[-1] ^ 1])
            with self.assertRaisesRegex(worker.Eshm20GsimResourceProfileError, "SHA-256"):
                worker.extract_verified_gsim_resource_profile(tampered)
            parse.assert_not_called()

        invalid_utf8 = b"\xff" + raw[1:]
        count_patch, hash_patch = self.patched_identity(invalid_utf8)
        with count_patch, hash_patch, mock.patch.object(worker, "_parse_xml") as parse:
            with self.assertRaisesRegex(worker.Eshm20GsimResourceProfileError, "strict UTF-8"):
                worker.extract_verified_gsim_resource_profile(invalid_utf8)
            parse.assert_not_called()

    def test_file_and_table_resources_are_grouped_with_sorted_origins(self) -> None:
        raw = gmm_xml()
        count_patch, hash_patch = self.patched_identity(raw)
        with count_patch, hash_patch:
            result = worker.extract_verified_gsim_resource_profile(raw)

        self.assertEqual(result["branch_set_count"], 1)
        self.assertEqual(result["branch_count"], 2)
        self.assertEqual(result["resource_reference_count"], 2)
        resources = result["resources"]
        by_key = {item["argument_key"]: item for item in resources}
        coeff = by_key["coeff_file"]
        self.assertEqual(coeff["relative_path"], INVENTORY_RESOURCE)
        self.assertTrue(coeff["selected_prefix_inventory_member"])
        self.assertFalse(coeff["comment_prefixed"])
        self.assertEqual(
            coeff["origins"],
            [
                {"branch_set_id": "bs2", "branch_id": "b2"},
                {"branch_set_id": "bs2", "branch_id": "b3"},
            ],
        )
        table = by_key["secondary_table"]
        self.assertEqual(table["relative_path"], OUTSIDE_RESOURCE)
        self.assertFalse(table["selected_prefix_inventory_member"])
        self.assertFalse(table["comment_prefixed"])
        self.assertFalse(any(item["argument_key"] == "ignored_file_extra" for item in resources))

    def test_similar_suffixes_are_ignored_but_exact_suffixes_are_detected(self) -> None:
        self.assertEqual(worker._resource_assignments("thing_file_extra = 'a.csv'"), ())
        self.assertEqual(
            worker._resource_assignments("thing_file = 'a.csv'\nthing_table = 'b.csv'"),
            (("thing_file", "a.csv", False), ("thing_table", "b.csv", False)),
        )

    def test_openquake_314_comment_prefixed_resource_quirk_is_preserved(self) -> None:
        self.assertEqual(
            worker._resource_assignments("# coeff_file = 'commented.csv'"),
            (("coeff_file", "commented.csv", True),),
        )
        raw = (
            "<nrml><logicTree>"
            "<logicTreeBranchSet branchSetID='bs1' uncertaintyType='gmpeModel'>"
            "<logicTreeBranch branchID='b1'><uncertaintyModel>"
            "# coeff_file = 'commented.csv'"
            "</uncertaintyModel></logicTreeBranch>"
            "</logicTreeBranchSet></logicTree></nrml>"
        ).encode()
        count_patch, hash_patch = self.patched_identity(raw)
        with count_patch, hash_patch:
            result = worker.extract_verified_gsim_resource_profile(raw)
        self.assertEqual(result["resource_reference_count"], 1)
        self.assertEqual(result["resources"][0]["argument_key"], "coeff_file")
        self.assertTrue(result["resources"][0]["comment_prefixed"])

    def test_multiple_comment_markers_fail_closed_instead_of_silent_underreporting(self) -> None:
        with self.assertRaisesRegex(worker.Eshm20GsimResourceProfileError, "argument name"):
            worker._resource_assignments("## coeff_file = 'commented.csv'")

    def test_nonliteral_or_ambiguous_resource_assignment_fails_closed(self) -> None:
        for model_text in (
            "coeff_file = some_variable",
            "coeff_file = 'a=b.csv'",
            "coeff_file = 123",
        ):
            with self.subTest(model_text=model_text):
                with self.assertRaises(worker.Eshm20GsimResourceProfileError):
                    worker._resource_assignments(model_text)

    def test_unsafe_or_noncanonical_resource_paths_fail_closed(self) -> None:
        for path in (
            "/tmp/a.csv",
            "https://example.test/a.csv",
            "C:\\tmp\\a.csv",
            "../a.csv",
            "tables/../a.csv",
            "tables//a.csv",
            "tables/./a.csv",
            "a.csv?token=x",
            "a.csv#fragment",
            "a\x00.csv",
        ):
            with self.subTest(path=path):
                with self.assertRaises(worker.Eshm20GsimResourceProfileError):
                    worker._canonical_relative_resource(path)

    def test_dtd_entity_nul_and_malformed_xml_fail_closed(self) -> None:
        raws = (
            b"<!DOCTYPE nrml><nrml/>",
            b"<!ENTITY x 'y'><nrml/>",
            b"<nrml>\x00</nrml>",
            b"<nrml>",
        )
        for raw in raws:
            count_patch, hash_patch = self.patched_identity(raw)
            with self.subTest(raw=raw), count_patch, hash_patch:
                with self.assertRaises(worker.Eshm20GsimResourceProfileError):
                    worker.extract_verified_gsim_resource_profile(raw)

    def test_non_gmpe_branchset_and_duplicate_ids_fail_closed(self) -> None:
        wrong_type = (
            b"<nrml><logicTree><logicTreeBranchSet branchSetID='bs1' uncertaintyType='sourceModel'>"
            b"<logicTreeBranch branchID='b1'><uncertaintyModel>x</uncertaintyModel></logicTreeBranch>"
            b"</logicTreeBranchSet></logicTree></nrml>"
        )
        duplicate_branch = (
            b"<nrml><logicTree><logicTreeBranchSet branchSetID='bs1' uncertaintyType='gmpeModel'>"
            b"<logicTreeBranch branchID='b1'><uncertaintyModel>x</uncertaintyModel></logicTreeBranch>"
            b"<logicTreeBranch branchID='b1'><uncertaintyModel>y</uncertaintyModel></logicTreeBranch>"
            b"</logicTreeBranchSet></logicTree></nrml>"
        )
        for raw in (wrong_type, duplicate_branch):
            count_patch, hash_patch = self.patched_identity(raw)
            with self.subTest(raw=raw), count_patch, hash_patch:
                with self.assertRaises(worker.Eshm20GsimResourceProfileError):
                    worker.extract_verified_gsim_resource_profile(raw)

    def test_branch_identifiers_must_be_trimmed_and_control_free(self) -> None:
        cases = (
            ("", "b1"),
            ("   ", "b1"),
            (" bs1", "b1"),
            ("bs1 ", "b1"),
            ("bs&#10;1", "b1"),
            ("bs&#x7F;1", "b1"),
            ("bs1", ""),
            ("bs1", "   "),
            ("bs1", " b1"),
            ("bs1", "b1 "),
            ("bs1", "b&#10;1"),
            ("bs1", "b&#x7F;1"),
        )
        for branch_set_id, branch_id in cases:
            raw = (
                "<nrml><logicTree>"
                f"<logicTreeBranchSet branchSetID='{branch_set_id}' uncertaintyType='gmpeModel'>"
                f"<logicTreeBranch branchID='{branch_id}'><uncertaintyModel>"
                "coeff_file = 'a.csv'"
                "</uncertaintyModel></logicTreeBranch>"
                "</logicTreeBranchSet></logicTree></nrml>"
            ).encode("utf-8")
            count_patch, hash_patch = self.patched_identity(raw)
            with self.subTest(branch_set_id=branch_set_id, branch_id=branch_id), count_patch, hash_patch:
                with self.assertRaises(worker.Eshm20GsimResourceProfileError):
                    worker.extract_verified_gsim_resource_profile(raw)

    def test_worker_uses_fixed_provider_target(self) -> None:
        raw = gmm_xml()
        captured: list[str] = []
        with mock.patch.object(
            worker,
            "extract_verified_gsim_resource_profile",
            return_value=self.synthetic_result(),
        ) as profile:
            result = worker.acquire_eshm20_gsim_resource_profile(
                opener=self.opener_for(raw, captured)
            )
        self.assertEqual(len(captured), 1)
        self.assertIn(f"/api/v4/projects/{worker.PROJECT_ID}/", captured[0])
        self.assertIn(worker.COMMIT_SHA, captured[0])
        self.assertIn("gmpe_complete_logic_tree_5br.xml", result["repository_path"])
        profile.assert_called_once_with(raw)

    def test_response_identity_status_and_oversize_fail_before_profile(self) -> None:
        raw = gmm_xml()

        def wrong_url(request, timeout):
            return FakeResponse(
                raw,
                request.full_url,
                final_url="https://gitlab.seismo.ethz.ch/unexpected",
            )

        def wrong_status(request, timeout):
            return FakeResponse(raw, request.full_url, status=206)

        oversize = b"x" * (worker.EXPECTED_BYTE_COUNT + 1)
        for opener in (wrong_url, wrong_status, self.opener_for(oversize, [])):
            with self.subTest(opener=opener):
                with mock.patch.object(worker, "extract_verified_gsim_resource_profile") as profile:
                    with self.assertRaises(worker.Eshm20GsimResourceProfileError):
                        worker.acquire_eshm20_gsim_resource_profile(opener=opener)
                profile.assert_not_called()

    def test_transport_and_xml_failures_do_not_leak_payload_text(self) -> None:
        def opener(request, timeout):
            raise OSError("PROVIDER_SECRET_BODY")

        with self.assertRaises(worker.Eshm20GsimResourceProfileError) as caught:
            worker.acquire_eshm20_gsim_resource_profile(opener=opener)
        self.assertNotIn("PROVIDER_SECRET_BODY", str(caught.exception))
        self.assertIn("OSError", str(caught.exception))

        raw = b"<nrml>PROVIDER_PRIVATE_BODY"
        count_patch, hash_patch = self.patched_identity(raw)
        with count_patch, hash_patch:
            with self.assertRaises(worker.Eshm20GsimResourceProfileError) as caught:
                worker.extract_verified_gsim_resource_profile(raw)
        self.assertNotIn("PROVIDER_PRIVATE_BODY", str(caught.exception))

    def test_authority_ceilings_cannot_be_widened_and_payload_is_not_returned(self) -> None:
        raw = b"PROVIDER_PRIVATE_BODY"
        result = self.synthetic_result()
        with mock.patch.object(
            worker, "extract_verified_gsim_resource_profile", return_value=result
        ):
            observed = worker.acquire_eshm20_gsim_resource_profile(
                opener=self.opener_for(raw, [])
            )
        self.assertNotIn("PROVIDER_PRIVATE_BODY", repr(observed))

        keys = (
            "dependency_inventory_authorized",
            "dependency_receipt_authorized",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        )
        for key in keys:
            widened = self.synthetic_result()
            widened[key] = True
            with mock.patch.object(
                worker, "extract_verified_gsim_resource_profile", return_value=widened
            ):
                with self.assertRaisesRegex(worker.Eshm20GsimResourceProfileError, "widened"):
                    worker.acquire_eshm20_gsim_resource_profile(
                        opener=self.opener_for(gmm_xml(), [])
                    )


if __name__ == "__main__":
    unittest.main()
