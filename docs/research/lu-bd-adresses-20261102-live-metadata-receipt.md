<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg ACT BD-Adresses 2026-11-02: official metadata canary execution

**2026-11-04. Research-only, no source admission.** This note connects the
existing official-source version-pinned parser
[`scripts/probe_lu_bd_adresses_metadata_v0.py`](../../scripts/probe_lu_bd_adresses_metadata_v0.py)
to a dedicated GitHub Actions metadata-only execution. This is intentionally
separate from the full official-source Buildings 2026 GeoPackage pipeline and
from geometry or insurer-portfolio model inputs.

## Why a live metadata receipt is necessary

The original [ACT BD-Adresses catalogue](https://data.public.lu/en/datasets/adresses-georeferencees-bd-adresses/)
lists a weekly updated set of georeferenced address points (dataset licence
CC0). Its web page currently identifies **2026-11-02** versions. The upstream
API resource IDs are *stable*, but published resource URLs, checksums and
timestamps can change; a passing test against a fabricated JSON payload
does not prove that the current publisher has the intended revision.

The existing 2026-11-02 parser deliberately pins only these three resources:

| Exact original ACT resource | Stable resource ID | Publisher catalogue MD5 |
| --- | --- | --- |
| [GeoJSON 20261102-033136](https://download.data.public.lu/resources/adresses-georeferencees-bd-adresses/20261102-033136/addresses.geojson) | `7b58cf20-cbb0-4970-83f7-53a277f691b8` | `16d7e4e2ccf735fea7ca0db26378281b` |
| [CSV 20261102-033122](https://download.data.public.lu/resources/adresses-georeferencees-bd-adresses/20261102-033122/addresses.csv) | `5cadc5b8-6a7d-4283-87bc-f9e58dd771f7` | `946114c1a24b49471b580bc225e4cb25` |
| [SHP 20261102-033150](https://download.data.public.lu/resources/adresses-georeferencees-bd-adresses/20261102-033150/addresses-shp.zip) | `2a17ddc2-b961-45ce-83a2-be751d3af9b8` | `3b1bb33c8c1a4fc2bbd95d5fb6317d29` |

The checksum is **publisher-announced MD5**, not a cryptographic
authenticity proof. The original bytes and SHA-256 have NOT been downloaded or
independently measured by this metadata canary. A version mismatch must
**fail closed** rather than silently rewriting the historical source identity.

## Live workflow contract

[`luxembourg-bd-adresses-20261102-metadata.yml`](../../.github/workflows/luxembourg-bd-adresses-20261102-metadata.yml)
runs the existing mocked metadata/parser safety tests first, then:

```sh
python scripts/probe_lu_bd_adresses_metadata_v0.py --live
```

The opt-in parser performs **exactly three GET requests** to versioned source
metadata endpoints under `https://data.public.lu/api/1/datasets/...`.
It caps each JSON response at 128 KiB; accepts no redirects, arbitrary URLs,
credentials, user-chosen source paths or third-party hosts. It verifies original
resource ID, fixed filename, path/vintage, expected publisher checksum,
bounded byte-size field, and publication-date string. All live output is
metadata-only, including response hash and explicit non-admission flags. It
does not request a GeoJSON/CSV/SHP download, emit address rows or geometry,
write to the insurance database or create a model manifest.

The CI workflow is distinct from the currently edited central CI file
and so does not overlap with open source-quality PRs. If publisher API
responses differ from the assumed schema or the release moves again, the job
fails. Diagnose that failure against the *current official original*, rather
than weakening path, digest or date validations.

## Caveats and next real-data gate

- The ACT source documentation explicitly says address points can represent
  cadastral parcel or largest-building centroids, **not real entrances**;
  multiple addresses may have the same coordinates and coverage is incomplete.
- ACT BD-Adresses and ACT BD-L-GeoBase Buildings are the **same provider
  family**, not independently observed geospatial truth. The 2026 Buildings
  original was already validated in the separate existing workflow.
- **Next**, only after a passing live metadata receipt and source-rights
  review, fetch a single exactly pinned original CSV/GeoJSON into a *temporary
  authorized runner*, verify the full published digest, produce an observed
  SHA-256 and aggregate-only field/CRS/count/duplicate/coordinate diagnostics.
  A true independent holdout and adjudicated building correspondence must
  precede any real model admission.

A passing metadata workflow proves only **the resource metadata matches
the frozen 2026-11-02 catalogue**, not source bytes, real building identity,
insurance interest, values or CAT loss suitability.

## Actual publisher API metadata receipt (2026-11-04)

The first exact-head original-source GitHub Action run
[41799217860](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41799217860)
**passed** all 11 synthetic parser/security tests and the three real fixed
publisher metadata API GETs. GitHub's job output, recorded at about
**2026-11-04 08:24:30 UTC**, returned the following provider-advertised
file sizes and metadata-response SHA-256 hashes:

| Exact frozen resource | API-reported file size (bytes) | Metadata response SHA-256 | Published file MD5 matches |
| --- | ---: | --- | --- |
| 2026-11-02 GeoJSON | 80,901,702 | `602a9c8eafba6d8cfddd071be4642170fb2202d4b37ef8ae47da43b4fc99bf49` | Yes |
| 2026-11-02 CSV | 28,209,815 | `549f30d08e1b50fe9153f4807b58c5b559ff9d94107924a0accd229ad065c62a` | Yes |
| 2026-11-02 Shapefile ZIP | 19,700,240 | `ed73882663ab19a0a2063ee00e9086f0f378b34e386a39c4c850b615093e5ea2` | Yes |

All three resource IDs, fixed download paths, publisher MD5 values, timestamps
and expected bounded sizes matched the previously pinned November 2 metadata
contract. The report returned `asset_bytes_downloaded: 0` and explicit
non-admission flags. The SHA-256 values above fingerprint **metadata JSON
responses**, not ZIP/CSV/GeoJSON content. They may change with metadata JSON
formatting or non-content attributes; do not use them in lieu of original
source-file SHA-256, signed provenance, or a complete source licence review.

**Next gate remains outstanding:** retrieve only one frozen original dataset
file into an ephemeral authorized worker, independently calculate the actual
file MD5/SHA-256 and review original columns, number of observed address points,
coordinate precision, and any repeated coordinates. Full metadata agreement
is not proof of valid location truth or an insured building crosswalk.
