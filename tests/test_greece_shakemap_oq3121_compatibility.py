# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "profile_esrm20_scenario_v10_greece_shakemap.py"
)
SPEC = importlib.util.spec_from_file_location("profile_shakemap_oq3121_compat", MODULE_PATH)
assert SPEC and SPEC.loader
profile = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = profile
SPEC.loader.exec_module(profile)


def _xml(fields, rows):
    field_text = "\n".join(
        f'<grid_field index="{index}" name="{name}" units="{units}" />'
        for index, name, units in fields
    )
    row_text = "\n".join(" ".join(map(str, row)) for row in rows)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<shakemap_grid event_id="Greece_07-9-1999" '
        'shakemap_id="Greece_07-9-1999" shakemap_version="1" '
        'code_version="3.5" shakemap_originator="us" map_status="RELEASED" '
        'shakemap_event_type="SCENARIO">\n'
        '<event magnitude="5.9" lat="0" lon="0" />\n'
        '<grid_specification lon_min="10" lat_min="20" lon_max="11" lat_max="21" '
        'nominal_lon_spacing="1" nominal_lat_spacing="1" nlon="2" nlat="2" />\n'
        f'{field_text}\n<grid_data>\n{row_text}\n</grid_data>\n</shakemap_grid>\n'
    ).encode("ascii")


GRID_FIELDS = [(1, "LON", "dd"), (2, "LAT", "dd"), (3, "PGA", "pctg")]
UNCERTAINTY_FIELDS = [
    (1, "LON", "dd"),
    (2, "LAT", "dd"),
    (3, "STDPGA", "ln(pctg)"),
]
ROWS = [(10, 21, 1), (11, 21, 2), (10, 20, 3), (11, 20, 4)]


class GreeceShakeMapOq3121CompatibilityTests(unittest.TestCase):
    def test_generic_parser_still_rejects_nonstandard_pga_unit(self):
        fields = list(GRID_FIELDS)
        fields[2] = (3, "PGA", "g")
        root = ET.fromstring(_xml(fields, ROWS).decode("ascii"))
        with self.assertRaisesRegex(
            profile.ShakeMapProfileError,
            "unsupported_grid_field_units",
        ):
            profile._parse_fields(
                root,
                namespace="",
                allowed_units=profile._GRID_FIELD_UNITS,
                max_fields=32,
            )

    def test_compatibility_redacts_only_nonstandard_pga_unit(self):
        fields = list(GRID_FIELDS)
        fields[2] = (3, "PGA", "g")
        root = ET.fromstring(_xml(fields, ROWS).decode("ascii"))
        parsed = profile._parse_fields(
            root,
            namespace="",
            allowed_units=profile._GRID_FIELD_UNITS,
            max_fields=32,
            unit_metadata_ignored_fields=frozenset({"PGA"}),
        )
        self.assertEqual(parsed[2], (3, "PGA", "ignored_by_openquake_3_12_1"))
        self.assertNotIn("g", profile._GRID_FIELD_UNITS["PGA"])

    def test_documented_pctg_unit_is_not_redacted(self):
        root = ET.fromstring(_xml(GRID_FIELDS, ROWS).decode("ascii"))
        parsed = profile._parse_fields(
            root,
            namespace="",
            allowed_units=profile._GRID_FIELD_UNITS,
            max_fields=32,
            unit_metadata_ignored_fields=frozenset({"PGA"}),
        )
        self.assertEqual(parsed[2], (3, "PGA", "pctg"))

    def test_compatibility_does_not_widen_other_grid_fields(self):
        fields = [(1, "LON", "dd"), (2, "LAT", "dd"), (3, "PGV", "mystery")]
        root = ET.fromstring(_xml(fields, ROWS).decode("ascii"))
        with self.assertRaisesRegex(
            profile.ShakeMapProfileError,
            "unsupported_grid_field_units",
        ):
            profile._parse_fields(
                root,
                namespace="",
                allowed_units=profile._GRID_FIELD_UNITS,
                max_fields=32,
                unit_metadata_ignored_fields=frozenset({"PGA"}),
            )

    def test_compatibility_flag_requires_canonical_receipt_identity(self):
        grid = _xml(GRID_FIELDS, ROWS)
        uncertainty = _xml(UNCERTAINTY_FIELDS, ROWS)
        with self.assertRaisesRegex(
            profile.ShakeMapProfileError,
            "historical_compatibility_requires_canonical_identity",
        ):
            profile._profile_verified_greece_shakemap_pair(
                grid,
                uncertainty,
                grid_expected_byte_count=len(grid),
                grid_expected_sha256=hashlib.sha256(grid).hexdigest(),
                uncertainty_expected_byte_count=len(uncertainty),
                uncertainty_expected_sha256=hashlib.sha256(uncertainty).hexdigest(),
                expected_event_id="Greece_07-9-1999",
                historical_oq_3_12_1_compatibility=True,
            )

    def test_production_entry_enables_exact_oq3121_compatibility(self):
        with mock.patch.object(
            profile,
            "_profile_verified_greece_shakemap_pair",
            return_value={"ok": True},
        ) as wrapped:
            self.assertEqual(
                profile.profile_fixed_greece_shakemap_pair(b"grid", b"uncertainty"),
                {"ok": True},
            )
        kwargs = wrapped.call_args.kwargs
        self.assertTrue(kwargs["historical_oq_3_12_1_compatibility"])
        self.assertEqual(kwargs["grid_expected_sha256"], profile.GRID_SHA256)
        self.assertEqual(
            kwargs["uncertainty_expected_sha256"],
            profile.UNCERTAINTY_SHA256,
        )


if __name__ == "__main__":
    unittest.main()
