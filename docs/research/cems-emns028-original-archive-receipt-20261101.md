<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CEMS EMSN028 2016 France ZIP: original-link access and intake gates

**Checked 2026-11-01.** This is an *independent source-intake
research receipt*, not a physical 2016 flood-footprint, licensed
historical building exposure or CAT-model admission.

## Official first-party source and exact URL

- [Copernicus EMSN028 activation](https://mapping.emergency.copernicus.eu/activations/EMSN028/):
  France 2016 flood, 17 AOIs, 51 published products.
- Original HTML anchor in activation's **Geospatial Data** section:
  [EMNS028_AOI_FRANCE_utm31n.gdb.zip](https://mapping.emergency.copernicus.eu/download/EMSN028/EMNS028_AOI_FRANCE_utm31n.gdb.zip).
  **Important:** this exact first-party filename is **EMNS028**, despite
  the activation being **EMSN028**. Do not silently "fix" the typo.
  The observed link resolves through Copernicus's S3 archive.
- Independently visible AOI04 **Observed Flood Extent (Detail)**
  [map PDF](https://mapping.emergency.copernicus.eu/download/EMSN028/EMSN028_04SAINT-FARGEAU-PONTHIERRY_01OBSFLOODEXTENT_DETAILS_v1_100dpi.pdf).
  A map link is not an original vector polygon or georeferenced
  building-level flood-depth observation.
- The *observed extent* (principally remote-sensing image
  classification), *modelled/extrapolated maximum flood extent/depth*
  (using IGN BD Alti 5 m) and *derived impact assessments* are separate
  product families. Do not combine or relabel them.

## First two executed live access checks

1. **HEAD-only original source link**:
   [run 41335510643](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41335510643)
   returned HTTP 200 with \`text/html\` and zero content length.
   This is **inconclusive**, not a proved unavailable ZIP.
2. **GET with HTTP \`Range: bytes=0-3\`**:
   [successful run 41335865007](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41335865007)
   returned **HTTP 206**, range honored, S3 target
   \`cems-mapping-website.s3.amazonaws.com\`, media type
   \`application/x-zip-compressed\`, ZIP local-file signature
   \`PK\\x03\\x04\`, and total original archive length
   **155,898,548 bytes** (about 149 MiB) from
   \`Content-Range\`.
   Exactly **four data bytes were read**; no source ZIP was downloaded,
   archived, decompressed, or retained in this run.

Both requests use [the fixed first-party path](https://mapping.emergency.copernicus.eu/download/EMSN028/EMNS028_AOI_FRANCE_utm31n.gdb.zip).
Presigned S3 query tokens are intentionally never logged or stored.

## Bounded full original archive intake (metadata-only)

The independently synthetic-tested
\`scripts/cems_emns028_ephemeral_zip_inventory_v0.py\` can perform
**one explicit** \`--live\` original ZIP request. It:
- allows only the official first-party/S3 redirect allowlist over HTTPS;
- caps the complete response at **180,000,000 bytes**;
- requires exact previously measured original ZIP length **155,898,548**,
  to stop unreviewed source-version changes;
- computes a **SHA-256 of the response bytes fetched**, but does not
  mistake that for an independently signed publisher checksum;
- reads only the ZIP *central directory*, records member count,
  extension distribution and FileGDB folder count, without extracting
  or decompressing provider file payloads;
- bounds member count, declared uncompressed total and rejects unsafe
  archive member paths even though extraction is disabled;
- automatically deletes its temporary original ZIP even on failure;
- prints metadata only; never stores third-party original bytes in Git.

Run locally only after source-specific rights are reviewed:

\`\`\`bash
python -m unittest tests.test_cems_emns028_zip_head_receipt_v0 \
  tests.test_cems_emns028_zip_prefix_receipt_v0 \
  tests.test_cems_emns028_ephemeral_zip_inventory_v0 -v
python -m scripts.cems_emns028_ephemeral_zip_inventory_v0 --live
\`\`\`

[Bounded GitHub Actions workflow](https://github.com/pokekarten/OpenCatastrophe-data/blob/main/.github/workflows/cems-emns028-ephemeral-inventory.yml)
runs this once when its relevant source files change, with no recurring
schedule or artifact upload. Verify its *actual completion* and log receipt
before claiming a full archive was retrieved.

## Legal, semantic and historical boundaries

[Current CEMS On-Demand Mapping terms](https://mapping.emergency.copernicus.eu/terms-and-conditions/)
permit broad use of nonrestricted CEMS results subject to source credit,
but explicitly reserve access for some restricted activations and do
not override third-party imagery/underlying geodata rights.
Historical 2016 deliverables may carry additional access notes.
**The specific EMSN028 archive's restriction status and embedded
third-party licence constraints have not been independently cleared**.
Public HTTP accessibility is not proof of commercial redistributability.

The France-wide archive could contain files spanning many AOIs; the
presence of \`EMNS028\` in the filename does *not* prove it contains the
**AOI04 observed** flood polygon with a verified timestamp/CRS.
An original ZIP checksum alone likewise does *not* prove GIS layer
semantics, 2016 building-vintage correspondence, penetration of insured
risks, hazard depth or insurance loss. The existing CAT-only Neon
\`research.cems_emns028_aoi04_product_evidence_v0\` has three
metadata-only rows; all original-geodata, rights and CAT admission
flags remain **false**. No Neon data or schema were modified by
these checks.

## Next evidence gates

1. Preserve exact original archive receipt after controlled full run.
   Confirm ZIP member list and geodatabase contents without
   publishing licensed source bytes.
2. Identify the **specific AOI04 observed extent feature layer**,
   geometries, acquisition time, coordinate system, provenance and
   source-specific permissions (not merely the maximum flood extent).
3. Acquire a legally usable **2016-vintage** building inventory,
   independently quantify alignment and 2016 flood overlap.
4. Obtain insured sums and policies, vulnerability assumptions and
   validated claims/loss evidence before a real CAT simulation.


## Completed one-time original-source check (2026-11-01)

The [GitHub Actions run 41336175575](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41336175575)
**completed successfully**. The bounded downloader obtained and checked
the **complete original archive** without committing or redistributing
any downloaded provider data. It wrote only metadata to the public log.

| Field | Verified value |
| --- | --- |
| Complete official archive length | **155,898,548** bytes |
| Locally computed original ZIP SHA-256 | **7ef43d0637447abae705728723c06d2f05415a21667fdee1f10e8fc25b5bf3c2** |
| ZIP members | **173** |
| Declared uncompressed size | **297,718,220** bytes |
| FileGDB folders | **1** |
| \`.gdbtable\` / \`.gdbtablx\` | **30 / 30** |
| ESRI \`.lyr\` style files | **18** |
| Filenames loosely containing “04” or “ponthierry” | **13** (only name hints) |

The exact receipt is saved as
[\`cems-emns028-original-archive-receipt-20261101.toml\`](cems-emns028-original-archive-receipt-20261101.toml).
The ZIP was automatically deleted from temporary runner storage;
no private asset, credentials or original geodata is stored here.

**New stage:** \`ORIGINAL_ARCHIVE_SHA256_OBSERVED\`. This is stronger than
a discoverable website link, but it is **not** \`AOI04_OBSERVED_FLOOD_GEOMETRY_VERIFIED\`.
The package needs a real FileGDB layer-name and CRS/content review before
spatial analysis. The source archive checksum is calculated from one
download; an independent publisher-provided signature is not claimed.
Copernicus restricted-activation and third-party rights must still be
confirmed before reuse or distribution. All CAT model admission remains
blocked.
