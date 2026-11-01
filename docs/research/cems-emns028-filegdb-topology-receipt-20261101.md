<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CEMS EMSN028 original FileGDB layer and topology research receipt

This is a **metadata-only original-source research observation**, not verified
Paris 2016 insurance exposure, a valid loss footprint, or permission to
redistribute the source FileGDB.

The exact original Copernicus EMSN028 ZIP, SHA-256 and official download
are preserved in the [TOML research receipt](cems-emns028-filegdb-topology-receipt-20261101.toml).
Independent bounded original-source jobs:
[FileGDB layers](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41347769305)
and [original topology semantics](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41348300755).

The complete original archive was **155,898,548 bytes** with locally observed
SHA-256 7ef43d0637447abae705728723c06d2f05415a21667fdee1f10e8fc25b5bf3c2.
The source contains 18 opened FileGDB layers. Important distinctions:

- **Flooded_area**: one original source MultiPolygon for 2016-06-02 with
  approximately **59,755** listed source coordinates. The original geometry
  is **invalid due to a ring self-intersection**. Neither geometry repair
  nor an exact AOI04 observed-flood polygon was validated.
- **Estimated_Max_Flood_Extent**: 1,237 candidate MultiPolygon features,
  which are **estimated/modelled**, not independently confirmed observed
  flooding. Only the first two sample geometries were checked; full
  polygon validity is **not** proven.
- **Buildings**: 647,276 source features, but their **2016 historical
  building vintage** and insured location/value correspondence are
  unverified. These are not 647,276 insured buildings.
- **aoi**: one MultiPolygon for regional coverage, but it does **not**
  establish exact AOI04 spatial correspondence merely from a gauge.

This is a documentation/format correction only. The original source
values, layers, provenance and explicit scientific/rights limitations
are preserved. Copernicus product-specific restricted-use notices and
third-party attribution remain subject to review. No original vector
files, source geometries or insurance risk values are committed.
No topology repair, insurer TIV, vulnerability or CAT model admission.

The research receipt uses TOML because all canonical JSON in this
repository must belong to registered, paired projection families.
The old research-folder JSON was not part of an approved family;
it must not weaken these fail-closed repository validations.
