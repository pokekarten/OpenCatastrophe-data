<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Global Dam Watch v1.0 — exact-source per-ID native invalidity concordance

## Original publisher evidence, 2026-11-04

The published GDW v1.0 data have **two independent archive representations**
of one authored reservoir/barrier inventory, not two independent scientific
observations.

- Shapefile version: Figshare file 47913754; exact original ZIP
  SHA-256 2fe0b367ed3fcfb299160cd9652b16a8a19338951026ee2ac91edfebf1f3b7ae.
  Official original source GEOS/Shapefile result:
  https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41887835566
- Geodatabase version: Figshare file 47913742, 57,476,758 bytes, source
  declared MD5 410d1ed16312ac613975fd092c193c65. Its original
  independently observed ZIP SHA-256:
  **5ebb1092e355f1833132be8a16340da7de979314d06aba00e57eb7412884f09f**.
  Official original source Fiona/OpenFileGDB/GEOS receipt:
  https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41892321883.

Both observed source archives contain 41,145 barrier points, 35,295
reservoir polygons and 5,850 point-only barriers. With two independently
implemented source readers, both show 35,074 valid reservoir polygons,
**221 invalid** reservoirs, and the GEOS reason family
**ring_self_intersection = 221**, with no invalid points outside an
assessable valid source polygon.

## What matching aggregate totals do NOT establish

Identical totals and identical GEOS error families alone do not prove the
same **source GDW_IDs** were classified invalid. Two formats could have
different invalid polygon identities while both show 221 failures.

The separate reproducible runner
research_runners/gdw_v1_original_crossformat_invalidity_v0.py
therefore checks **both exact original ZIP SHA-256 pins**, reads the
Shapefile source IDs using PyShp and the Geodatabase IDs using Fiona,
and computes transient set overlaps within the same temporary process.

It publishes only source aggregate counts:
- intersection and symmetric difference of original barrier GDW_IDs;
- intersection and symmetric difference of original polygon GDW_IDs;
- number of polygon IDs invalid in both formats versus only one format;
- Boolean equality of full source ID sets and invalid sets.

No actual source GDW_ID, record, coordinate, geometry or individual
GEOS validity explanation escapes the trusted process. The local original
ZIPs are kept outside Git in a private temporary runner and removed;
there are no uploaded source artifacts.

The pull-request job runs **synthetic-only** tests, and an exact-main
workflow push runs one comparison using both immutable original
published file IDs; no redownload on arbitrary branch or unreviewed PR.

**Scientific boundary:** Per-ID source agreement still does not prove
topological correctness, representativeness of reservoir surface at
event time, independent GIS-engine validity, dam-breach likelihood,
insured asset exposure or CAT loss curve readiness. Never automatically
repair, snap or accept these 221 native invalid source polygons.
The original authors' CC BY attribution/no-wholesale-mirror guidance
and the repository's separate admission policy continue to apply.


## Observed exact-ID result (main workflow, 2026-11-04)

The real original-data workflow has now run successfully:
https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41893588594

Both source archives were downloaded **anew**, verified against their
separately frozen full original ZIP SHA-256s, and processed in one
temporary runner with PyShp and Fiona/OpenFileGDB, respectively.

| Exact original GDW_ID set comparison | Result |
| --- | ---: |
| Source barrier GDW_IDs shared by both formats | 41,145 |
| Barrier IDs unique to Shapefile | 0 |
| Barrier IDs unique to Geodatabase | 0 |
| Source reservoir GDW_IDs shared by both formats | 35,295 |
| Reservoir IDs unique to Shapefile | 0 |
| Reservoir IDs unique to Geodatabase | 0 |
| GEOS-invalid native ring GDW_IDs shared by both formats | **221** |
| Invalid polygon IDs unique to Shapefile | **0** |
| Invalid polygon IDs unique to Geodatabase | **0** |

Therefore **all 221 native invalid polygon source IDs are identical
between the two original formats**. This is substantially stronger
than equal counts and helps exclude format-specific record differences
as the explanation for the observed invalidity. It does not establish
bitwise identical underlying geometry coordinates or independently
validate the GEOS topology algorithm.

The evidence is frozen in
research_runners/gdw_v1_original_crossformat_id_receipt_v0.py.

### Follow-up quality gate

The 221 polygons are **not admitted** as unqualified CAT model input.
No automatic ring repair, clipping, snapping or silent deletion is
permitted. Next quantify the consequences of possible modifications
separately, e.g. native polygon area, conservative area change under
a named repair method, feature-count change, paired point coverage,
and the extent of geometry changes. Those are what-if diagnostics,
not approval to modify the original inventory or assign a loss value.

A full independently verified hydraulic model, source coverage,
risk exposure values and insurer hazard/vulnerability calibration
remain outside the evidence of these GIS source quality checks.
