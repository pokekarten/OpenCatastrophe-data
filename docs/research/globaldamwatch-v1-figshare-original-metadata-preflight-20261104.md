<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Global Dam Watch v1.0: original-source metadata preflight (2026-11-04)

**Scope:** one fixed public Figshare article-version metadata request. This is
not an archive download, an admission, a dam-failure-risk model, a licence
for raw-data redistribution or a Neon database update.

## Original sources and provenance

- Publisher archive: https://figshare.com/articles/dataset/Global_Dam_Watch_database_version_1_0/25988293
- Exact v1 DOI: https://doi.org/10.6084/m9.figshare.25988293.v1
- Peer-reviewed paper: https://doi.org/10.1038/s41597-024-03752-9
- Project: https://www.globaldamwatch.org/database
- Figshare API route specification: https://docs.figshare.com/v2/
- Anonymous metadata API guide: https://info.figshare.com/user-guide/how-to-use-the-figshare-api/
- Data Access Policy: https://info.figshare.com/user-guide/figshare-policies/

The publisher and journal describe 41,145 **barrier points** and 35,295
associated **reservoir polygons** in GDW v1.0. Exactly 5,850 barrier points
have no corresponding polygon. These are two feature types, not two independent
source inventories. The shared GDW_ID relates paired features but must still
be tested for uniqueness and correct spatial/topological matching on original
files. Archive names **GDW_v1_0_gdb.zip** and **GDW_v1_0_shp.zip** are alternate
format representations of one dataset, not distinct scientific releases.
The Shapefile representation additionally includes barrier-attribute CSV.

### Original-publisher disagreement: do not silently calibrate

The publication reports **7,420 km³** storage and **304,600 km²**
artificial terrestrial surface water; the project's current database page
reports **7,405 km³** and **302,450 km²** with the same barrier/polygon counts.
Differences are 15 km³ and 2,150 km², respectively. They might reflect
revisions, rounding or different definitions; there is not yet evidence
to resolve the cause. Neither set is verified from original data bytes.
Do not use as an exact model calibration target without reconciliation.

A publicly indexed **pre-release delta** technical document at
https://jeodpp.jrc.ec.europa.eu/ftp/public/JRC-OpenData/GDW/GDW_TechDoc_v1_delta.pdf
requests avoiding full original-format redistribution without explicit author
permission, despite its stated CC BY licence. It is not the final v1 TechDoc
inside the published archive. Check the final release instructions, reuse
rights and attribution before republishing any source bytes. The source is
CC BY 4.0 per publisher and journal, but this PR grants no public mirror.

## Implementation: bounded metadata only

- The existing canonical access file is elevated from documented_only to
  **probe_ready**, not verified_anonymous. It permits exactly one manually
  opted-in GET of the documented **version-specific** endpoint:
  https://api.figshare.com/v2/articles/25988293/versions/1
- New script: **scripts/probe_globaldamwatch_gdw_v1_metadata_v0.py**. One
  explicit --live request, no caller-provided URL/ID/headers/credentials,
  redirect, pagination, retry, archive retrieval or polling; timeout 30 s,
  metadata maximum 131072 bytes, strict UTF-8 JSON, fixed article/version/DOI,
  CC BY 4.0 and precisely two archive names with positive IDs/sizes.
- The receipt records retrieval UTC, exact request, response SHA-256/byte count,
  script SHA-256 and provider-declared file metadata; provider download links
  are never followed. Provider MD5 is **not** independent byte verification.
- Synthetic offline tests reject wrong identities, wrong or missing licence,
  file-list drift, malformed JSON, duplicate keys, wrong media/status,
  redirects, oversized responses and naive clocks.

**Actual evidence boundary:** publisher and API documentation checked on
2026-11-04. In this session the endpoint's real JSON could not be retrieved
from the local execution plane, and no production live canary, original archive
bytes, GIS audit or full repository CI is claimed. This source is **probe_ready**
but not **verified_anonymous** and remains **not admitted** for model input.
Any real response-shape conflict must be treated as a failed source check,
not bypassed by loosening identity or rights constraints.

## Next causal steps

1. At the exact PR head run **python scripts/check_all.py**. Then, from a
   trusted network environment, intentionally run a single
   **python scripts/probe_globaldamwatch_gdw_v1_metadata_v0.py --live**.
   Save only the small receipt and exact commit identity, not provider JSON.
2. Resolve any metadata shape mismatch against the original API specification;
   do not infer a live pass from synthetic tests. Confirm final v1 archive
   licence/TechDoc and choose one file representation. Separately freeze its
   file ID, download rights, byte count and independently computed SHA-256.
3. Audit GDW_ID uniqueness, polygon match coverage, geometry, CRS, original
   per-record source attribution and attribute missingness before external
   raw storage or scientific admission. Separate training from validation
   lineage when combining GDW with HydroSHEDS and observed flood data.
4. Potential consumers: regional infrastructure exposure proxies,
   basin/upstream-downstream context and observational overlays.
   GDW alone has no dam breach frequency, structural fragility,
   flood-depth/intensity, insured TIV, claims, policy or loss information.

No upstream data bytes, credentials or private assets are committed here.
