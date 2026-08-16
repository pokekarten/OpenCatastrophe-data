# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import profile_eshm20_gsim_identities as profiler
from scripts import validate_eshm20_gsim_openquake_runtime as gate


def xml_for(model: str = "DirectGsim", *, model_attrs: str = "") -> bytes:
    return f"""
    <nrml><logicTree>
      <logicTreeBranchSet uncertaintyType="gmpeModel" branchSetID="bs1" applyToTectonicRegionType="Active Shallow Crust">
        <logicTreeBranch branchID="b1">
          <uncertaintyModel{model_attrs}>{model}</uncertaintyModel>
          <uncertaintyWeight>1.0</uncertaintyWeight>
        </logicTreeBranch>
      </logicTreeBranchSet>
    </logicTree></nrml>
    """.encode()


class DirectGsim:
    pass


class ResolvedGsim:
    pass


class FakeRuntime:
    def __init__(self) -> None:
        self.aliases = frozenset({"AliasGsim", "AliasResourceGsim"})
        self.registry = {
            "DirectGsim": DirectGsim,
            "ResolvedGsim": ResolvedGsim,
            "AliasGsim": ResolvedGsim,
            "AliasResourceGsim": ResolvedGsim,
        }
        self.engine_source_checkout_verified = True
        self.engine_checkout_commit = gate.OPENQUAKE_COMMIT
        self.calls = 0

    @staticmethod
    def _token(model: object) -> str:
        text = (getattr(model, "text", "") or "").strip()
        first = text.splitlines()[0].strip()
        return first[1:-1].strip() if first.startswith("[") else first

    def argument_keys_after_alias(self, model: object) -> list[str]:
        text = (getattr(model, "text", "") or "").strip()
        keys = list(getattr(model, "attrib", {}).keys())
        for line in text.splitlines()[1:]:
            if "=" in line:
                keys.append(line.split("=", 1)[0].strip())
        if self._token(model) == "AliasResourceGsim":
            keys.append("coeffs_file")
        return sorted(keys)

    def instantiate(self, model: object) -> object:
        self.calls += 1
        token = self._token(model)
        if token == "DirectGsim":
            return DirectGsim()
        if token in {"AliasGsim", "AliasResourceGsim"}:
            return ResolvedGsim()
        if token == "BrokenGsim":
            raise TypeError("argument-value-must-not-leak")
        return ResolvedGsim()


def evaluate(
    payload: bytes,
    runtime: FakeRuntime | None = None,
) -> tuple[dict[str, object], FakeRuntime]:
    runtime = runtime or FakeRuntime()
    digest = hashlib.sha256(payload).hexdigest()
    with (
        patch.object(profiler, "EXPECTED_BYTE_COUNT", len(payload)),
        patch.object(profiler, "EXPECTED_SHA256", digest),
        patch.object(profiler, "EXPECTED_BRANCH_SET_COUNT", 1),
        patch.object(profiler, "EXPECTED_BRANCH_COUNT", 1),
    ):
        result = gate._evaluate_verified_payload(
            payload,
            {"reference_recipe_match": True},
            runtime,
        )
    return result, runtime


