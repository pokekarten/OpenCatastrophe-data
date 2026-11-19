<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# US Census TIGER/Line 2026 — source-specific reuse, trademark and CAT science gate

**Research review: 2026-11-03.** No provider geospatial data or private insurer
material is copied into this public repository. This is a citation and
release-boundary note, **not** a legal certification or CAT source admission.

## Direct first-party evidence for the 2026 vintage

1. [Census 2026 TIGER/Line release page](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.2026.html):
   2026 boundaries and names are as of **2026-01-01**, released **2026-10-14**.
   The core shapefiles carry geographic entity IDs but **no demographic data**.
2. [2026 technical documentation index](https://www.census.gov/programs-surveys/geography/technical-documentation/complete-technical-documentation/tiger-geo-line.html)
   links the release-specific **Chapter 1** rather than a previous-year licence.
3. [Original Census 2026 Chapter 1 — legal disclaimer / citation](https://www2.census.gov/geo/pdfs/maps-data/data/tiger/tgrshp2026/TGRSHP2026_TechDoc_Ch1.pdf):
   Section 1.2 states US government work is outside US copyright protection under
   17 USC 105 and Census material can be reproduced, while **requesting Census
   Bureau attribution**. Section 1.1 separately protects the **TIGER/Line® and
   Census TIGER registered marks**: do not use the marks as/in the proprietary
   commercial product name; indicate that name only as source/type and carry
   their requested visible disclaimer in repackaging.
4. The same 2026 Chapter 1 explicitly gives **no positional/attribute accuracy
   warranty**, and describes boundaries for **statistical data collection and
   tabulation**, not a determination of land ownership, legal title or jurisdiction.

## Source rights are not the same as insurance-science admission

| Decision axis | Research finding |
| --- | --- |
| 2026 original source text | Retrieved directly from the Census publisher's version-specific Chapter 1 |
| US copyright / general reproduction | Source describes US government Census materials as reproducible; maintain citation |
| Trademark / product branding | Must **not** use TIGER/Line® as a proprietary product name or imply sponsorship; retain source attribution and requested notice |
| Region geography | 2026 administrative-vintage boundary, NOT original 2016/2021 event geography |
| Asset identity and position | No real insured building/policy or authoritative parcel/geocoder validation |
| Geophysical peril model | No flood depth, wind intensity, occurrence rate or calibrated vulnerability |
| Legal/operational final review | **Pending** version-specific operational implementation and downstream terms review |
| Scientific / model input admission | **Not admitted** |
| Database change / raw content persistence | **None** |

Canonical research candidate
`us.census.tigerline.county-parish-equivalent.v2026` was registered in
[discovery-only PR #1189](https://github.com/pokekarten/OpenCatastrophe-data/pull/1189).
Keep its `rights_review_status=not_reviewed`,
`scientific_review_status=not_reviewed` and `admission_status=not_admitted`
until an explicit reviewer approves the source-specific rights determination
and a **separate** scientific/geometry/insured-identity model-input gate passes.

The longer research [PR #1100](https://github.com/pokekarten/OpenCatastrophe-data/pull/1100)
reports independently pinned 2026 national COUNTY original-ZIP metadata,
64 Louisiana original parish polygon research checks and a tiny Microsoft
roofprint sample; those analyses have separate provenance/rights constraints.
They do **not** turn official administrative geometry into insured-property
data, and they do not prove native OpenCatastrophe→NextGen multi-peril runs.

**Next technical gate:** independently preserve the 2026 national COUNTY
source checksum/asset receipt plus provenance without publishing raw geometry;
require correct `GEOID`/boundary vintage, separately review Microsoft and any
commercial footprints, verify all relevant national geographic levels, and
check policy/TIV records only in private authorized systems. A 2026 boundary
must never silently relabel historical CAT years.
