# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "profile_esrm20_scenario_v10_greece_shakemap.py"
)
SPEC = importlib.util.spec_from_file_location("profile_shakemap", MODULE_PATH)
assert SPEC and SPEC.loader
profile = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = profile
SPEC.loader.exec_module(profile)


def _xml(
    fields,
    rows,
    *,
    event_id="Greece_07-9-1999",
    namespace="",
    nlon=2,
    nlat=2,
    encoding="UTF-8",
    extra_root="",
    spacing="1.0",
):
    ns = f' xmlns="{namespace}"' if namespace else ""
    root_attrs = (
        f'event_id="{event_id}" shakemap_id="{event_id}" shakemap_version="1" '
        f'code_version="3.5" shakemap_originator="us" map_status="RELEASED" '
        f'shakemap_event_type="SCENARIO" {extra_root}'
    ).strip()
    field_text = "\n".join(
        f'  <grid_field index="{idx}" name="{name}" units="{units}" />'
        for idx, name, units in fields
    )
    row_text = "\n".join(" ".join(map(str, row)) for row in rows)
    return (
        f'<?xml version="1.0" encoding="{encoding}"?>\n'
        f'<shakemap_grid{ns} {root_attrs}>\n'
        '  <event magnitude="5.9" lat="0" lon="0" />\n'
        f'  <grid_specification lon_min="10" lat_min="20" lon_max="11" lat_max="21" '
        f'nominal_lon_spacing="{spacing}" nominal_lat_spacing="{spacing}" '
        f'nlon="{nlon}" nlat="{nlat}" />\n'
        f"{field_text}\n"
        f"  <grid_data>\n{row_text}\n  </grid_data>\n"
        "</shakemap_grid>\n"
    ).encode("ascii")


GRID_FIELDS = [
    (1, "LON", "dd"),
    (2, "LAT", "dd"),
    (3, "PGA", "pctg"),
    (4, "PGV", "cms"),
    (5, "MMI", "intensity"),
    (6, "PSA03", "pctg"),
    (7, "PSA10", "pctg"),
    (8, "PSA30", "pctg"),
    (9, "SVEL", "ms"),
]
UNC_FIELDS = [
    (1, "LON", "dd"),
    (2, "LAT", "dd"),
    (3, "STDPGA", "ln(pctg)"),
    (4, "STDPGV", "ln(cms)"),
    (5, "STDMMI", "intensity"),
    (6, "STDPSA03", "ln(pctg)"),
    (7, "STDPSA10", "ln(pctg)"),
    (8, "STDPSA30", "ln(pctg)"),
]
COORDS = [(10, 21), (11, 21), (10, 20), (11, 20)]
GRID_ROWS = [tuple(c) + (1, 2, 3, 4, 5, 6, 760) for c in COORDS]
UNC_ROWS = [tuple(c) + (0.5, 0.6, 0.7, 0.8, 0.9, 1.0) for c in COORDS]


def _call(grid=None, uncertainty=None, **kwargs):
    grid = grid if grid is not None else _xml(GRID_FIELDS, GRID_ROWS)
    uncertainty = uncertainty if uncertainty is not None else _xml(UNC_FIELDS, UNC_ROWS)
    defaults = dict(
        grid_expected_byte_count=len(grid),
        grid_expected_sha256=hashlib.sha256(grid).hexdigest(),
        uncertainty_expected_byte_count=len(uncertainty),
        uncertainty_expected_sha256=hashlib.sha256(uncertainty).hexdigest(),
        expected_event_id="Greece_07-9-1999",
        max_fields=32,
        max_rows=100,
        max_columns=32,
        max_xml_bytes=100_000,
    )
    defaults.update(kwargs)
    return profile._profile_verified_greece_shakemap_pair(grid, uncertainty, **defaults)


