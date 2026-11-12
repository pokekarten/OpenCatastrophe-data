<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Oberbayern HU-BY original Shapefile — bounded first Polygon proof

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
