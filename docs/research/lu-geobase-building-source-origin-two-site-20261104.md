<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg GeoBase Buildings: original digitization-source lineage

**2026-11-04 — research only.** No original feature IDs, individual source labels, building geometries, addresses, policies or financial exposures are written to Git.

## Scientific motivation

ACT BD-Adresses declares that georeferencing can come from manual placement, cadastral parcel centroid, or largest-building-on-parcel centroid. Thus address-in-polygon is **not an independent positional accuracy test**:
https://data.public.lu/en/datasets/adresses-georeferencees-bd-adresses/

The official BD-L-GeoBase Buildings source combines geometries originating from multiple digitization pathways; the publisher's GeoBase contents-description v1 Section 4.4 has a Source field:
https://download.data.public.lu/resources/bd-l-geobase/20240925-163507/contentsdescription-bd-l-geobase-v1.pdf
https://data.public.lu/en/datasets/bd-l-geobase/

| Original published Source code | Origin described by producer | Independently validated observation? |
| --- | --- | --- |
| Bati3DACT | ACT-managed 3D buildings database | No |
| Bati3DVDL | City of Luxembourg-managed 3D buildings database | No; separate data manager only |
| PCN | Digital cadastral plan | No; likely related to address georeferencing |
| MO | Official surveying / mensuration officielle | Not established |
| Ortho | Digitized from orthoimage | Not established |
| missing_label and other_unreviewed | Missing or not-listed code | Block from lineage-based promotion |

OSM and Overture cannot automatically serve as independent reference observations: Overture conflates OSM, Esri, Google/Microsoft and other geometries under ODbL:
https://docs.overturemaps.org/guides/buildings/
EUBUCCO government-labelled Luxembourg geometry may share historical ACT lineage. Dataset branding does not prove independent feature provenance.

## Original data contract

Research runner: research_runners/lu_geobase_source_origin_two_site_v0.py

The runner reuses the original 2026-10-01 official GeoBase Buildings ZIP checksum:
6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3.
The extracted original GPKG SHA-256 is:
ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676.
National original feature count: 230,353.

Both 100 × 100m EPSG3035 site rectangles were predeclared in prior ACT GIS studies. The source runner requires previous original exact spatial counts:
- Luxembourg city centre 6.1319 E,49.6116 N: 107 enclosing native RTree rectangle candidates, **104 true positive-area buildings**.
- Berdorf St John church centre 6.348821 E,49.820946 N: 18 enclosing candidates, **16 true positive-area buildings**.

Only the fixed official Source code-count distribution for each site is output. Each actual true-area polygon contributes exactly one counted source code. Missing and unreviewed codes are aggregated under fixed marker categories; their raw unreviewed text is never emitted. The original signed/source IDs, geographic coordinates and geometry WKB are not logged, committed, copied to Neon or uploaded as CI artifacts.

Focused CI: .github/workflows/luxembourg-geobase-source-origin-two-site.yml
Synthetic tests: tests/test_lu_geobase_source_origin_two_site_v0.py
Command: python -m unittest discover -s tests -p test_lu_geobase_source_origin_two_site_v0.py -v
Original execution only after pinning Python 3.13, pyproj 3.7.2 and Shapely 2.1.2.

## Controls still needed

The GeoBase Source column is a **source-family hint**, not evidence of truly independent sensors, upstream observation, data rights, ground-truth building existence or entry point accuracy. Neither publisher-separated nor ML-derived geometries should be called independent without feature-level ancestry, original-byte receipts, different raw observations and a blinded verification sample.

No insurer, TIV, address unit, building ownership, vulnerability, insured loss, catastrophe model result, or regulatory source admission is allowed from this research. Two purposive 100m sites are not representative of Luxembourg nationally. The sample output must remain non-admitted.

**Actual source-frequency counts remain unverified until exact-head CI run completes successfully.**
