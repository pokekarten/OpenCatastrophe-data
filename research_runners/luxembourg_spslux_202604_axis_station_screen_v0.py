# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only screen against published ACT SPSLux LUREF reference stations.

* This checks the conventional EPSG:2169 *coordinate interpretation*.
* It does NOT inspect or ground-control ACT2026 building GeoPackage objects.
* Published ITRF2020 @ 2025.83 longitude/latitude are NOT a current
  official direct WGS84-to-LURES conversion. Datum and epoch matter.
* The LUREF2020 -> LUREF2025 effective-date change on 2026-10-31 is
  not silently treated as a coordinate-system regression or ignored.
* No observed station coordinate or derived individual location is emitted.
"""
from __future__ import annotations

import json
import math
import statistics

OFFICIAL_PDF = ("https://act.public.lu/content/dam/act/fr/publications/"
                "documents-techniques/202604-dtech-coordinates-reference-station.pdf")
OFFICIAL_FRAME_INFO = ("https://act.public.lu/fr/gps-reseaux/spslux1/"
                       "spsluxgeodeticdatum.html")
ORIGINAL_SOURCE_RELEASE = "2026-10-01"
FRAME_TRANSITION_DATE = "2026-10-31"
# Fixed, non-personal national GNSS station reference points, ACT April 2026
# published table. Columns: site code, ITRF2020 @2025.83 longitude/latitude
# (publication calls this WGS84), LUREF LTM easting/northing in metres.
# These factual coordinates are *station observations*, not buildings.
STATIONS = (
    ("BASC", 5.939268402, 49.567938522, 63444.851, 70387.364),
    ("ECH2", 6.443104868, 49.803055276, 99794.700, 96549.497),
    ("ERPL", 6.323182598, 49.547792172, 91220.576, 68133.384),
    ("KBG2", 6.159481924, 49.625428187, 79375.025, 76756.545),
    ("ROUL", 5.917815811, 49.951423710, 62034.771, 113045.443),
    ("TROS", 6.007300152, 50.126737907, 68498.645, 132528.176),
    ("WALF", 6.131583885, 49.658142955, 77361.065, 80395.766),
)
MAX_NATIVE_PLAUSIBILITY_METRES = 20.0
MIN_SWAPPED_REJECTION_METRES = 1000.0


class StationScreenError(ValueError):
    """Misidentified control points or an implausible coordinate-order result."""


def screen(stations: tuple = STATIONS) -> dict:
    """Compare published sites under both axes using pinned pyproj/PROJ.

    The tolerance is deliberately DECAMETRE-scale, not ground-survey accuracy.
    WGS84/ITRF2020 and ETRF frame differences/epochs limit direct residual
    interpretation.  No station-by-station coordinate or residual is output.
    """
    try:
        from pyproj import Transformer, Geod, __version__ as pyproj_version
    except ImportError as exc:
        raise StationScreenError("Requires reviewed pyproj spatial dependency") from exc
    if not isinstance(stations, (tuple, list)) or len(stations) < 3 or len(stations) > 15:
        raise StationScreenError("Require at least three bounded independently published controls")
    codes = set()
    for site in stations:
        if (not isinstance(site, (tuple, list)) or len(site) != 5
                or not isinstance(site[0], str) or len(site[0]) != 4
                or site[0] in codes
                or any(type(v) not in (int, float) or not math.isfinite(v) for v in site[1:])
                or not (5.65 <= site[1] <= 6.6 and 49.35 <= site[2] <= 50.25)
                or not (45000 <= site[3] <= 110000 and 54000 <= site[4] <= 140000)):
            raise StationScreenError("Malformed, duplicate or implausible official control")
        codes.add(site[0])
    to_geographic = Transformer.from_crs(2169, 4326, always_xy=True)
    geodesic = Geod(ellps="WGS84")
    native_residuals = []
    swapped_residuals = []
    for _, lon, lat, east, north in stations:
        for swapped, out in ((False, native_residuals), (True, swapped_residuals)):
            x, y = (north, east) if swapped else (east, north)
            result_lon, result_lat = to_geographic.transform(x, y)
            if not all(math.isfinite(v) for v in (result_lon, result_lat)):
                raise StationScreenError("Nonfinite transformed published control")
            residual = geodesic.inv(lon, lat, result_lon, result_lat)[2]
            if not math.isfinite(residual) or residual < 0:
                raise StationScreenError("Invalid control residual")
            out.append(residual)
    native_max = max(native_residuals)
    swapped_min = min(swapped_residuals)
    if native_max > MAX_NATIVE_PLAUSIBILITY_METRES or swapped_min <= MIN_SWAPPED_REJECTION_METRES:
        raise StationScreenError("Official stations do not support assumed EPSG:2169 axis order")
    return {
        "profile": "lu-act-spslux-202604-epsg2169-frame-aware-station-screen-v0",
        "source": OFFICIAL_PDF,
        "official_frame_guidance": OFFICIAL_FRAME_INFO,
        "source_published_month": "2026-04",
        "station_coordinates_reference_epoch": "ITRF2020 @ 2025.83 (publication uses approximate WGS84)",
        "luref_station_coordinates_reference": "ACT 2026-04 published LUREF LTM",
        "station_control_points": len(native_residuals),
        "original_geobase_release_date": ORIGINAL_SOURCE_RELEASE,
        "luref2025_effective_date": FRAME_TRANSITION_DATE,
        "official_direct_wgs84_to_lures_transform_exists": False,
        "station_native_xy_max_residual_m_rounded_1dp": round(native_max, 1),
        "station_native_xy_median_residual_m_rounded_1dp": round(statistics.median(native_residuals), 1),
        "station_swapped_xy_min_residual_m_rounded_1dp": round(swapped_min, 1),
        "native_xy_plausible_for_published_stations": True,
        "swapped_xy_rejected_for_published_stations": True,
        "pyproj_version": pyproj_version,
        "station_frame_epoch_tied_to_geobase_original_proven": False,
        "individual_geobase_geometry_axis_ground_control_verified": False,
        "source_building_position_or_accuracy_verified": False,
        "source_building_geometries_ingested": False,
        "CAT_model_input_admitted": False,
        "warning": "Only external published GNSS reference station plausibility. Not an observed "
                   "building ground-control point, cadastral footprint accuracy test, "
                   "certified epoch-specific ITRF/WGS84-to-LUREF conversion or source-admission gate.",
    }


def main() -> int:
    try:
        print(json.dumps(screen(), indent=2, sort_keys=True, allow_nan=False))
    except StationScreenError as exc:
        raise SystemExit("BLOCKED: " + str(exc)) from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
