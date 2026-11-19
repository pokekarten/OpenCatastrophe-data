# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Wholly synthetic adversarial tests for the original-source code-only join gate."""
from __future__ import annotations

import csv
import io
import json
import struct
import unittest
import zipfile

from research_runners.materialcities_bkg_gadm_2022_code_crosswalk_v0 import (
    CodeCrosswalkError, _bkg_codes, _source_zip, _gadm_features, _materialcities_gids,
    inspect_exact_sources, reconcile_codes,
)


def _toy():
    # Artificial source identities, NEVER measurements or insurer locations.
    gadm = [
        {"gid": "DEU.1.1_1", "code": "01001"},
        {"gid": "DEU.1.2_1", "code": "03152"},
        {"gid": "DEU.1.3_1", "code": "03156"},
        {"gid": "DEU.1.4_1", "code": "16063"},
        {"gid": "DEU.1.6_1", "code": "16056"},
        {"gid": "DEU.1.5_1", "code": "NA"},
    ]
    return (["01001", "03159", "16063", "01001"], gadm,
            [r["gid"] for r in gadm if r["code"] != "NA"],
            {"01001", "03159", "16063"})


def _dbf(keys):
    # Real dBASE header shapes but synthetic, no physical geometry or source rows.
    fields = [("AGS", 5), ("GEN", 20), ("BEGINN", 8)]
    width = 1 + sum(n for _, n in fields)
    header = 32 + 32 * len(fields) + 1
    out = bytearray(header + width * len(keys) + 1)
    out[0] = 3
    struct.pack_into("<I", out, 4, len(keys))
    struct.pack_into("<H", out, 8, header)
    struct.pack_into("<H", out, 10, width)
    for i, (name, length) in enumerate(fields):
        off = 32 + 32 * i
        out[off:off + 11] = name.encode("ascii").ljust(11, b"\0")
        out[off + 11] = ord("C")
        out[off + 16] = length
    out[header - 1] = 13
    for i, key in enumerate(keys):
        p = header + i * width
        out[p] = 32
        payload = key.ljust(5) + "ToyDistrict".ljust(20) + "20221231"
        out[p + 1:p + width] = payload.encode("ascii")
    out[-1] = 26
    return bytes(out)


def _zip(members):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, content in members.items():
            z.writestr(name, content)
    return buffer.getvalue()


def _toy_sources():
    bkg, gadm, mc, zensus = _toy()
    bb = _zip({"dummy/VG250_KRS.dbf": _dbf(bkg)})
    gj = {"type": "FeatureCollection",
          "features": [{"type": "Feature", "properties": {
              "GID_0": "DEU", "GID_2": row["gid"], "CC_2": row["code"]}}
              for row in gadm]}
    gb = _zip({"gadm41_DEU_2.json": json.dumps(gj).encode()})
    buff = io.StringIO()
    writer = csv.DictWriter(buff, fieldnames=["GID_0", "GID_2", "GFA_NR_C"])
    writer.writeheader()
    for gid in mc:
        writer.writerow({"GID_0": "DEU", "GID_2": gid, "GFA_NR_C": "100"})
    mb = _zip({"MaterialCities_adm_gfa_ADM2.csv": buff.getvalue().encode()})
    original = ("schema_version = \"ZENSUS2022_400_KREIS_ORIGINAL_BUILDING_AGGREGATES_V0\"\n"
                "original_full_file_sha256 = \"82da8578a4657e20752b436a756ed27846c77f96e3f7333bdea7f4fe29a8b551\"\n"
                "source_event_date = \"2022-05-15\"\n" +
                "\n".join("[[kreise]]\nags = \"" + k + "\"" for k in sorted(zensus)) + "\n")
    return bb, gb, mb, original.encode()


