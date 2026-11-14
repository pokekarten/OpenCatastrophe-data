<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Germany wind hazard map export

The runner exports original SHA-256-verified CLIMK-WINDS v2 ERA5 gust cells
as GeoJSON polygons suitable for QGIS. Install netCDF4 and numpy using the
repository's acquisition environment. Each feature retains the same
`areaperil_id = native_row * 269 + native_col + 1` as the Oasis hazard tile.

```sh
python research_runners/climk_germany_hazard_geojson_v0.py \
  --storm-index 0 --output /tmp/kyrill-germany.geojson
```

Open the output as a vector layer in QGIS and use graduated styling on
`gust_mps`. Missing gusts are null and must receive a distinct missing-data
style. The original storm label, date, units, source digest and attribution
are included in collection metadata. Native cell boundaries use coordinate
midpoints. The selection uses centres within 5–16 E and 47–56 N, a bounding
box including neighbouring countries; it is not a clipped German boundary.

This is a physical hazard map. To build a spatial CAT scenario, join exposure
points to these polygons and preserve the area-peril ID when constructing
Oasis keys. Supply explicit building classes and a separately justified
vulnerability function before calculating losses. The existing one-cell
Kyrill native GUL demonstration uses fictional exposure and an authored,
uncalibrated curve. Broader maps do not validate that curve. CLIMK's selected
50 storms supply scenarios without annual event frequencies; annual AAL,
OEP and AEP require an additional defensible occurrence catalogue.