class Eshm20GsimOpenQuakeRuntimeTests(unittest.TestCase):
    def test_direct_class_resolves_without_alias(self) -> None:
        result, _ = evaluate(xml_for())
        branch = result["branches"][0]
        self.assertEqual(branch["requested_gsim_token"], "DirectGsim")
        self.assertEqual(branch["resolved_gsim_class"], "DirectGsim")
        self.assertEqual(branch["request_form"], "bare")
        self.assertFalse(branch["alias_definition_present"])
        self.assertFalse(branch["alias_expansion_applied"])
        self.assertTrue(branch["constructor_accepted"])
        self.assertEqual(
            result["reference_runtime_fingerprint"],
            {"reference_recipe_match": True},
        )
        self.assertTrue(result["reference_runtime_observation_validated"])
        self.assertFalse(result["executing_environment_bound_to_reference_recipe"])
        self.assertFalse(result["reference_runtime_recipe_verified"])
        self.assertTrue(result["exact_source_constructor_compatibility_verified"])
        self.assertFalse(result["gsim_request_runtime_compatibility_verified"])
        self.assertFalse(result["full_hazard_compatibility_verified"])
        self.assertFalse(result["model_use_authorized"])

    def test_bare_alias_is_explicitly_resolved(self) -> None:
        result, _ = evaluate(xml_for("AliasGsim"))
        branch = result["branches"][0]
        self.assertEqual(branch["resolved_gsim_class"], "ResolvedGsim")
        self.assertTrue(branch["alias_definition_present"])
        self.assertTrue(branch["alias_expansion_applied"])
        self.assertFalse(branch["registry_alias_key_used"])
        self.assertEqual(result["alias_requested_tokens"], ["AliasGsim"])

    def test_explicit_alias_table_is_not_mislabeled_as_alias_expansion(self) -> None:
        result, _ = evaluate(xml_for("[AliasGsim]\nfoo = 1"))
        branch = result["branches"][0]
        self.assertEqual(branch["request_form"], "table")
        self.assertTrue(branch["alias_definition_present"])
        self.assertFalse(branch["alias_expansion_applied"])
        self.assertTrue(branch["registry_alias_key_used"])
        self.assertEqual(branch["argument_keys"], ["foo"])
        self.assertEqual(branch["runtime_argument_keys_after_alias"], ["foo"])

    def test_identity_change_without_alias_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            gate.Eshm20GsimRuntimeCompatibilityError,
            "changed identity without an alias",
        ):
            evaluate(xml_for("OtherGsim"))

    def test_constructor_failure_does_not_serialize_argument_values(self) -> None:
        payload = xml_for("BrokenGsim", model_attrs=' secret="do-not-serialize"')
        with self.assertRaises(gate.Eshm20GsimRuntimeCompatibilityError) as caught:
            evaluate(payload)
        self.assertNotIn("argument-value-must-not-leak", str(caught.exception))
        self.assertNotIn("do-not-serialize", str(caught.exception))

    def test_external_resource_key_fails_before_runtime_instantiation(self) -> None:
        runtime = FakeRuntime()
        with self.assertRaisesRegex(
            gate.Eshm20GsimRuntimeCompatibilityError,
            "requires external resources",
        ):
            evaluate(xml_for("[DirectGsim]\ncoeffs_file = 'outside.csv'"), runtime)
        self.assertEqual(runtime.calls, 0)

    def test_alias_introduced_resource_key_fails_before_runtime_instantiation(self) -> None:
        runtime = FakeRuntime()
        with self.assertRaisesRegex(
            gate.Eshm20GsimRuntimeCompatibilityError,
            "requires external resources after alias expansion",
        ):
            evaluate(xml_for("AliasResourceGsim"), runtime)
        self.assertEqual(runtime.calls, 0)

    def test_unverified_or_wrong_source_checkout_fails_closed(self) -> None:
        runtime = FakeRuntime()
        runtime.engine_source_checkout_verified = False
        with self.assertRaisesRegex(
            gate.Eshm20GsimRuntimeCompatibilityError,
            "source checkout identity",
        ):
            evaluate(xml_for(), runtime)

        runtime = FakeRuntime()
        runtime.engine_checkout_commit = "0" * 40
        with self.assertRaisesRegex(
            gate.Eshm20GsimRuntimeCompatibilityError,
            "commit drifted",
        ):
            evaluate(xml_for(), runtime)

    def test_invalid_runtime_observation_fails_before_openquake_import(self) -> None:
        with (
            patch.object(gate, "_load_verified_openquake_runtime") as load_runtime,
            self.assertRaisesRegex(
                gate.Eshm20GsimRuntimeCompatibilityError,
                "fingerprint did not pass",
            ),
        ):
            gate.validate_verified_gsim_runtime(b"not-inspected", {})
        load_runtime.assert_not_called()

    def test_public_path_binds_validated_fingerprint_not_raw_observation(self) -> None:
        payload = xml_for()
        digest = hashlib.sha256(payload).hexdigest()
        raw_observation = {"unvalidated_secret": "must-not-be-output"}
        validated_fingerprint = {
            "reference_recipe_match": True,
            "observation": {
                "engine_version": gate.OPENQUAKE_VERSION,
                "python_version": "3.8.17",
            },
        }
        with (
            patch.object(profiler, "EXPECTED_BYTE_COUNT", len(payload)),
            patch.object(profiler, "EXPECTED_SHA256", digest),
            patch.object(profiler, "EXPECTED_BRANCH_SET_COUNT", 1),
            patch.object(profiler, "EXPECTED_BRANCH_COUNT", 1),
            patch.object(
                gate.runtime_fingerprint,
                "validate_runtime_observation",
                return_value=validated_fingerprint,
            ),
            patch.object(
                gate,
                "_load_verified_openquake_runtime",
                return_value=FakeRuntime(),
            ),
        ):
            result = gate.validate_verified_gsim_runtime(payload, raw_observation)

        self.assertEqual(
            result["reference_runtime_fingerprint"], validated_fingerprint
        )
        self.assertTrue(result["reference_runtime_observation_validated"])
        self.assertFalse(result["reference_runtime_recipe_verified"])
        self.assertFalse(result["gsim_request_runtime_compatibility_verified"])
        self.assertNotIn("must-not-be-output", repr(result))

    def test_frozen_release_and_commit_bound_git_versions_are_accepted(self) -> None:
        gate._require_compatible_openquake_version(gate.OPENQUAKE_VERSION)
        for prefix_length in (7, 12, 40):
            with self.subTest(prefix_length=prefix_length):
                gate._require_compatible_openquake_version(
                    gate.OPENQUAKE_VERSION
                    + "-git"
                    + gate.OPENQUAKE_COMMIT[:prefix_length]
                )

    def test_foreign_or_malformed_runtime_versions_fail_closed(self) -> None:
        rejected = (
            gate.OPENQUAKE_VERSION + "-gitdeadbee",
            gate.OPENQUAKE_VERSION + "-git" + gate.OPENQUAKE_COMMIT[:6],
            gate.OPENQUAKE_VERSION + "-git" + gate.OPENQUAKE_COMMIT[:7].upper(),
            gate.OPENQUAKE_VERSION + "-git" + gate.OPENQUAKE_COMMIT + "0",
            "3.14.1",
            True,
            None,
        )
        for value in rejected:
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    gate.Eshm20GsimRuntimeCompatibilityError,
                    "does not match the frozen v3.14.0 source",
                ):
                    gate._require_compatible_openquake_version(value)

    def test_output_never_contains_argument_values(self) -> None:
        result, _ = evaluate(
            xml_for(
                "[DirectGsim]\nfoo = 'private-ish-value'",
                model_attrs=' bar="another-value"',
            )
        )
        rendered = repr(result)
        self.assertIn("foo", rendered)
        self.assertIn("bar", rendered)
        self.assertNotIn("private-ish-value", rendered)
        self.assertNotIn("another-value", rendered)

    def test_exact_checkout_helper_rejects_dirty_or_untracked_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "openquake" / "hazardlib" / "valid.py"
            source.parent.mkdir(parents=True)
            source.write_text("VALUE = 1\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "config",
                    "user.email",
                    "test@example.invalid",
                ],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(root), "config", "user.name", "Test"],
                check=True,
            )
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(root), "commit", "-qm", "fixture"],
                check=True,
            )
            head = subprocess.check_output(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
            ).strip()

            with patch.object(gate, "OPENQUAKE_COMMIT", head):
                self.assertEqual(gate._verify_exact_openquake_checkout(source), root)
                (root / "openquake" / "evil.py").write_text(
                    "BAD = True\n",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(
                    gate.Eshm20GsimRuntimeCompatibilityError,
                    "modifications or untracked files",
                ):
                    gate._verify_exact_openquake_checkout(source)


if __name__ == "__main__":
    unittest.main()