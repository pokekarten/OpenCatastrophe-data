<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# FEMA Hurricane Michael DR-4399: original image-lineage field completeness and comment hints

**Original read-only provider aggregate queries:** 2026-11-01. **Not admitted.** Public FEMA historical geospatial damage assessment layer 0: https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/FEMA_Historical_Geospatial_Damage_Assessment_Database/FeatureServer/0/query .

The original cohort `DIS_NUMBER = 'DR-4399' AND ASMT_TYPE = 'RS' AND DMG_TYPE = 'WI'` contains **23,682 public FEMA remote-sensing wind damage assessment point features**. These are ordinal visual damage classifications, not paid claims, independent field measurements or unique building identities. Only aggregate `returnCountOnly=true`, `returnGeometry=false`, `f=json` queries were used; **not a single `COMMENTS`, `OBJECTID`, point, address or image value was requested or downloaded**.

## Original provider count-only checks

| Exact strictly aggregate provider filter within the cohort | Original count |
| --- | ---: |
| `COMMENTS IS NOT NULL` | **212** |
| `IMG_DATE IS NOT NULL` | **0** |
| `PROD_DATE IS NOT NULL` | **0** |
| `COMMENTS LIKE '%NOAA%'` | 0 |
| `COMMENTS LIKE '%NICB%'` | 0 |
| `COMMENTS LIKE '%NCIB%'` | 0 |
| `COMMENTS LIKE '%GIC%'` | 0 |
| `COMMENTS LIKE '%VEXCEL%'` | 0 |
| `COMMENTS LIKE '%IMAGE%'` | 0 |
| `COMMENTS LIKE '%IMAGERY%'` | 0 |
| `COMMENTS LIKE '%AERIAL%'` | 0 |
| `COMMENTS LIKE '%ORTHO%'` | 0 |
| `COMMENTS LIKE '%2018%'` | 0 |
| `COMMENTS LIKE '%DATE%'` | 0 |
| `COMMENTS LIKE '%SATELLITE%'` | 0 |
| `COMMENTS LIKE '%FLIGHT%'` | 0 |
| `COMMENTS LIKE '%GOOGLE%'` | 0 |
| `COMMENTS LIKE '%FEMA%'` | 0 |

The 212 non-null comments are a real original **aggregate count**, not full comment content. A zero on fifteen handpicked strings says **only** that none of those case-insensitive-or-provider-collation-dependent literal `LIKE` predicates matched; it does NOT establish that all comment strings are empty, irrelevant, safe to publish or incapable of linking imagery. The source database's collation and each text value were not audited. A source provider `SOURCE=FEMA` is the **producer of the labels**, not the original aerial image producer. Both `IMG_DATE` and `PROD_DATE` are absent for all the selected 23,682 assessments, so a date for the original evidence cannot be derived from `EVENT_DATE`, a NOAA STAC time, a dashboard date or a present publication timestamp.

## Scientific consequence

FEMA classifies remote-sensed `AFF` and `DES` based on post-event imagery, but the public field representation does not link those classifications to an exact scene/file checksum, acquisition hour, image tile URL or assessed-building identity. A NOAA/FEMA spatial overlap **must not** be presented as independent ground truth without proving the original classifier did not use that NOAA source. A 2022 NOAA presentation shows historical alternate `NCIB Imagery` and NOAA layers, but a map checkbox alone is **not a per-FEMA-feature lineage record**. The exact original 2018 FEMA image provenance and any independent non-remote-sensing ground reference remain **unknown**.

`research_runners/fema_michael_comments_lineage_v0.py` builds exactly 18 pinned **count-only** queries with no feature/attribute/geometry requests. Its `reconcile_lineage_counts()` accepts only strict response objects of the form `{"count": integer}`, validates each within the frozen 23,682 feature cohort and ensures keyword counts do not exceed the non-null comment count. Its synthetic test companion verifies negative privacy and leakage paths. **No data is admitted to any CAT model.**

## Next source-scoped research

Find an official archive of the exact FEMA 2018 damage-dashboard map/source-layer configuration or a provider-issued data dictionary with an original `source_image_url`/scene provenance field; separately seek professionally recorded field inspections with permission and dated structure identity. Avoid interpreting comments as owner addresses or requesting feature-level free text absent a distinct legal/privacy/scientific justification.
