# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import profile_eshm20_gsim_identities as profiler
from scripts import verify_eshm20_gsim_openquake314 as verifier


def xml_for(branch_sets: str) -> bytes:
    return f"<nrml><logicTree>{branch_sets}</logicTree></nrml>".encode()


def branch_set(
    *,
    set_id: str = "bs1",
    branch_id: str = "b1",
    model: str = "ExampleGsim",
    attrs: str = "",
) -> str:
    return f"""
    <logicTreeBranchSet uncertaintyType="gmpeModel" branchSetID="{set_id}" applyToTectonicRegionType="Active Shallow Crust">
      <logicTreeBranch branchID="{branch_id}">
        <uncertaintyModel{attrs}>{model}</uncertaintyModel>
        <uncertaintyWeight>1.0</uncertaintyWeight>
      </logicTreeBranch>
    </logicTreeBranchSet>
    """


def verified_payload(xml: bytes):
    return (
        patch.object(profiler, "EXPECTED_BYTE_COUNT", len(xml)),
        patch.object(profiler, "EXPECTED_SHA256", hashlib.sha256(xml).hexdigest()),
    )


class FakeGsim:
    pass


def passthrough_to_toml(model):
    text = (model.text or "").strip()
    if not text.startswith("["):
        text = f"[{text}]"
    for key, value in model.attrib.items():
        text += f"\n{key} = {value!r}"
    return text


