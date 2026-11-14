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
The actual original Figshare v1 metadata also lists the **final technical
document as a distinct third file**: GDW_TechDoc_v1_0.pdf. That file is
scientific documentation, not a third GIS dataset.

### Original Figshare API metadata receipt, 2026-11-04

The official version-specific endpoint
https://api.figshare.com/v2/articles/25988293/versions/1 was fetched
independently through a web research connector. The provider returned
HTTP 200, application/json, 9,524 response bytes, article id 25988293,
version 1, v1 DOI, CC BY 4.0 and article total size 127,938,795 bytes.
The three file rows are:

| Original publisher file | Figshare file id | Declared bytes | Provider supplied and computed MD5 |
| --- | ---: | ---: | --- |
| GDW_TechDoc_v1_0.pdf | 47913739 | 716,288 | 5b2fc93c384f674414fa711b657bef5e |
| GDW_v1_0_gdb.zip | 47913742 | 57,476,758 | 410d1ed16312ac613975fd092c193c65 |
| GDW_v1_0_shp.zip | 47913754 | 69,745,749 | 5064cf2315ef6159d9133b03596e761a |

The original response's declared sizes sum exactly to its article total
(127,938,795 bytes); the two provider MD5 fields agreed for each of
three files. These are **observed provider metadata** only: none of the
three original file bodies were fetched or independently hashed. This
independent API read verifies real endpoint/record shape but does **not**
constitute a live execution receipt of the repository's Python probe.
The Python probe remains probe_ready pending an exact-branch live run.
No original provider response body is stored in the repository.

### Original-publisher disagreement: do not silently calibrate

The publication reports **7,420 km³** storage and **304,600 km²**
artificial terrestrial surface water; the project's current database page
reports **7,405 km³** and **302,450 km²** with the same barrier/polygon counts.
Differences are 15 km³ and 2,150 km², respectively. They might reflect
revisions, rounding or different definitions; there is not yet evidence
to resolve the cause. Neither set is verified from original data bytes.
Do not use as an exact model calibration target without reconciliation.

### Final v1.0 Technical Documentation inspected

The **actual final** `GDW_TechDoc_v1_0.pdf`, Figshare file id **47913739**
(15-page original, dated July 2024), was inspected as public documentation
through a web research connector on 2026-11-04:
https://ndownloader.figshare.com/files/47913739

Its sections 3.1, 3.2 and 4.1 establish these field-level and rights
conditions for future original-archive import (not yet executed):

- Two GIS feature layers **GDW_barriers_v1_0** (points) and
  **GDW_reservoirs_v1_0** (polygons); paired features share **GDW_ID**.
  The declared 5,850 point-only barriers must be treated as expected
  unmatched points, not silently discarded as bad joins.
- GIS coordinates use **geographic WGS 84 (GCS_WGS_1984)**, not an
  implicitly metric/projected CRS. The Shapefile representation declares
  a .prj companion; a standalone UTF-8 comma-delimited barrier attributes
  text file is included in the Shapefile package.
- **-99** denotes missing numeric values; **-9999** denotes missing
  elevation values; empty text fields mean unknown, never inferred absence
  or measured zero. Replace sentinels with *typed nulls* only in a
  documented derivative with untouched raw values preserved externally.
- Section 4.1 states **CC BY 4.0**, while additionally *asking* downstream
  users not to rehost the complete unmodified original release on other
  websites without explicit written author permission. This is an author
  request in the final document, not a silently inferred new licence
  prohibition overriding CC BY terms. In line with the repo's separate
  admission/redistribution governance, no original GIS/PDF mirror is
  authorized or included in this PR.

The **pre-release delta** technical document at
https://jeodpp.jrc.ec.europa.eu/ftp/public/JRC-OpenData/GDW/GDW_TechDoc_v1_delta.pdf
is a separate review-phase artefact and should **not** be substituted for the
final original v1.0 document. This resolves the former documentation-version
uncertainty but does not establish independent original GIS byte integrity,
source record completeness or fitness for insurer CAT modelling.

## Implementation: bounded metadata only

- The existing canonical access file is elevated from documented_only to
  **probe_ready**, not verified_anonymous. It permits exactly one manually
  opted-in GET of the documented **version-specific** endpoint:
  https://api.figshare.com/v2/articles/25988293/versions/1
- New script: **scripts/probe_globaldamwatch_gdw_v1_metadata_v0.py**. One
  explicit --live request, no caller-provided URL/ID/headers/credentials,
  redirect, pagination, retry, archive retrieval or polling; timeout 30 s,
  metadata maximum 131072 bytes, strict UTF-8 JSON, fixed article/version/DOI,
  CC BY 4.0 and the exact two GIS archive names plus the standalone
  final technical PDF, each with frozen file IDs, provider byte sizes
  and mutually matching provider MD5 fields.
- The receipt records retrieval UTC, exact request, response SHA-256/byte count,
  script SHA-256 and provider-declared file metadata; provider download links
  are never followed. Provider MD5 is **not** independent byte verification.
- Synthetic offline tests reject wrong identities, wrong or missing licence,
  file-list drift, malformed JSON, duplicate keys, wrong media/status,
  redirects, oversized responses and naive clocks.

**Actual evidence boundary:** official version-specific JSON was retrieved
through a connected public web research service on 2026-11-04, with exact
article/file-level identity proven at metadata level. The local Linux
container could not reach Figshare directly (DNS resolution unavailable),
so the updated repository-owned Python --live probe has not been run against
the provider from its intended execution environment. The earlier PR-head
GitHub CI was successful, but CI after these changes must be rechecked.
No original archive/PDF bytes, independently computed archive SHA-256,
GIS audit or model admission is claimed. This source is **probe_ready**
rather than **verified_anonymous** and remains **not admitted**.
Any real response-shape conflict must be treated as a failed source check,
not bypassed by loosening identity or rights constraints.

## Next causal steps

1. At the exact new PR head run **python scripts/check_all.py**. Then, from a
   trusted network environment, intentionally run a single
   **python scripts/probe_globaldamwatch_gdw_v1_metadata_v0.py --live**.
   Save only the small receipt and exact commit identity, not provider JSON.
2. Resolve any metadata shape mismatch against the original API specification;
   do not infer a live pass from synthetic tests. The final v1.0 TechDoc has
   now been read; explicitly preserve its WGS84, GDW_ID, missing-value and
   full-original-rehosting caveats when choosing one GIS representation. Separately freeze its
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
