# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import unittest
from unittest import mock

from scripts import acquire_eshm20_source_model_dependencies as worker


SOURCE_PATH = (
    "oq_computational/oq_configuration_eshm20_v12e_region_main/"
    "source_models/fsm_v09/fs_ver09e_model_aGR_SRA_MA_fMthr.xml"
)
OTHER_SOURCE_PATH = (
    "oq_computational/oq_configuration_eshm20_v12e_region_main/"
    "source_models/interface_v12b/CaA_IF2222222_M40.xml"
)
RAW = (
    b"<nrml><logicTree><logicTreeBranchSet uncertaintyType=\"sourceModel\">"
    b"<logicTreeBranch branchID=\"b1\"><uncertaintyModel>"
    b"source_models/fsm_v09/fs_ver09e_model_aGR_SRA_MA_fMthr.xml"
    b"</uncertaintyModel></logicTreeBranch></logicTreeBranchSet>"
    b"</logicTree></nrml>"
)
PRIVATE_MARKER_RAW = b"<nrml>PROVIDER_PRIVATE_BODY</nrml>"


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


class FixedEshm20SourceModelDependencyWorkerTests(unittest.TestCase):
    def opener_for(self, raw: bytes, captured: list[str]):
        def opener(request, timeout):
            self.assertGreater(timeout, 0)
            captured.append(request.full_url)
            return FakeResponse(raw, request.full_url)

        return opener

    def synthetic_result(self) -> dict[str, object]:
        return {
            "schema_version": worker.SCHEMA_VERSION,
            "source_issue": worker.SOURCE_ISSUE,
            "control_issue": worker.CONTROL_ISSUE,
            "dataset_id": worker.DATASET_ID,
            "project_id": worker.PROJECT_ID,
            "project_path": worker.PROJECT_PATH,
            "commit_sha": worker.COMMIT_SHA,
            "repository_path": worker.REPOSITORY_PATH,
            "byte_count": len(RAW),
            "sha256": hashlib.sha256(RAW).hexdigest(),
            "parser": worker.PARSER_ID,
            "inventory_receipt_comment_id": worker.INVENTORY_RECEIPT_COMMENT_ID,
            "root_dependency_result_comment_id": worker.ROOT_DEPENDENCY_RESULT_COMMENT_ID,
            "root_dependency_section": worker.ROOT_DEPENDENCY_SECTION,
            "root_dependency_option": worker.ROOT_DEPENDENCY_OPTION,
            "first_order_receipt_request_comment_id": worker.FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID,
            "first_order_receipt_run_id": worker.FIRST_ORDER_RECEIPT_RUN_ID,
            "first_order_receipt_execution_sha": worker.FIRST_ORDER_RECEIPT_EXECUTION_SHA,
            "dependencies": [],
            "dependency_inventory_authorized": False,
            "external_bytes_persisted": False,
            "publication_authorized": False,
        }

    def patched_identity(self, raw: bytes):
        return (
            mock.patch.object(worker, "_CANONICAL_EXPECTED_BYTE_COUNT", len(raw)),
            mock.patch.object(
                worker, "_CANONICAL_EXPECTED_SHA256", hashlib.sha256(raw).hexdigest()
            ),
        )

    def test_frozen_source_capability_and_receipt_identity_are_exact(self) -> None:
        self.assertIs(
            worker._CANONICAL_SOURCE_SPEC,
            worker.first_order_authority._SOURCE_MODEL_LOGIC_TREE,
        )
        self.assertEqual(worker.SOURCE_ISSUE, worker.first_order_authority.SOURCE_ISSUE)
        self.assertEqual(worker.DATASET_ID, worker.first_order_authority.DATASET_ID)
        self.assertEqual(worker.PROJECT_ID, worker.first_order_authority.PROJECT_ID)
        self.assertEqual(worker.PROJECT_PATH, worker.first_order_authority.PROJECT_PATH)
        self.assertEqual(worker.COMMIT_SHA, worker.first_order_authority.COMMIT_SHA)
        self.assertEqual(
            worker.REPOSITORY_PATH,
            worker.first_order_authority._SOURCE_MODEL_LOGIC_TREE.repository_path,
        )
        self.assertEqual(worker.EXPECTED_BYTE_COUNT, 17_579)
        self.assertEqual(
            worker.EXPECTED_SHA256,
            "97a37911f9eae73766f386686b112e5a4e111965da3e4e1543627c28d4201867",
        )
        self.assertEqual(worker.INVENTORY_RECEIPT_COMMENT_ID, 5290449064)
        self.assertEqual(
            worker.INVENTORY_RECEIPT_COMMENT_ID,
            worker.root_bridge.INVENTORY_RECEIPT_COMMENT_ID,
        )
        self.assertEqual(
            worker.ROOT_DEPENDENCY_RESULT_COMMENT_ID,
            worker.first_order_authority.SELECTION_RESULT_COMMENT_ID,
        )
        self.assertNotEqual(
            worker.INVENTORY_RECEIPT_COMMENT_ID,
            worker.ROOT_DEPENDENCY_RESULT_COMMENT_ID,
        )
        self.assertEqual(worker.FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID, 5301857400)
        self.assertEqual(worker.FIRST_ORDER_RECEIPT_RUN_ID, 31880089623)
        self.assertFalse(
            hasattr(worker, "FIRST_ORDER_RECEIPT_RESULT_COMMENT_ID"),
            "complete #361 GitHub result-comment identity is not verified offline",
        )
        self.assertFalse(
            hasattr(worker, "FIRST_ORDER_RECEIPT_RETRIEVED_AT"),
            "unbound runtime receipt timestamps must not become durable evidence",
        )

    def test_public_worker_exposes_no_target_parser_or_inventory_selector(self) -> None:
        signature = inspect.signature(worker.acquire_eshm20_source_model_dependencies)
        self.assertEqual(set(signature.parameters), {"opener", "monotonic"})
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            )
        )

    def test_worker_uses_only_canonical_source_capability(self) -> None:
        captured: list[str] = []
        with mock.patch.object(
            worker,
            "extract_verified_source_model_dependencies",
            return_value=self.synthetic_result(),
        ) as verified_bridge:
            result = worker.acquire_eshm20_source_model_dependencies(
                opener=self.opener_for(RAW, captured)
            )

        self.assertEqual(len(captured), 1)
        self.assertIn(f"/api/v4/projects/{worker._CANONICAL_PROJECT_ID}/", captured[0])
        self.assertIn(worker._CANONICAL_COMMIT_SHA, captured[0])
        self.assertIn("source_model_logic_tree_eshm20_model_v12e.xml", result["repository_path"])
        verified_bridge.assert_called_once_with(RAW)

    def test_equal_but_distinct_source_spec_fails_before_network(self) -> None:
        original = worker.first_order_authority._SOURCE_MODEL_LOGIC_TREE
        replacement = worker.first_order_authority.DependencySpec(
            repository_path=original.repository_path,
            parent_section=original.parent_section,
            parent_option=original.parent_option,
        )
        opened: list[bool] = []

        def opener(request, timeout):
            opened.append(True)
            raise AssertionError("provider must not be called")

        with mock.patch.object(
            worker.first_order_authority,
            "_SOURCE_MODEL_LOGIC_TREE",
            replacement,
        ):
            with self.assertRaisesRegex(
                worker.Eshm20SourceModelDependencyError, "capability identity drifted"
            ):
                worker.acquire_eshm20_source_model_dependencies(opener=opener)
        self.assertEqual(opened, [])

    def test_fixed_authority_alias_drift_fails_before_network(self) -> None:
        cases = (
            ("SOURCE_ISSUE", worker.SOURCE_ISSUE + 1),
            ("CONTROL_ISSUE", worker.CONTROL_ISSUE + 1),
            ("DATASET_ID", "efehr.other"),
            ("PROJECT_ID", worker.PROJECT_ID + 1),
            ("PROJECT_PATH", "efehr/other"),
            ("COMMIT_SHA", "0" * 40),
            (
                "REPOSITORY_PATH",
                worker.first_order_authority._GMPE_LOGIC_TREE.repository_path,
            ),
            ("PARSER_ID", "scripts.other.parser"),
            ("EXPECTED_BYTE_COUNT", worker.EXPECTED_BYTE_COUNT + 1),
            ("EXPECTED_SHA256", "0" * 64),
            ("INVENTORY_RECEIPT_COMMENT_ID", worker.INVENTORY_RECEIPT_COMMENT_ID + 1),
            (
                "ROOT_DEPENDENCY_RESULT_COMMENT_ID",
                worker.ROOT_DEPENDENCY_RESULT_COMMENT_ID + 1,
            ),
            ("ROOT_DEPENDENCY_SECTION", "other"),
            ("ROOT_DEPENDENCY_OPTION", "other"),
            (
                "FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID",
                worker.FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID + 1,
            ),
            ("FIRST_ORDER_RECEIPT_RUN_ID", worker.FIRST_ORDER_RECEIPT_RUN_ID + 1),
            ("FIRST_ORDER_RECEIPT_EXECUTION_SHA", "0" * 40),
        )
        for name, replacement in cases:
            opened: list[bool] = []

            def opener(request, timeout):
                opened.append(True)
                raise AssertionError("provider must not be called")

            with self.subTest(name=name), mock.patch.object(worker, name, replacement):
                with self.assertRaisesRegex(
                    worker.Eshm20SourceModelDependencyError,
                    "frozen ESHM20 source-model",
                ):
                    worker.acquire_eshm20_source_model_dependencies(opener=opener)
            self.assertEqual(opened, [])

    def test_receipt_identity_is_checked_before_decode_or_parser(self) -> None:
        good_count, good_hash = self.patched_identity(RAW)
        with (
            good_count,
            good_hash,
            mock.patch.object(
                worker.parser,
                "extract_source_model_logic_tree_dependencies",
                return_value=(),
            ) as parser_call,
        ):
            worker.extract_verified_source_model_dependencies(RAW)
            parser_call.assert_called_once()
            parser_call.reset_mock()

            tampered = RAW[:-1] + bytes([RAW[-1] ^ 1])
            with self.assertRaisesRegex(worker.Eshm20SourceModelDependencyError, "SHA-256"):
                worker.extract_verified_source_model_dependencies(tampered)
            parser_call.assert_not_called()

        invalid_utf8 = b"\xff" + RAW[1:]
        count_patch, hash_patch = self.patched_identity(invalid_utf8)
        with (
            count_patch,
            hash_patch,
            mock.patch.object(
                worker.parser, "extract_source_model_logic_tree_dependencies"
            ) as parser_call,
        ):
            with self.assertRaisesRegex(
                worker.Eshm20SourceModelDependencyError, "strict UTF-8"
            ):
                worker.extract_verified_source_model_dependencies(invalid_utf8)
            parser_call.assert_not_called()

    def test_real_parser_keeps_exact_inventory_path_and_does_not_invent_hdf5(self) -> None:
        count_patch, hash_patch = self.patched_identity(RAW)
        with count_patch, hash_patch:
            result = worker.extract_verified_source_model_dependencies(RAW)

        self.assertEqual(len(result["dependencies"]), 1)
        dependency = result["dependencies"][0]
        self.assertEqual(dependency["resolved_path"], SOURCE_PATH)
        self.assertEqual(
            dependency["origins"],
            [{"uncertainty_type": "sourceModel", "branch_id": "b1"}],
        )
        self.assertFalse(dependency["is_hdf5_companion"])
        self.assertFalse(any(path.endswith(".hdf5") for path in worker._CANONICAL_INVENTORY))
        self.assertFalse(result["dependency_inventory_authorized"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])

    def test_profile_rebinds_parent_receipt_and_parser_identity_without_unverified_comment_or_time(self) -> None:
        count_patch, hash_patch = self.patched_identity(RAW)
        with count_patch, hash_patch:
            result = worker.extract_verified_source_model_dependencies(RAW)

        self.assertEqual(result["source_issue"], 281)
        self.assertEqual(result["control_issue"], 367)
        self.assertEqual(result["dataset_id"], "efehr.eshm20")
        self.assertEqual(result["project_path"], "efehr/eshm20")
        self.assertEqual(result["inventory_receipt_comment_id"], 5290449064)
        self.assertEqual(result["root_dependency_result_comment_id"], 5301726249)
        self.assertNotEqual(
            result["inventory_receipt_comment_id"],
            result["root_dependency_result_comment_id"],
        )
        self.assertEqual(result["root_dependency_section"], "calculation")
        self.assertEqual(result["root_dependency_option"], "source_model_logic_tree_file")
        self.assertEqual(result["first_order_receipt_request_comment_id"], 5301857400)
        self.assertNotIn("first_order_receipt_result_comment_id", result)
        self.assertNotIn("first_order_receipt_retrieved_at", result)
        self.assertEqual(result["first_order_receipt_run_id"], 31880089623)
        self.assertEqual(
            result["first_order_receipt_execution_sha"],
            "ab66e3e4c58c9b8f18587f1a8a51cf67cf9851b1",
        )
        self.assertEqual(result["byte_count"], len(RAW))
        self.assertEqual(result["sha256"], hashlib.sha256(RAW).hexdigest())
        self.assertEqual(result["parser"], worker._CANONICAL_PARSER_ID)

    def test_out_of_inventory_dependency_fails_closed(self) -> None:
        outside = worker.parser.SourceModelDependency(
            "oq_computational/oq_configuration_eshm20_v12e_region_main/"
            "source_models/not_in_inventory.xml",
            (worker.parser.LogicTreeDependencyOrigin("sourceModel", "b1"),),
            False,
        )
        count_patch, hash_patch = self.patched_identity(RAW)
        with (
            count_patch,
            hash_patch,
            mock.patch.object(
                worker.parser,
                "extract_source_model_logic_tree_dependencies",
                return_value=(outside,),
            ),
        ):
            with self.assertRaisesRegex(
                worker.Eshm20SourceModelDependencyError, "absent from.*inventory"
            ):
                worker.extract_verified_source_model_dependencies(RAW)

    def test_type_confused_parser_output_fails_before_ordering(self) -> None:
        class TypeConfusedDependency:
            resolved_path = 7
            is_hdf5_companion = False
            origins = ()

        legitimate = worker.parser.SourceModelDependency(
            SOURCE_PATH,
            (worker.parser.LogicTreeDependencyOrigin("sourceModel", "b1"),),
            False,
        )
        count_patch, hash_patch = self.patched_identity(RAW)
        with (
            count_patch,
            hash_patch,
            mock.patch.object(
                worker.parser,
                "extract_source_model_logic_tree_dependencies",
                return_value=(legitimate, TypeConfusedDependency()),
            ),
        ):
            with self.assertRaisesRegex(
                worker.Eshm20SourceModelDependencyError, "invalid item"
            ):
                worker.extract_verified_source_model_dependencies(RAW)

    def test_malformed_exact_origin_identities_fail_before_serialization(self) -> None:
        malformed_origins = (
            worker.parser.LogicTreeDependencyOrigin("sourceModel", ""),
            worker.parser.LogicTreeDependencyOrigin("sourceModel", "   "),
            worker.parser.LogicTreeDependencyOrigin("sourceModel", " bad"),
            worker.parser.LogicTreeDependencyOrigin("sourceModel", "bad\nbranch"),
            worker.parser.LogicTreeDependencyOrigin("sourceModel\t", "b1"),
            worker.parser.LogicTreeDependencyOrigin(" sourceModel", "b1"),
        )
        count_patch, hash_patch = self.patched_identity(RAW)
        with count_patch, hash_patch:
            for origin in malformed_origins:
                with self.subTest(origin=origin):
                    dependency = worker.parser.SourceModelDependency(
                        SOURCE_PATH,
                        (origin,),
                        False,
                    )
                    with mock.patch.object(
                        worker.parser,
                        "extract_source_model_logic_tree_dependencies",
                        return_value=(dependency,),
                    ):
                        with self.assertRaises(worker.Eshm20SourceModelDependencyError):
                            worker.extract_verified_source_model_dependencies(RAW)

    def test_noncanonical_or_duplicate_dependency_output_fails_closed(self) -> None:
        origin = (worker.parser.LogicTreeDependencyOrigin("sourceModel", "b1"),)
        first = worker.parser.SourceModelDependency(SOURCE_PATH, origin, False)
        second = worker.parser.SourceModelDependency(OTHER_SOURCE_PATH, origin, False)
        count_patch, hash_patch = self.patched_identity(RAW)
        with count_patch, hash_patch:
            with mock.patch.object(
                worker.parser,
                "extract_source_model_logic_tree_dependencies",
                return_value=(second, first),
            ):
                with self.assertRaisesRegex(
                    worker.Eshm20SourceModelDependencyError, "canonical order"
                ):
                    worker.extract_verified_source_model_dependencies(RAW)

            with mock.patch.object(
                worker.parser,
                "extract_source_model_logic_tree_dependencies",
                return_value=(first, first),
            ):
                with self.assertRaisesRegex(
                    worker.Eshm20SourceModelDependencyError, "duplicate path"
                ):
                    worker.extract_verified_source_model_dependencies(RAW)

    def test_parser_failure_does_not_leak_source_text(self) -> None:
        count_patch, hash_patch = self.patched_identity(PRIVATE_MARKER_RAW)
        with (
            count_patch,
            hash_patch,
            mock.patch.object(
                worker.parser,
                "extract_source_model_logic_tree_dependencies",
                side_effect=worker.parser.OpenQuakeLogicTreeError(
                    "PROVIDER_PRIVATE_BODY"
                ),
            ),
        ):
            with self.assertRaises(worker.Eshm20SourceModelDependencyError) as caught:
                worker.extract_verified_source_model_dependencies(PRIVATE_MARKER_RAW)
        self.assertNotIn("PROVIDER_PRIVATE_BODY", str(caught.exception))
        self.assertIn("failed closed", str(caught.exception))

    def test_response_identity_status_and_oversize_fail_before_profile(self) -> None:
        def wrong_url_opener(request, timeout):
            return FakeResponse(
                RAW,
                request.full_url,
                final_url="https://gitlab.seismo.ethz.ch/unexpected",
            )

        def wrong_status_opener(request, timeout):
            return FakeResponse(RAW, request.full_url, status=206)

        oversize = b"x" * (worker._CANONICAL_EXPECTED_BYTE_COUNT + 1)

        for opener in (
            wrong_url_opener,
            wrong_status_opener,
            self.opener_for(oversize, []),
        ):
            with self.subTest(opener=opener):
                with mock.patch.object(
                    worker, "extract_verified_source_model_dependencies"
                ) as verified_bridge:
                    with self.assertRaises(worker.Eshm20SourceModelDependencyError):
                        worker.acquire_eshm20_source_model_dependencies(opener=opener)
                verified_bridge.assert_not_called()

    def test_transport_failure_does_not_leak_provider_exception_text(self) -> None:
        def opener(request, timeout):
            raise OSError("PROVIDER_SECRET_BODY")

        with self.assertRaises(worker.Eshm20SourceModelDependencyError) as caught:
            worker.acquire_eshm20_source_model_dependencies(opener=opener)
        self.assertNotIn("PROVIDER_SECRET_BODY", str(caught.exception))
        self.assertIn("OSError", str(caught.exception))

    def test_provider_payload_is_not_returned_and_authority_cannot_widen(self) -> None:
        result = self.synthetic_result()
        with mock.patch.object(
            worker,
            "extract_verified_source_model_dependencies",
            return_value=result,
        ):
            observed = worker.acquire_eshm20_source_model_dependencies(
                opener=self.opener_for(PRIVATE_MARKER_RAW, [])
            )
        self.assertNotIn("PROVIDER_PRIVATE_BODY", repr(observed))
        self.assertNotIn("first_order_receipt_result_comment_id", observed)
        self.assertNotIn("first_order_receipt_retrieved_at", observed)

        for mutation in (
            {"dependency_inventory_authorized": True},
            {"external_bytes_persisted": True},
            {"publication_authorized": True},
        ):
            widened = self.synthetic_result()
            widened.update(mutation)
            with mock.patch.object(
                worker,
                "extract_verified_source_model_dependencies",
                return_value=widened,
            ):
                with self.assertRaisesRegex(
                    worker.Eshm20SourceModelDependencyError, "widened"
                ):
                    worker.acquire_eshm20_source_model_dependencies(
                        opener=self.opener_for(RAW, [])
                    )


if __name__ == "__main__":
    unittest.main()
