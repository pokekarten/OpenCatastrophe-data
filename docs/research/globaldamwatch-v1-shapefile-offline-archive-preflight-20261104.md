<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GDW v1.0: offline Shapefile original-archive validation contract (2026-11-04)

## Source and execution status

Original-source metadata has been verified for the frozen
[Global Dam Watch v1.0 Figshare release](https://api.figshare.com/v2/articles/25988293/versions/1):

- Article/version 25988293 / 1, DOI 10.6084/m9.figshare.25988293.v1.
- Original **GDW_v1_0_shp.zip**, file **47913754**, Figshare-declared
  **69,745,749 bytes**, supplier/computed metadata MD5
  **5064cf2315ef6159d9133b03596e761a**.
- Other original representations: Geodatabase ZIP file 47913742 and
  standalone final Technical Documentation file 47913739.
- Scientific inventory claimed by original author: **41,145** barrier point
  records, **35,295** reservoir polygon records, **5,850** legitimate
  point-only barriers, linked through **GDW_ID** and geographic WGS 84.
  Source manual: https://ndownloader.figshare.com/files/47913739.

**No actual original archive was downloaded in this PR.** Local execution
could not reach the original Figshare ZIP. The runnable source preflight was
tested only on synthetic fixtures and is not a claim that the real archive
passes. The accompanying script adds reproducible *readiness* to inspect the
original exactly, once bytes are acquired in an approved external storage
plane. No original provider file is copied into Git.

## Offline runner

From a checkout with a separately and lawfully acquired original ZIP:

    python research_runners/gdw_v1_shapefile_archive_preflight_v0.py \
      --original-zip /path/to/external/GDW_v1_0_shp.zip

Optionally supply an **independently frozen** SHA-256 value:

    python research_runners/gdw_v1_shapefile_archive_preflight_v0.py \
      --original-zip /path/to/external/GDW_v1_0_shp.zip \
      --expected-sha256 <independent_pinned_lowercase_sha256>

Do not compute the comparison hash from the same questionable download and
then present it as independent authenticity evidence. The script always
computes SHA-256 for a receipt; it separately checks the official Figshare
size and MD5 metadata (MD5 is a weak collision-resistant hash and insufficient
as an independent authenticity guarantee).

The runner never downloads, extracts or writes provider records. Its fixed
bounds reject local symlinks, unsupported ZIP compression, unsafe/duplicate
paths, unexpected archive size or MD5, excessive member expansion, bad CRC,
and structural mismatches. Two original shapefile layers must reconcile
SHP/SHX/DBF record counts, SHX byte offsets, numeric nonduplicated
GDW_IDs, and the expected polygon-ID-subset/5,850 point-only count.
Coordinate values are checked against geographic bounds, polygon part
offsets must be valid, every polygon ring must close, and geographic WGS84
must be declared in each PRJ. Raw original IDs and coordinates are only
held transiently as required for the check and never emitted in output.

### Deliberate limits / not a source admission

- A passing structural preflight **does not prove** spatial containment
  of each dam in its paired reservoir polygon, polygon topology/validity,
  correct hydrologic connection, completeness of small dams, current
  operating state, dam-failure frequencies, event loss or insurance TIV.
- The original author's manual warns that reservoir geometry can be
  affected by observation date, and missing numeric source values use
  -99 (elevation -9999), with empty text meaning unknown. This preflight
  does not transform/impute missing values.
- The final TechDoc publishes CC BY 4.0 and separately requests that the
  complete original release not be mirrored on other websites without
  the authors' express permission. Existing metadata-only Git-publication
  policy is unchanged. Raw ZIP bytes must remain outside the repository.
- This is a strict v0 original-source parser. If the real archive exposes
  an unreviewed DBF field encoding, ZIP layout, CRS representation or
  geometry irregularity, preserve the failing receipt. Reconcile against
  actual original content and technical-document semantics; do not weaken
  checks simply to assert readiness.
- No insurer exposures, Cat ILT/YLT, pricing, licensing promotion, model
  training or Neon database writes are performed.

## Tests and next action

The synthetic offline test suite exercises valid shape, wrong byte-size/
publisher MD5/SHA-256, unexpected IDs, missing sidecars, invalid SHX offsets,
row count mismatch, invalid CRS, corrupt ZIP CRC, path traversal, symlinks,
bad polygon closure, invalid geographic coordinates, null shapes, duplicate
archive entries and deleted/invalid GDW_ID records.

After review of the PR and a trusted network/external-data plane becomes
available, acquire the **exact** v1 Shapefile ZIP by file ID, preserve its
external original receipt and run the preflight. Record the actual
provider-byte SHA-256 and any failure flags without uploading source bytes.
A separate scientific audit can then assess per-feature completeness,
attribute provenance/sentinels, topology, spatial ID matching and independent
event evidence before any model input admission.
