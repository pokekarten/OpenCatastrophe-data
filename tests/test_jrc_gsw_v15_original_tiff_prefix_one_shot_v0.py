# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No-network synthetic one-shot CloudFerro JRC source TIFF prefix tests."""
from __future__ import annotations

from copy import deepcopy
from email.message import Message
import hashlib
import json
import tomllib
import unittest
from urllib import error
from unittest.mock import patch

from research_runners import jrc_gsw_v15_original_tiff_prefix_one_shot_v0 as jrc
from scripts.validate_source_access import validate_contract, validate_path
from tests.test_preflight_jrc_gsw_v15_occurrence_header_v0 import classic


class FakeResponse:
    def __init__(self, body, *, status=206, url=jrc.SOURCE_URL, headers=None):
        self.body = body
        self.status = status
        self.url = url
        self.headers = headers or {
            "Content-Type": "image/tiff",
            "Content-Encoding": "identity",
            "Content-Range": "bytes 0-4095/10000000",
            "Content-Length": "4096",
        }
        self.read_sizes = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return self.url

    def read(self, size):
        self.read_sizes.append(size)
        return self.body[:size]


def hypothetical_review(policy, contract):
    """Synthetic future review state: NOT authority to change canonical files."""
    policy = deepcopy(policy)
    contract = deepcopy(contract)
    policy["public_anonymous_download_permission"] = "reviewed_allowed"
    policy["customer_terms_applicability_to_anonymous_reader"] = "reviewed"
    policy["range_support_verified"] = True
    policy["redirect_policy_verified"] = True
    policy["anonymous_http_rate_cap"] = 1
    policy["approved_network_requests"] = 1
    policy["approved_original_download_bytes"] = jrc.PREFIX_BYTES
    policy["live_provider_probe_approved"] = True
    contract["status"] = "probe_ready"
    contract["implementation_decision"] = "build_adapter_now"
    contract["rights_and_policy"]["api_terms_status"] = "separate_reviewed"
    # This official provider-hosted customer-terms URL alone is NOT proof
    # that those terms govern anonymous JRC readers. These flags are
    # synthetic in-memory test data, not a reviewed real-world decision.
    contract["rights_and_policy"]["terms_url"] = (
        "https://cloudferro.s3.waw3-1.cloudferro.com/"
        "wp-content/uploads/2024/05/general_terms_and_conditions.pdf"
    )
    contract["rights_and_policy"]["commercial_automation_status"] = "allowed"
    contract["probe_contract"]["mode"] = "provider_specific"
    contract["probe_contract"]["operation"] = "inspect_fixed_v15_occurrence_tiff"
    contract["probe_contract"]["expected_evidence"] = [
        "Original HTTP206 exact 4096-byte TIFF prefix and SHA256"
    ]
    contract["request_contract"]["parameter_rules"] = jrc.ACTIVE_ONE_SHOT_PARAMETER_RULES
    validate_contract(contract)
    return policy, contract


class JRCOriginalPrefixOneShotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = tomllib.loads(jrc.POLICY.read_text(encoding="utf-8"))
        cls.contract = validate_path(jrc.CONTRACT)

    def test_current_repository_cannot_call_cloudferro_under_any_cli_flag(self):
        reasons = jrc.authorization_blockers(self.policy, self.contract)
        self.assertTrue(reasons)
        self.assertIn("independently reviewed public anonymous source-asset GET permission", reasons)
        self.assertIn("independently reviewed active probe contract", reasons)
        self.assertIn("CloudFerro anonymous-reader service scope independently reviewed", reasons)
        self.assertIn("HTTP Range method/service entitlement independently verified", reasons)
        self.assertIn("no-redirect original-host transport policy independently verified", reasons)
        calls = []
        def forbidden(req, timeout):
            calls.append(req.full_url)
            raise AssertionError("source GET must not occur")
        with self.assertRaisesRegex(jrc.OriginalPrefixBlocked, "source request blocked"):
            jrc.probe_original_prefix(self.policy, self.contract, open_request=forbidden)
        self.assertEqual(calls, [])
        # Even --one-shot must not bypass two canonical independent gates.
        with patch.object(jrc, "_open_fixed", side_effect=AssertionError("called")):
            self.assertEqual(jrc.main(["--one-shot"]), 1)

    def test_synthetic_post_review_contract_is_schema_valid_and_requires_all_gates(self):
        policy, contract = hypothetical_review(self.policy, self.contract)
        self.assertEqual(jrc.authorization_blockers(policy, contract), [])
        for target, key, bad in (
            ("p", "public_anonymous_download_permission", "unknown"),
            ("p", "customer_terms_applicability_to_anonymous_reader", "unverified"),
            ("p", "range_support_verified", False),
            ("p", "range_support_verified", 1),
            ("p", "redirect_policy_verified", False),
            ("p", "redirect_policy_verified", 1),
            ("p", "approved_network_requests", 2),
            ("p", "approved_network_requests", True),
            ("p", "approved_original_download_bytes", 8192),
            ("p", "approved_original_download_bytes", True),
            ("p", "live_provider_probe_approved", False),
            ("p", "fixed_tile_url", "https://attacker.example/tiff"),
            ("p", "anonymous_http_rate_cap", 0),
            ("p", "anonymous_http_rate_cap", True),
            ("c", "status", "documented_only"),
            ("c", "service_root", "https://attacker.example"),
            ("c", "request_contract", dict(contract["request_contract"],
                                           parameter_rules=self.contract["request_contract"]["parameter_rules"])),
            ("c", "request_contract", dict(contract["request_contract"],
                                           parameter_rules="EXPLICIT REVIEWED JRC V1.5 SOURCE OPERATION: unlimited downloads")),
            ("c", "probe_contract", {"mode":"none","operation":None,
                "requires_credentials":False,"expected_evidence":[]}),
            ("c", "rights_and_policy", dict(contract["rights_and_policy"],
                                           api_terms_status="separate_unreviewed")),
        ):
            p, c = deepcopy(policy), deepcopy(contract)
            (p if target == "p" else c)[key] = bad
            with self.subTest(target=target,key=key,bad=str(bad)[:30]):
                self.assertTrue(jrc.authorization_blockers(p, c))

    def test_official_terms_host_required_without_confusing_customer_contract_for_grant(self):
        p,c=hypothetical_review(self.policy,self.contract)
        for url in (
            "https://example.test/fake-approval",
            "https://cloudferro.com.evil.example/terms",
            "http://docs.cloudferro.com/terms",
            "https://docs.cloudferro.com/",
            "https://user:password@docs.cloudferro.com/terms",
            "https://docs.cloudferro.com/terms?approval=1",
        ):
            changed=deepcopy(c)
            changed["rights_and_policy"]["terms_url"]=url
            with self.subTest(url=url):
                self.assertIn("separately reviewed anonymous API/commercial terms",
                              jrc.authorization_blockers(p,changed))
        self.assertEqual(jrc.authorization_blockers(p,c), [])

    def test_direct_runner_cannot_bypass_complete_contract_schema(self):
        p,c=hypothetical_review(self.policy,self.contract)
        broken=deepcopy(c)
        broken.pop("response_contract")
        # All coarse-grained activation fields are present, but the full
        # source-access schema must block the direct function call.
        self.assertEqual(jrc.authorization_blockers(p,broken), [])
        calls=[]
        def must_not_open(*args):
            calls.append(True)
            raise AssertionError("should have blocked before a GET")
        with self.assertRaisesRegex(jrc.OriginalPrefixBlocked, "contract is invalid"):
            jrc.probe_original_prefix(p,broken,open_request=must_not_open)
        self.assertEqual(calls, [])

    def test_exact_successful_206_range_with_native_tiff_parses_metadata_only(self):
        p, c = hypothetical_review(self.policy, self.contract)
        raw = classic()
        response = FakeResponse(raw)
        calls = []
        def fake_open(req, timeout):
            calls.append(req)
            self.assertEqual(req.full_url, jrc.SOURCE_URL)
            self.assertEqual(req.get_method(), "GET")
            self.assertEqual(req.get_header("Range"), "bytes=0-4095")
            self.assertEqual(req.get_header("Accept-encoding"), "identity")
            self.assertEqual(timeout, 20)
            return response
        result = jrc.probe_original_prefix(p, c, open_request=fake_open)
        self.assertEqual(len(calls), 1)
        self.assertEqual(response.read_sizes, [4096])
        self.assertEqual(result["http_status"], 206)
        self.assertEqual(result["original_range_bytes_received"], 4096)
        self.assertEqual(result["original_range_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["external_prefix_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertTrue(result["range_response_verified"])
        self.assertTrue(result["http_206_exact_requested_url_and_range_observed"])
        self.assertFalse(result["original_provider_source_identity_verified"])
        self.assertFalse(result["original_asset_release_identity_independently_verified"])
        self.assertTrue(result["first_ifd_fully_within_prefix"])
        self.assertFalse(result["whole_original_tiff_sha256_verified"])
        self.assertFalse(result["post_2026_11_10_correction_verified"])
        self.assertFalse(result["decoded_original_pixels_verified"])
        self.assertFalse(result["model_input_approved"])
        self.assertIsNone(result["original_asset_whole_file_sha256"])
        self.assertNotIn("provider_body", json.dumps(result))
        self.assertNotIn("pixel_array", json.dumps(result))

    def test_no_200_full_download_no_redirect_no_wrong_host(self):
        p, c = hypothetical_review(self.policy, self.contract)
        for response in (
            FakeResponse(classic(), status=200),
            FakeResponse(classic(), status=302),
            FakeResponse(classic(), url="https://attacker.example/other.tif"),
            FakeResponse(classic(), headers={"Content-Type":"text/html",
                "Content-Range":"bytes 0-4095/10000000","Content-Length":"4096"}),
            FakeResponse(classic(), headers={"Content-Type":"image/tiff",
                "Content-Encoding":"gzip","Content-Range":"bytes 0-4095/10000000",
                "Content-Length":"4096"}),
        ):
            with self.subTest(status=response.status,url=response.url), self.assertRaises(
                jrc.OriginalPrefixBlocked
            ):
                jrc.probe_original_prefix(p,c,open_request=lambda *_:response)

    def test_unbounded_or_unverifiable_range_response_blocked(self):
        p, c = hypothetical_review(self.policy, self.contract)
        for headers in (
            {"Content-Type":"image/tiff","Content-Length":"4096"},
            {"Content-Type":"image/tiff","Content-Range":"bytes 1-4096/10000000",
             "Content-Length":"4096"},
            {"Content-Type":"image/tiff","Content-Range":"bytes 0-4095/*",
             "Content-Length":"4096"},
            {"Content-Type":"image/tiff","Content-Range":"bytes 0-4095/4096",
             "Content-Length":"4096"},
            {"Content-Type":"image/tiff","Content-Range":"bytes 0-4095/10000000",
             "Content-Length":"8192"},
            {"Content-Type":"image/tiff","Content-Range":"bytes 0-4095/10000000"},
            {"Content-Type":"image/tiff","Content-Range":"bytes 0-4095/" + "9"*5000,
             "Content-Length":"4096"},
            {"Content-Type":"image/tiff","Content-Range":"bytes 0-4095/10000000",
             "Content-Length":"9"*5000},
        ):
            with self.subTest(headers=headers), self.assertRaises(jrc.OriginalPrefixBlocked):
                jrc.probe_original_prefix(p,c,
                    open_request=lambda *_:FakeResponse(classic(),headers=headers))

    def test_duplicate_original_http_framing_is_rejected_before_any_body_read(self):
        # Real urllib HTTPResponse.headers is an email.message.Message.
        # A dict fake can't represent multiple Content-Length/Range lines,
        # so use the same multi-value API as the production HTTP client.
        p,c=hypothetical_review(self.policy,self.contract)
        pairs={
            "Content-Type":"image/tiff",
            "Content-Encoding":"identity",
            "Content-Range":"bytes 0-4095/10000000",
            "Content-Length":"4096",
        }
        for header, extra in (
            ("Content-Type", "text/html"),
            ("Content-Range", "bytes 0-4095/999999"),
            ("Content-Length", "8192"),
            ("Content-Encoding", "gzip"),
            ("Transfer-Encoding", "chunked"),
        ):
            hdr=Message()
            for k,v in pairs.items():
                hdr[k]=v
            if header == "Transfer-Encoding":
                hdr[header] = extra
            else:
                hdr[header] = extra
            response=FakeResponse(classic(),headers=hdr)
            with self.subTest(header=header), self.assertRaises(
                jrc.OriginalPrefixBlocked
            ):
                jrc.probe_original_prefix(p,c,open_request=lambda *_:response)
            self.assertEqual(response.read_sizes,[])

    def test_duplicate_case_insensitive_dict_headers_fail_closed(self):
        p,c=hypothetical_review(self.policy,self.contract)
        headers={
            "Content-Type":"image/tiff",
            "Content-Range":"bytes 0-4095/10000000",
            "content-range":"bytes 0-4095/999999",
            "Content-Length":"4096",
        }
        response=FakeResponse(classic(),headers=headers)
        with self.assertRaisesRegex(jrc.OriginalPrefixBlocked, "duplicate"):
            jrc.probe_original_prefix(p,c,open_request=lambda *_:response)
        self.assertEqual(response.read_sizes,[])

    def test_original_release_identity_not_proved_by_any_syntactic_206(self):
        p,c=hypothetical_review(self.policy,self.contract)
        reply=FakeResponse(classic())
        result=jrc.probe_original_prefix(p,c,open_request=lambda *_:reply)
        self.assertTrue(result["http_206_exact_requested_url_and_range_observed"])
        self.assertTrue(result["range_response_verified"])
        self.assertFalse(result["original_provider_source_identity_verified"])
        self.assertFalse(result["original_asset_release_identity_independently_verified"])
        self.assertFalse(result["post_2026_11_10_correction_verified"])
        self.assertFalse(result["model_input_approved"])

    def test_short_long_or_invalid_tiff_body_blocked_without_source_admission(self):
        p, c = hypothetical_review(self.policy, self.contract)
        for raw in (b"", b"not tiff", classic()[:4095],
                    bytes(jrc.PREFIX_BYTES)):
            with self.subTest(n=len(raw)), self.assertRaises(jrc.OriginalPrefixBlocked):
                jrc.probe_original_prefix(p,c,
                    open_request=lambda *_:FakeResponse(raw))

    def test_even_server_oversends_body_no_extra_original_bytes_are_read(self):
        # HTTP206 and declared Content-Length are checked *before* reading.
        # An untrusted transport could send trailing bytes beyond the
        # declared range: our bounded consumer never acquires them.
        p,c=hypothetical_review(self.policy,self.contract)
        response=FakeResponse(classic()+b"not-authorized")
        meta=jrc.probe_original_prefix(p,c,open_request=lambda *_:response)
        self.assertEqual(response.read_sizes,[4096])
        self.assertTrue(meta["original_prefix_sha_only_not_full_asset"])
        self.assertIsNone(meta["original_asset_whole_file_sha256"])
        self.assertFalse(meta["model_input_approved"])

    def test_http429_and_network_error_not_retried(self):
        p,c=hypothetical_review(self.policy,self.contract)
        times=[]
        def one_failure(req,timeout):
            times.append(req.full_url)
            raise error.HTTPError(req.full_url,429,"too many requests",{},None)
        with self.assertRaises(jrc.OriginalPrefixBlocked):
            jrc.probe_original_prefix(p,c,open_request=one_failure)
        self.assertEqual(times,[jrc.SOURCE_URL])

    def test_cli_and_default_network_gate_do_not_allow_arbitrary_endpoint(self):
        with self.assertRaises(SystemExit):
            jrc.main([])
        code = jrc.Path(jrc.__file__).read_text(encoding="utf-8")
        self.assertNotIn("request.urlopen(",code)
        self.assertNotIn("requests.get(",code)
        self.assertNotIn("follow_redirects=True",code)
        self.assertIn("ProxyHandler({})",code)
        self.assertIn("NoRedirect()",code)
        self.assertIn("read(PREFIX_BYTES)",code)
        self.assertNotIn("open(",code.split("def probe_original_prefix(",1)[1].split("def main(",1)[0].replace("open_request(", ""))


if __name__ == "__main__":
    unittest.main()
