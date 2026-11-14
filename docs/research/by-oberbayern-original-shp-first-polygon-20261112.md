<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Oberbayern HU-BY original Shapefile — bounded first Polygon proof

**Successful actual trusted-main source run:** [GitHub Actions #43320212959](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43320212959), merged original source commit `93386a86ddf383824de04daad9d76557d6c24e03`, first original Polygon record has now been decoded successfully. This remains a **single-source-record structural receipt**, not a 2.7-million-feature scientific admission or 2020 footprint comparison.

**Source scope:** one public, official Bavarian Vermessungsverwaltung
Hausumringe *Oberbayern* 2026 regional ZIP, not private ALKIS WFS and
not federal HU-DE. Existing [BVV original ZIP/DBF/SHX/PRJ research
receipts](by-hausumringe-wsf2019-alignment-20261112.md)
independently prove the original ZIP directory layout, 2,703,736
DBF active rows, matching SHX index offsets and original EPSG:25832
projection. **No individual original SHP Polygon record or complete
regional building geometry has been independently proven before this
new source probe succeeds.**

## Publisher, rights and exact byte budget

Original regional ZIP is directly listed by the official
[BVV Hausumringe regional KML index](https://geodaten.bayern.de/odd/m/3/daten/hausumringe/bezirk/kml/HU_regierungsbezirk.kml):

`https://geodaten.bayern.de/odd/m/3/daten/hausumringe/bezirk/data/091_Oberbayern_Hausumringe.zip`

The separate original issuer [BVV Gebühren-/Preisliste
§7.4](https://www.ldbv.bayern.de/mam/ldbv/dateien/gebuehren_und_preisliste.pdf)
declares **CC BY 4.0 for this open HU-BY product**, commercial
use permitted with source acknowledgement and modification notice.
Exact attribution:
**“Datenquelle: Bayerische Vermessungsverwaltung – www.geodaten.bayern.de”**.
The original anonymous ATOM service feed also declares CC BY 4.0,
although its linked dataset feed uses a `<rights>TODO</rights>`
placeholder; this inconsistency is recorded separately in
Neon metadata receipts **#53/#54** and does not extend rights
to closed ALKIS WFS or national HU-DE.

A single **external read-only source Range observation** on 2026-11-12
returned exactly **49,197 original ZIP bytes**, original
`Content-Type: application/zip`, comprising 45 local ZIP header
bytes + the first 49,152 compressed bytes of the original SHP member.
The delegated external transport did **not** independently expose
HTTP 206/Content-Range headers, so the earlier inspection did **not**
claim those transport checks or actual decoded source geometry.
The observed original ZIP local header exactly matched the previously
verified original central directory:

| Original source field | Exact fixed observed value |
| --- | --- |
| Original regional ZIP length | **174,299,765 bytes** |
| Original SHP local ZIP offset | **275,903** |
| Frozen bounded Range | **bytes=275903-325099** (49,197 B) |
| Local member name | `hausumringe.shp` |
| ZIP version / encrypted flags / method | **20 / 0 / 8 (DEFLATE)** |
| ZIP local/directory CRC32 | `55540a66` (**not** revalidated over the full SHP) |
| Original compressed SHP total length | **166,172,236 bytes** |
| Original uncompressed SHP file length | **501,212,696 bytes** |
| Native SHP data CRS source | **EPSG:25832**, from previously verified original `.prj` |

The new source-run implementation is
`research_runners/by_hausumringe_oberbayern_shp_first_original_v0.py`
with deterministic synthetic tests
`tests/test_by_hausumringe_oberbayern_shp_first_original_v0.py`.
It requires one **exact reviewed public HTTPS 206** request with
the complete original Content-Range, source total size and file MIME.
No free-form source URL, date, region, query, ZIP entry, offset or
additional byte request is permitted. No redirects, retries, pagination
or entire 174-MB ZIP download.

## Scientific native preview and fail-closed admission

The exact 49,152 source raw DEFLATE bytes are unpacked transiently
with a **4-MB maximum output cap**. This is deliberately an *incomplete*
compressed-member prefix: ZIP full-member CRC, 501-MB original SHP
SHA-256 and all 2.7 million source polygons **are not checked**.
The source's first 100-byte native Shapefile header must have
file code **9994**, version **1000**, shape type **Polygon (5)**,
size **501,212,696**, and broad finite source bounds compatible
with official ETRS89/UTM32 coordinates.

The source runner then requires exactly one **complete first original
Polygon record** inside the decompressed bounded prefix, checking
record framing, shape tag, part/point counts, ring closure, numeric
coordinate finiteness/UTM source bounds, and record-bbox conservation.
If any item is absent or malformed, the original source test
**fails closed**. The only permitted output is anonymous numeric
structure statistics and SHA-256 hashes of the original received
compressed prefix, partial decoded source and first content record.
No building coordinates, first-building bbox, vertices,
address, feature identifiers, raw polygons, entire decompressed
member, screenshot, geometry or insurer portfolio data may be
saved to Git, Neon or Actions artifacts.

`.github/workflows/by-hausumringe-first-shp-original.yml`
runs **synthetic-only** in pull requests. Only after reviewed merge
to `main` or a manual trusted workflow dispatch is one source
Range requested on an ephemeral runner. PR CI success **is not** a
claim of real original Polygon acquisition; the trusted-main source
step must return success and a first-record receipt.

**Still blocked:** complete original SHP/ZIP SHA-256, independent
GEOS validity for the entire dataset, original survey snapshot
vintage, geographic completeness around the fixed GHSL E2020
32×32 window, exact individual building counts, modelled
BUILT-S/V accuracy against a historical 2020 reference, insured
TIV, any OED exposure ingestion and CAT model approval.

## Actual first source Polygon success and Neon staging — 2026-11-12

**Verified first-party original source execution:**
[trusted main GitHub Actions #43320212959](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43320212959),
from reviewed merge commit
`93386a86ddf383824de04daad9d76557d6c24e03`.
The source-specific synthetic suite and full PR Python 3.11–3.14 / Berlin CI
checks passed prior to
[PR #1523 merge](https://github.com/pokekarten/OpenCatastrophe-data/pull/1523).
The main-only source action then **succeeded** on one exact official original
`hausumringe.shp` ZIP-member prefix, returning confirmed HTTP 206,
the exact fixed `bytes=275903-325099/174299765` response identity,
original ZIP header and SHP header, and the first complete native Polygon.

| Original first-party verified fact | Exact proven result |
| --- | --- |
| Original publisher source | Official BVV Oberbayern open Hausumringe ZIP (CC BY 4.0, attribution) |
| Original live UTC | **2026-11-12 22:28:33 UTC** |
| Exact original ranged ZIP response bytes | **49,197 bytes** |
| Original exact ranged HTTP response SHA-256 | `8a3c95bbbca493b192f6923fa4b6060798f561775f647bd34ffd4fc3af316f80` |
| ZIP raw-DEFLATE original SHP compressed-prefix SHA-256 | `e484f0225b8a85677c6824b258ffddd5833d727f1cc154667e05787cb5104b80` |
| Original bounded decompressed leading SHP bytes | **147,376** |
| Original bounded decompressed prefix SHA-256 | `fad5abf8ffcd4421acb35b338e7b262c53a780d847318381b411547c86457803` |
| Complete 100-byte native original SHP header SHA-256 | `f312c12beea148041db5ebf9727ad2aca59e036bef4665aae47402008f02bb09` |
| Original first complete native Polygon record content SHA-256 | `f6c7b5bc74f1d040a7280f0eb238c0f007aa6126c8c711f71f255b4f6f0c00ab` |
| Original first record type | **Polygon (5)** |
| Original first record rings / vertices | **1 ring, 7 points** |
| Ring closure and internal bbox vs all points | **Both independently checked true** |
| Independent GEOS/Shapely validity of original Polygon | **Not yet tested** |
| Exact whole ZIP/SHP byte hash or all features | **Not tested** |
| Original cadastre survey snapshot date | **Unverified** |

The source runner verified all seven original shape coordinate inputs as
finite and within the frozen source's broad EPSG:25832 bounding envelope,
but **emitted neither individual source coordinates nor the first
Polygon's bbox**, and did not persist original source bytes, geometry,
identifiers, ring vertex arrays or asset locations.

**Stored directly in the separate insurance Neon research DB:**

- `research.source_sample_v0.sample_id=61`,
  `source_id=de.bayern.hausumringe`,
  `sample_kind=observed_values` (one *original* polygon's structure,
  not an insurance loss or whole inventory);
- `provider_response_sha256` = exact original 49,197-byte
  source range hash `8a3c95bbbca493b192f6923fa4b6060798f561775f647bd34ffd4fc3af316f80`;
- canonical Neon JSONB-SHA-256
  `6d9d6f30f065822bc9a3a985f2db336d58bd87ba6570794cb2d37ea95559607d`;
- product-scoped **CC BY 4.0** backed by the original BVV
  `Gebühren- und Preisliste` §7.4 and feed, attribution unchanged;
  linked dataset ATOM rights tag `TODO` independently recorded as
  a metadata inconsistency in #53/54;
- both `research_only=true` and
  `model_input_approved=false`,
  `source_byte_persistence_authorized=false`;
- candidate advanced only in this **first-record-source research
  scope** from `actual_sample_state=metadata_only` to
  `collected_rights_cleared` while
  `commercial_reuse_verdict=allowed_verified` remains source-scoped
  and `admission_status=not_admitted` remains unchanged.

Safe *read-only* research replay:

```sql
SELECT sample_id, source_id, sample_kind, provider_response_sha256,
       sample_sha256=encode(sha256(convert_to(sample_json::text,'UTF8')),'hex')
          AS sample_hash_ok,
       sample_json->>'original_first_record_parts' AS original_parts,
       sample_json->>'original_first_record_points' AS original_points,
       sample_json->>'original_first_record_rings_closed' AS ring_closed,
       sample_json->>'source_geometry_observation_restricted_to_first_record' AS first_record_only,
       model_input_approved,source_byte_persistence_authorized
FROM research.source_sample_v0
WHERE sample_id=61 AND source_id='de.bayern.hausumringe';
```

**Strict remaining limitations:** one first native Polygon record
establishes only *bounded, first-record binary consistency*. It does
**not** validate all 2,703,736 source indexed records, GEOS
self-intersection validity, actual building counts or insurance
exposure, original SHP CRC or full file hash, publisher geometry
completeness, snapshot vintage, historical 2020 buildings, or
independent GHSL R2023A E2020 model validation. No insurer TIV,
OED exposure, hazard/vulnerability or CAT model admission.
