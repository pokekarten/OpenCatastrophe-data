# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline fail-closed tests; original DLR TIFF bytes are never fixture-committed."""
import hashlib
import unittest
from pathlib import Path

from scripts.validate_source_access import validate_path

from scripts.probe_dlr_wsf_native_cog_tile_v0 import (
    HEADER_SIZE, HEADER_SHA256, LZW_CLEAR, LZW_EOI, NATIVE_TILE_BYTES,
    NATIVE_TILE_INDEX, NATIVE_TILE_OFFSET, NATIVE_TILE_SHA256,
    SOURCE, URL, WINDOWS, NativeCOGBlocked, NoRedirect,
    _fetch_range, decode_tiff_lzw, inspect_tile, parse_native_header,
)


def pack_codes_9(codes):
    bits = "".join(f"{code:09b}" for code in codes)
    bits += "0" * ((8 - len(bits) % 8) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


class DLRNativeCogTests(unittest.TestCase):
    def test_frozen_byte_ranges_and_source_identity(self):
        self.assertEqual(SOURCE, "dlr.wsf.2019")
        self.assertEqual(URL, "https://download.geoservice.dlr.de/WSF2019/files/WSF2019_v1_10_48.tif")
        self.assertEqual((NATIVE_TILE_INDEX, NATIVE_TILE_OFFSET, NATIVE_TILE_BYTES),
                         (1793, 12156322, 24659))
        self.assertEqual(HEADER_SIZE, 32768)
        self.assertEqual(len(HEADER_SHA256), 64)
        self.assertEqual(len(NATIVE_TILE_SHA256), 64)
        for start, size in ((100, 200), (0, 100), (NATIVE_TILE_OFFSET, 262144)):
            with self.assertRaises(NativeCOGBlocked):
                _fetch_range(start, size)

    def test_wsf2019_canonical_original_access_contract_is_document_only(self):
        path = Path(__file__).resolve().parents[1] / "access" / "dlr.wsf.2019.native-geotiff.json"
        contract = validate_path(path)
        self.assertEqual(contract["source_ids"], [SOURCE])
        self.assertEqual(contract["interface_type"], "http_file")
        self.assertEqual(contract["status"], "documented_only")
        self.assertEqual(contract["service_root"] + contract["request_contract"]["path_templates"][0], URL)
        self.assertEqual(contract["authentication"]["mode"], "none")
        self.assertEqual(contract["probe_contract"], {
            "mode": "none", "operation": None,
            "requires_credentials": False, "expected_evidence": [],
        })
        self.assertEqual(contract["rights_and_policy"]["dataset_rights_status"], "verified")
        self.assertEqual(contract["rights_and_policy"]["api_terms_status"], "unknown")
        self.assertEqual(contract["rights_and_policy"]["commercial_automation_status"], "unknown")
        self.assertEqual(contract["implementation_decision"], "document_only")
        self.assertEqual(contract["operational_constraints"]["max_probe_bytes"], HEADER_SIZE)
        self.assertEqual(contract["operational_constraints"]["max_sample_bytes"],
                         HEADER_SIZE + NATIVE_TILE_BYTES)
        self.assertIn(f"bytes={NATIVE_TILE_OFFSET}-{NATIVE_TILE_OFFSET + NATIVE_TILE_BYTES - 1}",
                      contract["request_contract"]["parameter_rules"])
        self.assertIn(HEADER_SHA256, contract["operational_constraints"]["mutability_notes"])
        self.assertIn(NATIVE_TILE_SHA256, contract["operational_constraints"]["mutability_notes"])
        self.assertIn("NOT the full GeoTIFF SHA-256",
                      contract["operational_constraints"]["mutability_notes"])
        self.assertIn("not individual buildings",
                      contract["response_contract"]["scientific_semantics"])

    def test_tiff_lzw_msb_code_decoding_early_clear_and_eoi(self):
        compressed = pack_codes_9([LZW_CLEAR, 0, 255, LZW_EOI])
        self.assertEqual(decode_tiff_lzw(compressed, max_output=2), bytes([0, 255]))
        compressed = pack_codes_9([LZW_CLEAR, 65, 66, LZW_CLEAR, 255, 0, LZW_EOI])
        self.assertEqual(decode_tiff_lzw(compressed, max_output=4), b"AB\xff\x00")

    def test_bounded_lzw_rejects_corruption_and_inflation(self):
        valid = pack_codes_9([LZW_CLEAR, 0, 255, LZW_EOI])
        for payload, maximum in (
            (valid, 1),
            (valid[:-1], 2),
            (b"", 2),
            (valid, 262145),
            (pack_codes_9([0, 255, LZW_EOI]), 2),
        ):
            with self.subTest(size=len(payload), maximum=maximum):
                with self.assertRaises(NativeCOGBlocked):
                    decode_tiff_lzw(payload, max_output=maximum)

    def test_corrupt_or_wrong_tiff_rejected_before_geotiff_use(self):
        for original in (b"", b"\x00" * HEADER_SIZE,
                         b"MM\x00\x2a" + b"\x00" * (HEADER_SIZE - 4),
                         b"II\x2a\x00" + b"\x00" * (HEADER_SIZE - 4)):
            with self.assertRaises(NativeCOGBlocked):
                parse_native_header(original)
        with self.assertRaises(NativeCOGBlocked):
            inspect_tile(b"not original compressed source", {})

    def test_only_two_exact_native_windows_and_no_provider_byte_logging(self):
        self.assertEqual(set(WINDOWS), {"nonsettlement", "mixed"})
        self.assertEqual(WINDOWS["nonsettlement"]["tile_xy"], (448, 432))
        self.assertEqual(WINDOWS["mixed"]["tile_xy"], (464, 464))
        self.assertEqual(WINDOWS["nonsettlement"]["expected_255"], 0)
        self.assertEqual(WINDOWS["mixed"]["expected_255"], 482)
        for window in WINDOWS.values():
            self.assertEqual(len(window["rows_sha256"]), len(hashlib.sha256(b"").hexdigest()))

    def test_source_redirect_is_denied(self):
        with self.assertRaises(NativeCOGBlocked):
            NoRedirect().redirect_request(None, None, 302, "move", {},
                                          "https://other.example/original.tif")


if __name__ == "__main__":
    unittest.main()
