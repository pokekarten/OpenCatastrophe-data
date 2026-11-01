<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EUBUCCO Luxembourg LU00 v0.2: first original Parquet receipt

**Date:** 2026-11-01. **Status:** experimental original-byte read; NOT an
admitted CAT model input, building exposure import or ownership/address join.

## Original source target and lineage

- Producer: EUBUCCO / TU Berlin and partners.
- Original v0.2 NUTS2 partition candidate (official documented path template):
  <https://s3.eubucco.com/eubucco/v0.2/buildings/parquet/nuts_id=LU00/LU00.parquet>.
- Documentation: <https://docs.eubucco.com/v0.2/data-access/cli/>,
  <https://docs.eubucco.com/v0.2/data-format/schema/>,
  <https://docs.eubucco.com/v0.2/license/>.
- Luxembourg NUTS2 partition: `LU00`, NUTS3 region: `LU000` under the
  provider's adapted 2016 geography. Do not silently join to later NUTS
  releases.
- EUBUCCO dataset licence is generally **ODbL v1.0**, with explicitly listed
  regional source exceptions (Abruzzo, Prague). Confirm Luxembourg provider
  source lineage and any upstream rights/ODbL obligations *before* any
  redistribution, combined source release or commercial model ingestion.
- Original footprint geometry is documented as **EPSG:3035 WKB**; EUBUCCO
  `geometry_source`, `geometry_source_id` and per-attribute source metadata
  must be preserved for any scientific independence claim.
- Luxembourg ACT2023v2 official `238189` roof-derived MultiPolygon features
  in **EPSG:2169** are a DIFFERENT source, geometry definition and observation
  period; `ACT` counts must not be substituted for EUBUCCO building counts.

## Actual next execution

The new `.github/workflows/eubucco-lu00-original-source-receipt.yml`
workflow requests **one exact** public Luxembourg Parquet partition over
HTTPS, with no wildcard/pagination, an 256 MiB source byte cap, request timeout
and read-only GitHub permissions. It runs previously merged 10 synthetic
Parquet tests under pinned PyArrow 20.0.0, then uses
`research_runners/eubucco_lu00_lineage_preflight_v0.py` (merged via #915)
to validate the source object and return aggregate counts only.

It should emit:
- Exact original file SHA-256 and file size; a first observed digest is
  **not** prior independent authenticity verification. Freeze it only if
  the source filename, original provider HTTPS URL and parsing all succeed.
- Original EUBUCCO LU00 count and NUTS3 region count, unique building ID check,
  `geometry_source` families (government-labelled, OSM, Microsoft or other)
  and attribute-source family counts; never original per-building values.
- Explicit `false` values for scientific independence from ACT2023v2,
  licence approval, valid building geometry or CAT model input admission.

**Fail-closed outcomes**: missing object/HTTP error, oversized file, wrong
Parquet header, incorrect geometry data type, duplicate IDs, unexpected
regional values or more than 2 million rows stop the experiment. No fallback
to a different release or a guessed NUTS code.

The original Parquet remains only on the temporary workflow runner and is
deleted by a shell trap. No raw source bytes, geometry, individual IDs or
insurer records are uploaded, merged into Git or written into the independent
`insurance-risk-core` Neon metadata registry.

## Next matching evidence gate, not yet completed

1. Independently confirm exact LU00 original Parquet checksum and actual
   producer metadata for Luxembourg source geometry. Establish whether the
   upstream source overlaps ACT2023v2 or shares official cadastre lineage.
2. Audit the unusual **EPSG:2169 axis order** (X = northing,
   Y = easting) using known ground control and actual geometry coordinates,
   not just the declared EPSG code.
3. Select same geographic area and validated survey vintages; only then
   compare bounded EUBUCCO 3035 footprints to ACT 2169 rooftop extents.
   Use stratified manual review and retain unresolved 1:n/n:1 splits.
4. Before any source-to-source attribute enrichment, require provenance
   checks, geometry-match acceptance criteria, explicit commercial rights
   review and scientific admission. Do not treat high IoU or coincident
   addresses as a valid insurer exposure ID.
