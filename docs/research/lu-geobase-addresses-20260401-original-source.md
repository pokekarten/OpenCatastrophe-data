<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original ACT GeoBase Addresses-theme source: 2026-04-01 (not Buildings)

**Original-source preflight only, 2026-11-04.** The official ACT
[BD-L-GeoBase dataset](https://data.public.lu/en/datasets/bd-l-geobase/)
has a separately published, ~12.8 MB **GeoPackage ZIP** for its
**Addresses** theme (release **1 April 2026**). It is distinct from the
October 2026 **Buildings**-theme GeoPackage and from the November 2026
**BD-Adresses CSV**. All three have different source dates and meanings.

## Exact publisher discovery

- Original source ZIP:
  [addresses-20260401.zip](https://download.data.public.lu/resources/bd-l-geobase/20260401-011010/addresses-20260401.zip)
- Stable published resource ID: `d76d095a-94a0-4426-af15-45f70881c63f`.
- Provider-listed original MD5: `5157355db4b81736ad2e1d2d399a1bed`.
- Official catalogue licence marking: CC0.
- Original technical CRS: LUREF / **EPSG:2169**.
- The same page also lists an **October 1, 2026 GDB** Addresses-theme
  package, but it is **not** this April GeoPackage. Neither may be
  silently substituted for the other.

The official ACT
[BD-L-GeoBase content specification v1.0 (2024), §4.1](https://download.data.public.lu/resources/bd-l-geobase/20240925-163507/contentsdescription-bd-l-geobase-v1.pdf)
describes `AD_AddressID` as the unique address identifier and
`AlternativeIdentifier` as the CACLR-based address identifier.
§4.4 describes `BU_BuildingID` as a **different building feature**
identifier. No official mapping between these different namespaces has
been established.

## New bounded original-source gate

The runner
`research_runners/lu_geobase_addresses_20260401_original_v0.py`
verifies the full official publisher MD5, independently records actual
ZIP/GPKG SHA-256, safely extracts at most one GeoPackage in ephemeral
temporary storage, opens SQLite **read-only**, checks GeoPackage
application ID, original layer CRS, geometry and field structure,
then emits original **layer names, column names and aggregate ID counts**
only. It never logs row values, CACLR identifiers, individual addresses,
coordinates, household records, insured exposures, source files or
crosswalk pairs. Synthetic tests and a dedicated standalone workflow
run against the exact source revision.

**Important:** this first test confirms publisher MD5 and computes an
observed original SHA-256; neither is a signed provenance guarantee.
Only later may that independently observed SHA be pinned as an immutable
source identity. The validator does not approve item-level rights,
national coverage, address-to-building identities or CAT model input.

## Future scientific challenge

If the original Addresses theme actually provides `AD_AddressID` and
`AlternativeIdentifier`, compare its *2026-04* CACLR fields at aggregate
level against the *2026-11* BD-Adresses `id_caclr_bat` using separately
original-verified immutable bytes. Do not assume identical population
across seven months or interpret missing IDs as deleted buildings.
First document source field definitions and one-to-many relationships.
A building↔address linkage requires a reviewed official relation or
separately adjudicated geometric candidates, not raw string join
between `id_caclr_bat` and `BU_BuildingID` (national raw overlap
measured **zero** in PR #1287).

**Execution status:** initial source/run pending. No original-file
SHA-256, record counts or released source fields are claimed here until
the exact GitHub job reports success.