class Eshm20OpenQuake314CompatibilityTests(unittest.TestCase):
    def test_git_hash_primitives_match_known_git_objects(self) -> None:
        self.assertEqual(
            verifier._git_blob_sha1(b""),
            "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
        )
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                verifier._git_tree_sha1(Path(tmp)),
                "4b825dc642cb6eb9a060e54bf8d69288fbee4904",
            )

    def test_tree_identity_detects_content_addition_and_mode_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file = root / "module.py"
            file.write_text("value = 1\n", encoding="utf-8")
            baseline = verifier._git_tree_sha1(root)
            file.write_text("value = 2\n", encoding="utf-8")
            self.assertNotEqual(verifier._git_tree_sha1(root), baseline)
            file.write_text("value = 1\n", encoding="utf-8")
            extra = root / "extra.py"
            extra.write_text("pass\n", encoding="utf-8")
            self.assertNotEqual(verifier._git_tree_sha1(root), baseline)
            extra.unlink()
            os.chmod(file, 0o755)
            self.assertNotEqual(verifier._git_tree_sha1(root), baseline)

    def test_pycache_does_not_change_source_tree_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "module.py").write_text("value = 1\n", encoding="utf-8")
            baseline = verifier._git_tree_sha1(root)
            cache = root / "__pycache__"
            cache.mkdir()
            (cache / "module.cpython-312.pyc").write_bytes(b"generated")
            self.assertEqual(verifier._git_tree_sha1(root), baseline)

    def test_attestation_is_fail_closed_on_wrong_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "openquake"
            root.mkdir()
            with self.assertRaisesRegex(
                verifier.Eshm20OpenQuake314CompatibilityError, "does not match"
            ):
                verifier.attest_openquake314_source_tree(root)

    def test_wrong_payload_fails_before_runtime_invocation(self) -> None:
        calls = []

        def runtime(*args, **kwargs):
            calls.append((args, kwargs))
            return FakeGsim()

        with self.assertRaises(profiler.Eshm20GsimIdentityProfileError):
            verifier._verify_with_runtime(
                b"wrong",
                openquake_version="3.14.0",
                to_toml_callable=passthrough_to_toml,
                gsim_callable=runtime,
                source_tree_sha1=verifier.OPENQUAKE_SUBTREE_SHA1,
            )
        self.assertEqual(calls, [])

    def test_wrong_tree_and_version_fail_before_runtime_invocation(self) -> None:
        xml = xml_for(branch_set())
        calls = []

        def runtime(*args, **kwargs):
            calls.append((args, kwargs))
            return FakeGsim()

        p1, p2 = verified_payload(xml)
        with p1, p2:
            with self.assertRaisesRegex(
                verifier.Eshm20OpenQuake314CompatibilityError, "attestation"
            ):
                verifier._verify_with_runtime(
                    xml,
                    openquake_version="3.14.0",
                    to_toml_callable=passthrough_to_toml,
                    gsim_callable=runtime,
                    source_tree_sha1="0" * 40,
                )
            with self.assertRaisesRegex(
                verifier.Eshm20OpenQuake314CompatibilityError, "version"
            ):
                verifier._verify_with_runtime(
                    xml,
                    openquake_version="3.15.0",
                    to_toml_callable=passthrough_to_toml,
                    gsim_callable=runtime,
                    source_tree_sha1=verifier.OPENQUAKE_SUBTREE_SHA1,
                )
        self.assertEqual(calls, [])

    def test_external_resource_key_fails_before_runtime_invocation(self) -> None:
        xml = xml_for(branch_set(model="[ExampleGsim]\ncoeff_file = 'do-not-read'"))
        calls = []

        def runtime(*args, **kwargs):
            calls.append((args, kwargs))
            return FakeGsim()

        p1, p2 = verified_payload(xml)
        with p1, p2, self.assertRaisesRegex(
            verifier.Eshm20OpenQuake314CompatibilityError, "external GSIM resources"
        ):
            verifier._verify_with_runtime(
                xml,
                openquake_version="3.14.0",
                to_toml_callable=passthrough_to_toml,
                gsim_callable=runtime,
                source_tree_sha1=verifier.OPENQUAKE_SUBTREE_SHA1,
            )
        self.assertEqual(calls, [])

    def test_alias_expansion_resource_key_fails_before_constructor(self) -> None:
        xml = xml_for(branch_set(model="AliasWithHiddenFile"))
        calls = []

        def alias_to_toml(model):
            return "[Resolved]\ncoeff_table = 'hidden-provider-path'"

        def runtime(*args, **kwargs):
            calls.append((args, kwargs))
            return FakeGsim()

        p1, p2 = verified_payload(xml)
        with p1, p2, self.assertRaisesRegex(
            verifier.Eshm20OpenQuake314CompatibilityError,
            "alias/TOML expansion",
        ):
            verifier._verify_with_runtime(
                xml,
                openquake_version="3.14.0",
                to_toml_callable=alias_to_toml,
                gsim_callable=runtime,
                source_tree_sha1=verifier.OPENQUAKE_SUBTREE_SHA1,
            )
        self.assertEqual(calls, [])

    def test_constructor_failure_does_not_leak_provider_value(self) -> None:
        secret = "provider-secret-value"
        xml = xml_for(branch_set(model=f"[ExampleGsim]\nsecret = '{secret}'"))

        def runtime(*args, **kwargs):
            print(secret)
            raise ValueError(f"bad {secret}")

        p1, p2 = verified_payload(xml)
        with p1, p2, self.assertRaises(
            verifier.Eshm20OpenQuake314CompatibilityError
        ) as caught:
            verifier._verify_with_runtime(
                xml,
                openquake_version="3.14.0",
                to_toml_callable=passthrough_to_toml,
                gsim_callable=runtime,
                source_tree_sha1=verifier.OPENQUAKE_SUBTREE_SHA1,
            )
        self.assertNotIn(secret, str(caught.exception))
        self.assertIn("branch index 0", str(caught.exception))

    def test_success_is_deterministic_and_keeps_authority_ceilings_false(self) -> None:
        a = branch_set(set_id="z", branch_id="z1", model="AliasZ")
        b = branch_set(set_id="a", branch_id="a1", model="ClassA")

        class ResolvedAlias:
            pass

        class ResolvedClass:
            pass

        def runtime(model, basedir=""):
            token, _ = profiler._structural_model_identity(model)
            return ResolvedAlias() if token == "AliasZ" else ResolvedClass()

        results = []
        for xml in (xml_for(a + b), xml_for(b + a)):
            p1, p2 = verified_payload(xml)
            with p1, p2:
                results.append(
                    verifier._verify_with_runtime(
                        xml,
                        openquake_version="3.14.0+exact-tree",
                        to_toml_callable=passthrough_to_toml,
                        gsim_callable=runtime,
                        source_tree_sha1=verifier.OPENQUAKE_SUBTREE_SHA1,
                    )
                )
        self.assertEqual(
            results[0]["resolution_fingerprint_sha256"],
            results[1]["resolution_fingerprint_sha256"],
        )
        result = results[0]
        self.assertTrue(result["openquake_source_tree_verified"])
        self.assertTrue(result["constructor_compatibility_verified"])
        self.assertFalse(result["reference_environment_identity_closed"])
        self.assertFalse(result["provider_model_text_returned"])
        self.assertFalse(result["provider_argument_values_returned"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertNotIn("AliasZ", repr(result))
        self.assertNotIn("ClassA", repr(result))


if __name__ == "__main__":
    unittest.main()