class GermanOriginalCodeCrosswalkTests(unittest.TestCase):
    def test_semantic_mapping_is_complete_but_never_a_spatial_join(self):
        report = reconcile_codes(*_toy(), original_counts=False)
        self.assertEqual(report["source_bkg_2022_shape_rows"], 4)
        self.assertEqual(report["source_bkg_distinct_official_ags"], 3)
        self.assertEqual(report["gadm_valid_unique_cc2_exact_2022_ags_matches"], 2)
        self.assertEqual(report["historical_obsolete_ags_codes_needing_review"], 3)
        self.assertEqual(report["candidate_2022_ags_targets_reached_by_all_source_codes"], 3)
        self.assertEqual(report["multiple_historical_source_codes_to_2022_target_groups"], 2)
        self.assertTrue(report["source_bkg_zensus_2022_ags_identity_exact"])
        self.assertTrue(report["same_ags_not_proof_same_polygons"])
        for key in ("gadm_bkg_geometry_overlap_proven",
                    "source_vintages_spatially_equivalent",
                    "materialcities_to_official_ags_join_admitted",
                    "source_commercial_rights_cleared",
                    "original_provider_geometry_or_crosswalk_exported",
                    "real_insurer_exposures_inferred"):
            self.assertFalse(report[key])
        self.assertTrue(report["research_only"])

    def test_original_release_counts_block_fictional_sources(self):
        with self.assertRaisesRegex(CodeCrosswalkError, "version-pinned"):
            reconcile_codes(*_toy(), original_counts=True)

    def test_2022_bkg_census_exact_roster_required(self):
        b, g, m, _ = _toy()
        with self.assertRaisesRegex(CodeCrosswalkError, "rosters differ"):
            reconcile_codes(b, g, m, {"01001", "16063"}, original_counts=False)

    def test_unreviewed_obsolete_code_blocked(self):
        b, g, m, c = _toy()
        g[2]["code"] = "99999"
        with self.assertRaisesRegex(CodeCrosswalkError, "unreviewed historical"):
            reconcile_codes(b, g, m, c, original_counts=False)

    def test_materialcities_id_missing_in_gadm_blocked(self):
        b, g, m, c = _toy()
        m[0] = "DEU.10.99_1"
        with self.assertRaisesRegex(CodeCrosswalkError, "GID missing"):
            reconcile_codes(b, g, m, c, original_counts=False)

    def test_materialcities_duplicate_identity_blocked(self):
        b, g, m, c = _toy()
        m.append(m[0])
        with self.assertRaisesRegex(CodeCrosswalkError, "GID missing/duplicate"):
            reconcile_codes(b, g, m, c, original_counts=False)

    def test_gadm_uncoded_feature_cannot_be_materialcities_region(self):
        b, g, m, c = _toy()
        m.append("DEU.1.5_1")
        with self.assertRaisesRegex(CodeCrosswalkError, "unmappable"):
            reconcile_codes(b, g, m, c, original_counts=False)

    def test_gadm_coded_feature_missing_from_materialcities_blocked(self):
        b, g, m, c = _toy()
        m.remove(m[0])
        with self.assertRaisesRegex(CodeCrosswalkError, "coded GADM feature absent"):
            reconcile_codes(b, g, m, c, original_counts=False)

    def test_two_materialcities_regions_cannot_share_one_source_cc2(self):
        b, g, m, c = _toy()
        g[1]["code"] = "03156"
        with self.assertRaisesRegex(CodeCrosswalkError, "ambiguous"):
            reconcile_codes(b, g, m, c, original_counts=False)

    def test_target_roster_has_to_be_fully_reached(self):
        b, g, m, c = _toy()
        b.append("99998")
        c.add("99998")
        with self.assertRaisesRegex(CodeCrosswalkError, "target coverage incomplete"):
            reconcile_codes(b, g, m, c, original_counts=False)

    def test_source_zip_rejects_path_traversal(self):
        with self.assertRaisesRegex(CodeCrosswalkError, "unsafe ZIP"):
            with _source_zip(_zip({"../unsafe.txt": "bad"}), "GADM", "", exact_pin=False):
                pass

    def test_dbf_parser_preserves_leading_zero_and_duplicate_geometry_pieces(self):
        keys, *_ = _toy()
        got, count = _bkg_codes(_dbf(keys))
        self.assertEqual(got, keys)
        self.assertEqual(count, 4)
        self.assertEqual(len(set(got)), 3)

    def test_dbf_parser_rejects_invalid_ags(self):
        with self.assertRaisesRegex(CodeCrosswalkError, "five-digit"):
            _bkg_codes(_dbf(["0ABCD"]))

    def test_gadm_geojson_requires_german_original_cc2(self):
        data = {"type": "FeatureCollection", "features": [
            {"properties": {"GID_0": "DEU", "GID_2": "DEU.1.1_1", "CC_2": "NO"}}]}
        with self.assertRaisesRegex(CodeCrosswalkError, "CC2"):
            _gadm_features(data)

    def test_materialcities_csv_does_not_accept_unreviewed_schema(self):
        with self.assertRaisesRegex(CodeCrosswalkError, "schema"):
            _materialcities_gids(b"GID_0,GFA_NR_C\nDEU,23\n")

    def test_full_synthetic_zip_pipeline_executes_without_geography_admission(self):
        r = inspect_exact_sources(*_toy_sources(), exact_pin=False, original_counts=False)
        self.assertEqual(r["historical_obsolete_ags_codes_needing_review"], 3)
        self.assertEqual(r["candidate_2022_ags_targets_reached_by_all_source_codes"], 3)
        self.assertEqual(len(r["original_sha256"]), 3)
        self.assertFalse(r["materialcities_to_official_ags_join_admitted"])
        self.assertFalse(r["source_commercial_rights_cleared"])

    def test_original_pins_refuse_any_synthetic_zip(self):
        with self.assertRaisesRegex(CodeCrosswalkError, "original SHA256 changed"):
            inspect_exact_sources(*_toy_sources())

    def test_no_forged_census_source_identity(self):
        b, g, m, z = _toy_sources()
        with self.assertRaisesRegex(CodeCrosswalkError, "original source identity"):
            inspect_exact_sources(b, g, m, z.replace(b"2022-05-15", b"2025-01-01"),
                                  exact_pin=False, original_counts=False)


if __name__ == "__main__":
    unittest.main()
