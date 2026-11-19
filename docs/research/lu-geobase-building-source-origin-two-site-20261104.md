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

## Executed exact-source original-data evidence — 2026-11-04

**Successful original-source GitHub Actions run:** https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41885385975 .
The source runner downloaded the one fixed official GeoBase Buildings ZIP, checked the already established national source and inner GeoPackage SHA-256 receipts, verified all 230,353 source objects and the original geometry-layer index, then scanned the exact fixed city/Berdorf 100m windows. **Ten of ten offline fictional regression tests also passed.** No feature ID, origin text outside preapproved published labels, address or polygon coordinates, WKB, or source file was uploaded to GitHub.

| Exact original receipt and geometry filter | Luxembourg city | Berdorf |
| --- | ---: | ---: |
| Raw indexed rectangle RTree row hits | **108** | **18** |
| Geometry actually intersects the enclosing native rectangle | **107** | **18** |
| Geometry intersects the exact rotated 100m window with positive area | **104** | **16** |
| Removed by final positive-area filter | **3** | **2** |
| Source: Bati3DVDL, City of Luxembourg 3D database | **104** | 0 |
| Source: Bati3DACT, ACT 3D database | 0 | **16** |
| Source: PCN, MO, Ortho, missing_label, other_unreviewed | **0** | **0** |

**Conservation:** 104 city true-area polygons = 104 city-managed 3D-building origin labels; 16 village true-area polygons = 16 ACT-managed 3D-building origin labels. Neither site contained a missing or unrecognized Source code in this fixed original snapshot.

The explicit **108 → 107 → 104** distinction in the city experiment is important: the original native RTree may return an envelope-rectangle hit whose actual polygon does not even intersect that enclosing rectangle. Earlier city source experiments cited 107 as their native rectangle-filtered polygons, while the exact 100m research window contains 104 positive-area polygon objects. For Berdorf the same stages are 18 → 18 → 16. The official original data and original source hashes remained unchanged; the stage counts express different geometry selection rules.

### Interpretation for future genuinely independent validation

The observed city 104 all carry the original Bati3DVDL label while the observed village 16 all carry Bati3DACT. This **demonstrates heterogeneous digitization-source lineage** even within an ACT-published GeoBase export, and provides an informed direction for separate urban versus village ground-truth evaluation.

It does **not prove** that the municipality and national cadastre collected independent raw imagery or survey points, that VDL 3D geometry validates ACT addresses, or that these proportions generalize beyond two tiny purposively selected research blocks. The upstream municipal 3D survey epoch, photogrammetry inputs, joint cadastral data and licences are not independently audited. A blind manual control and independent raw sensor/sample design remain mandatory. The 51/51 city and 6/6 Berdorf address-in-polygon rates are not independent accuracies and no insured properties or replacement values are admitted.