class ShakeMapProfileTests(unittest.TestCase):
    def test_production_identity_constants_match_trusted_receipt(self):
        self.assertEqual(profile.GRID_BYTE_COUNT, 5_290_966)
        self.assertEqual(
            profile.GRID_SHA256,
            "3c2fe7a2a7182fac999442ce3d88ddfd99004b7f999462ef2327f2eebc1ccd9f",
        )
        self.assertEqual(profile.UNCERTAINTY_BYTE_COUNT, 5_340_320)
        self.assertEqual(
            profile.UNCERTAINTY_SHA256,
            "eb08df5ff78f265fb45bf31dbd3dddf4f01bf10632382d4156a2bdf016e46417",
        )
        self.assertEqual(profile.EVENT_ID, "Greece_07-9-1999")

    def test_happy_path_profiles_present_openquake_imts_without_sa06_invention(self):
        result = _call()
        self.assertEqual(
            result["schema_version"],
            "oc-esrm20-scenario-v10-greece-shakemap-profile-v1",
        )
        self.assertEqual(result["receipt_event_id"], "Greece_07-9-1999")
        self.assertEqual(
            result["openquake_3_12_1_paired_imts"],
            ["MMI", "PGA", "SA(0.3)", "SA(1.0)", "SA(3.0)"],
        )
        self.assertNotIn("SA(0.6)", result["openquake_3_12_1_paired_imts"])
        self.assertEqual(result["grid"]["ignored_fields"], ["PGV", "SVEL"])
        self.assertEqual(result["uncertainty"]["ignored_fields"], ["STDPGV"])
        self.assertTrue(result["coordinate_grids_equal"])
        self.assertEqual(result["grid"]["observed_row_count"], 4)
        self.assertEqual(
            result["grid"]["coordinate_sha256"],
            result["uncertainty"]["coordinate_sha256"],
        )
        for flag in (
            "event_location_inference_authorized",
            "scenario_selection_authorized",
            "independent_validation_established",
            "holdout_status_established",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertFalse(result[flag])

    def test_us_ascii_declaration_is_accepted(self):
        grid = _xml(GRID_FIELDS, GRID_ROWS, encoding="US-ASCII")
        uncertainty = _xml(UNC_FIELDS, UNC_ROWS, encoding="US-ASCII")
        self.assertTrue(_call(grid, uncertainty)["provider_file_content_profiled"])

    def test_namespace_must_match_across_pair(self):
        grid = _xml(GRID_FIELDS, GRID_ROWS, namespace="urn:one")
        uncertainty = _xml(UNC_FIELDS, UNC_ROWS, namespace="urn:two")
        with self.assertRaisesRegex(profile.ShakeMapProfileError, "shakemap_namespace_mismatch"):
            _call(grid, uncertainty)

    def test_root_event_ids_must_match_each_other_but_not_receipt_identity(self):
        grid = _xml(GRID_FIELDS, GRID_ROWS, event_id="provider-event")
        uncertainty = _xml(UNC_FIELDS, UNC_ROWS, event_id="other-provider-event")
        with self.assertRaisesRegex(
            profile.ShakeMapProfileError, "shakemap_event_id_pair_mismatch"
        ):
            _call(grid, uncertainty)
        uncertainty = _xml(UNC_FIELDS, UNC_ROWS, event_id="provider-event")
        result = _call(grid, uncertainty)
        self.assertEqual(result["metadata"]["event_id"], "provider-event")
        self.assertEqual(result["receipt_event_id"], "Greece_07-9-1999")

    def test_shakemap_ids_must_match_across_pair(self):
        grid = _xml(
            GRID_FIELDS,
            GRID_ROWS,
            event_id="provider-event",
        )
        uncertainty = _xml(
            UNC_FIELDS,
            UNC_ROWS,
            event_id="provider-event",
        ).replace(
            b'shakemap_id="provider-event"',
            b'shakemap_id="other-map"',
            1,
        )
        with self.assertRaisesRegex(
            profile.ShakeMapProfileError, "shakemap_id_pair_mismatch"
        ):
            _call(grid, uncertainty)

    def test_duplicate_or_gapped_field_indexes_fail_closed(self):
        duplicate = list(GRID_FIELDS)
        duplicate[3] = (3, "PGV", "cms")
        with self.assertRaisesRegex(profile.ShakeMapProfileError, "duplicate_grid_field_index"):
            _call(_xml(duplicate, GRID_ROWS))
        gapped = [(1, "LON", "dd"), (3, "LAT", "dd")]
        rows = [(10, 21), (11, 21), (10, 20), (11, 20)]
        with self.assertRaisesRegex(profile.ShakeMapProfileError, "gapped_grid_field_indexes"):
            _call(_xml(gapped, rows))

    def test_duplicate_field_name_fails_closed(self):
        duplicate_name = [
            (1, "LON", "dd"),
            (2, "LAT", "dd"),
            (3, "PGA", "pctg"),
            (4, "PGA", "pctg"),
        ]
        rows = [(10, 21, 1, 2)] * 4
        with self.assertRaisesRegex(profile.ShakeMapProfileError, "duplicate_grid_field_name"):
            _call(_xml(duplicate_name, rows))

    def test_unsupported_name_or_unit_fails_closed(self):
        bad_name = [(1, "LON", "dd"), (2, "LAT", "dd"), (3, "SECRET", "pctg")]
        rows = [(10, 21, 1)] * 4
        with self.assertRaisesRegex(profile.ShakeMapProfileError, "unsupported_grid_field_name"):
            _call(_xml(bad_name, rows))
        bad_unit = list(GRID_FIELDS)
        bad_unit[2] = (3, "PGA", "g")
        with self.assertRaisesRegex(profile.ShakeMapProfileError, "unsupported_grid_field_units"):
            _call(_xml(bad_unit, GRID_ROWS))

    def test_non_finite_and_wrong_width_rows_fail_closed(self):
        bad_rows = list(GRID_ROWS)
        bad_rows[0] = tuple(bad_rows[0][:-1]) + (float("nan"),)
        with self.assertRaisesRegex(
            profile.ShakeMapProfileError, "non_finite_grid_numeric_token"
        ):
            _call(_xml(GRID_FIELDS, bad_rows))
        narrow = list(GRID_ROWS)
        narrow[0] = tuple(narrow[0][:-1])
        with self.assertRaisesRegex(profile.ShakeMapProfileError, "grid_row_width_mismatch"):
            _call(_xml(GRID_FIELDS, narrow))

    def test_declared_cardinality_must_equal_observed_rows(self):
        grid = _xml(GRID_FIELDS, GRID_ROWS[:3])
        with self.assertRaisesRegex(profile.ShakeMapProfileError, "grid_row_count_mismatch"):
            _call(grid)

    def test_specification_mismatch_fails_closed(self):
        uncertainty = _xml(UNC_FIELDS, UNC_ROWS, spacing="0.5")
        with self.assertRaisesRegex(profile.ShakeMapProfileError, "grid_specification_mismatch"):
            _call(uncertainty=uncertainty)

    def test_coordinate_mismatch_fails_closed_without_raw_coordinates(self):
        rows = list(UNC_ROWS)
        rows[2] = (10.5, 20) + tuple(rows[2][2:])
        with self.assertRaisesRegex(profile.ShakeMapProfileError, "coordinate_grid_mismatch"):
            _call(uncertainty=_xml(UNC_FIELDS, rows))

    def test_dtd_and_non_utf8_declarations_fail_closed(self):
        grid = _xml(GRID_FIELDS, GRID_ROWS).replace(
            b"<shakemap_grid",
            b'<!DOCTYPE x [<!ENTITY y "z">]>\n<shakemap_grid',
            1,
        )
        with self.assertRaisesRegex(profile.ShakeMapProfileError, "dtd_or_entity_forbidden"):
            _call(grid)
        grid = _xml(GRID_FIELDS, GRID_ROWS, encoding="ISO-8859-1")
        with self.assertRaisesRegex(
            profile.ShakeMapProfileError, "xml_encoding_declaration_mismatch"
        ):
            _call(grid)

    def test_identity_is_checked_before_xml_semantics(self):
        grid = b"not xml"
        uncertainty = _xml(UNC_FIELDS, UNC_ROWS)
        with self.assertRaisesRegex(profile.ShakeMapProfileError, "byte_count_mismatch"):
            profile._profile_verified_greece_shakemap_pair(
                grid,
                uncertainty,
                grid_expected_byte_count=999,
                grid_expected_sha256="0" * 64,
                uncertainty_expected_byte_count=len(uncertainty),
                uncertainty_expected_sha256=hashlib.sha256(uncertainty).hexdigest(),
                expected_event_id="Greece_07-9-1999",
            )

    def test_production_authority_drift_fails_before_payload_handling(self):
        with mock.patch.object(profile, "GRID_SHA256", "0" * 64):
            with self.assertRaisesRegex(
                profile.ShakeMapProfileError,
                "production_authority_drift:grid_sha256",
            ):
                profile.profile_fixed_greece_shakemap_pair(b"", b"")

    def test_profile_does_not_return_raw_grid_rows(self):
        result = _call()
        rendered = repr(result)
        self.assertNotIn("grid_data", rendered)
        self.assertNotIn(str(GRID_ROWS[0]), rendered)
        self.assertIn("coordinate_sha256", rendered)


if __name__ == "__main__":
    unittest.main()
