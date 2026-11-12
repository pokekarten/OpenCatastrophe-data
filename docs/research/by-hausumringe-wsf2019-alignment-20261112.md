<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Bavaria public Hausumringe × original DLR WSF2019: offline spatial preflight (2026-11-12)

## Source IDs and real evidence

- Reuse existing landscape candidate `de.bayern.hausumringe` in `landscape/sources-europe-building-validation-context.json`. Do **not** duplicate source IDs.
- [Bayerische Vermessungsverwaltung open download](https://geodaten.bayern.de/opengeodata/OpenDataDetail.html?pn=hausumringe) and [official Geoportal Hausumringe record](https://geoportal.bayern.de/geoportalbayern/details-suche?0&resId=eb2bc103-d980-4c74-bb86-d850c92ebac6): cadastral-derived building and structure outlines (polygons), not private owners or insured TIV.
- [Public ATOM download](https://geoportal.bayern.de/gdiadmin/ausgabe/ATOM_SERVICE/eb2bc103-d980-4c74-bb86-d850c92ebac6). Source product is a regional Shapefile, normally ETRS89 / UTM 32 (EPSG:25832); components include original .shp, .shx, .dbf, .prj. Download/report exact regional release date and SHA-256 after direct source inspection.
- [City of Munich official open-data page](https://opendata.muenchen.de/dataset/g_stadtkarte_wms) says its BVV house outlines carry **CC BY 4.0** and attribution to BVV. Confirm the exact downloaded original archive's rights before actual geodata retention or redistribution.
- **Never substitute** the [access-controlled Bavarian ALKIS simplified WFS](https://geodatenonline.bayern.de/geodatenonline/seiten/wfs_alkis), available only to authorised customers. National federal HU-DE has separate restrictive licensing; open Bavarian HU-BY does not confer federal HU-DE rights.

## Official regional download identity and restricted original-byte probe

On 2026-11-12, the actual [BVV public Hausumringe regional KML index](https://geodaten.bayern.de/odd/m/3/daten/hausumringe/bezirk/kml/HU_regierungsbezirk.kml) was obtained as original XML/KML. Its `Regierungsbezirk Oberbayern` Placemark contains an explicit [public Oberbayern original ZIP URL](https://geodaten.bayern.de/odd/m/3/daten/hausumringe/bezirk/data/091_Oberbayern_Hausumringe.zip) and reports **one ZIP, approximately 162 MB**. That URL originates from the official KML; it is not guessed or a restricted ALKIS interface.

A separately scoped external **4,096-byte HTTP Range** retrieval on that fixed ZIP link returned the standard `PK\x03\x04` local-file ZIP signature and the first original member name `hausumringe.dbf`; original ZIP MIME was `application/zip`. This is **only** a bounded public transport/format observation. The externally observed response does not establish full archive SHA, original Shape/PRJ content, all file names, snapshot/survey date, completeness, source rights for bulk redistribution or original local building polygons.

`research_runners/by_hausumringe_oberbayern_zip_prefix_v0.py` and the separate fixed [trusted-main-only Actions workflow](../../.github/workflows/by-hausumringe-oberbayern-zip-prefix.yml) now implement a strict source-specific one-shot HTTP 206 `bytes=0-4095` verification and byte-hash receipt, subject to offline synthetic negative-case tests. Pull requests run **offline only**; on `main`, a failed provider read is reported as `FAILED` even when diagnostic network failures are non-gating. The workflow never requests the whole original 162 MB ZIP or stores source bytes, and it makes no model-admission claim.

The original DLR WSF2019 32×32 raster samples #28 and #29 **have** been independently decoded and verified in [main GitHub Actions run 43226483288](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43226483288): pure Python LZW and GDAL 3.12.2 agree on original TIFF header and compressed-block SHA-256, pixel classes 0/255, EPSG:4326 and both exact Neon mask hashes.

**No original Bavarian open-download Hausumringe Shapefile has yet been obtained, version-frozen, spatially sampled, independently hashed, or checked against these WSF windows. No real-world building/WSF overlap or loss validation is claimed by this change.**

## Source-specific open rights and original ZIP central-directory evidence (2026-11-12)

**Primary-source usage rights:** the Bavarian Vermessungsverwaltung's
[Gebühren- und Preisliste dated 2026-07-01](https://www.ldbv.bayern.de/mam/ldbv/dateien/gebuehren_und_preisliste.pdf),
section **7.4 Hausumringe**, explicitly states **kostenfrei, Lizenz CC BY 4.0**
for the house-outline product through Download, APIs or Geodatendienste.
For this *specific Bavarian HU-BY open product*, CC BY 4.0 permits commercial
reuse subject to attribution, a license link and indication of changes.
Do not extrapolate to the restricted ALKIS WFS, owner/address datasets,
federal HU-DE, or third-party rights. A licence signal is **not** a scientific
validation or insured-location/TIV approval. The original catalogue
`rights_review_status=not_reviewed` is retained until a scoped contract and
database rights review is committed; do not silently change it.

**Format/source semantics:** the LDBV
[Hausumringe Datenformatbeschreibung (10/2024)](https://www.ldbv.bayern.de/mam/ldbv/dateien/hausumringe-by_datenformatbeschreibung.pdf)
names exactly four Shapefile components `hausumringe.shp`, `.shx`,
`.dbf`, `.prj`; defaults to ETRS89/UTM zone 32 (EPSG:25832);
includes object types other than standalone residential buildings, and
carries municipal AGS. Data are refreshed quarterly: **the publication
of that specification does not establish the 2026 regional archive's
original observation vintage**.

A separately bounded original **4,096-byte HTTP Range from the ZIP end**
reported the EOCD at the final 22 bytes; the original central directory
claimed **four** Shape components with exactly these file lengths:

| Original ZIP directory member | Compressed bytes (claimed) | Uncompressed bytes (claimed) |
| --- | ---: | ---: |
| `hausumringe.dbf` | 275,557 | 27,037,425 |
| `hausumringe.prj` | 256 | 388 |
| `hausumringe.shp` | 166,172,236 | 501,212,696 |
| `hausumringe.shx` | 7,851,126 | 21,629,988 |

The directory offset is **174,299,355**, size **388 bytes**,
original archive length **174,299,765 bytes**. All member data extents
plus local headers are contiguous in this *directory claim*.
`research_runners/by_hausumringe_oberbayern_zip_central_v0.py`
strictly checks this profile via one exact `bytes=174295669-174299764`
HTTP 206; PR tests use synthetic central directories only.
The production `main` run is a **separate acceptance requirement**
and may block if the object changes.

This is **central-directory original metadata**, not CRC32 checking of
decompressed Shape bytes, a full archive SHA-256, proof of actual projection
text, independent feature count, full region completeness or an observed
WSF↔official polygon comparison. The next scientifically justified step
is a **controlled full-member provenance/import** only when necessary and
with explicit footprint-only storage scope; neither the testing workflow
nor the model registry should automatically ingest this 174.3-MB ZIP.

## Original ZIP projection .prj: complete single member proof (2026-11-12)

Following the independently reviewed [main ZIP central directory proof](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43291927411),
the exact original `hausumringe.prj` member was also fetched as **one bounded
301-byte public HTTP Range** `bytes=275602-275902`. The original 45-byte ZIP
local header identifies a 256-byte raw-DEFLATE member with **388** unpacked
bytes; original directory and local header CRC32 `d49ececb` agreed with
the independently recomputed CRC32 of the unpacked WKT.

Original member SHA-256 fingerprints (independently observed, not a whole
ZIP hash): compressed deflate bytes
`055f581691a9def92166569c959a0713d4c0e34cf746d1238821ad18caaea2c8`;
uncompressed 388-byte WKT
`03c412dbe0da64f769d15d4de5ee08309680542a54630d3e8baf8d82d0091670`.
The WKT identifies `ETRS89_UTM_zone_32N`; a separate pyproj 3.7.2 parse
independently maps it to **EPSG:25832**. This validates the *real original
projection file* for the cadastral-to-WSF conversion, not geometry correctness.

`research_runners/by_hausumringe_oberbayern_prj_v0.py` captures the complete
301-byte original only transiently; its exact provider request and CRC/SHA
and CRS checks run **only on trusted main/manual GitHub workflows** after the
ZIP prefix and central directory succeeded. All PR tests run on **synthetic
raw-DEFLATE WKT bytes** with pinned PROJ, not original provider content.
The independent accepted production run remains necessary before claiming
the source CRS has been reverified in GitHub.

No original SHP member (~166 MB compressed), building polygon, raw address,
full ZIP SHA256, source vintage or model admission was obtained or authorized.

## Original source DBF member: bounded table and row-count gate (2026-11-12)

The original official Oberbayern ZIP central directory independently recorded
`hausumringe.dbf`: **275,557 DEFLATE bytes, 27,037,425 unpacked bytes**,
CRC32 `67324194`, at ZIP local header byte offset 0. The local ZIP member
extends to byte **275,601**, directly followed by the previously verified
original projection member at 275,602. Consequently, a **single read-only
HTTP 206 Range `bytes=0-275601`** is sufficient to retrieve the *complete
original compressed DBF*, without the huge original polygon (`.shp`) file.

The source's original `.shx` central directory claims an uncompressed index
length of **21,629,988 bytes**. Shapefile index format reserves 100 bytes
for the header and 8 bytes per feature offset/length entry, implying
**2,703,736 index entries**; the original DBF directory length is also
consistent with 65-byte dBase III header + `2,703,736 × 10` bytes per row.
These counts are **arithmetic expectations from ZIP metadata**, not yet
independently verified records, survey objects or individual usable
buildings.

`research_runners/by_hausumringe_oberbayern_dbf_v0.py` now implements
that single-source DBF member check. It requires fixed URL, HTTP 206,
original archive total length, 275,602-byte exact response, no redirects,
valid local ZIP header and DEFLATE, CRC32 recomputed over a **bounded
27-MB decompression**, and source DBF format/version/date/header/field
length/record count validation. It independently checks the DBF row count
against the `.shx` **directory-reported** index cardinality and emits only
an anonymous numeric active/deleted record summary, original SHA-256/CRC32
receipts, and the DBF header file date (explicitly **not** cadastral survey
vintage). No IDs, source attribute values, full polygon geometries or
provider bytes are emitted or retained.

PR-head runs are **offline synthetic only**. The first real source-DBF
acceptance requires the exact trusted `main` Actions provider-step outcome
after all prior source prefix/central-directory/projection checks succeed.
Until then there is **no live DBF record proof**. Even if it succeeds,
the `.shx` file and `.shp` footprint geometries remain independently
unvalidated; no actual building count, matched 2019 WSF score, TIV,
insurer exposure, model-input approval or automatic scientific admission
is claimed.

## 2026-11-12 original DBF verified; index-only spatial integrity next

The preceding DBF section described a proposed source test. **It has now
completed on trusted main:** [GitHub Actions 43306712553](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43306712553)
inspected all **275,557 original ZIP-compressed DBF bytes** (275,602 bytes
including ZIP local header) with an exact HTTP 206 source Range, and
independently decoded **27,037,425** uncompressed original bytes under
a hard cap. It verified original CRC32 `67324194`, compressed SHA-256
`21f613c4ac435f45197c87bf8143be8525976a3de7a4c7713c6c09b0643ee1df`,
uncompressed SHA-256
`69af1705c347ab9e233598b0bf82c8665239a4bc19f1e516d35b6634e02515ed`,
dBase III header, **2,703,736 active / 0 deleted records**, one nine-byte
attribute field and DBF file-header *modification* date **2026-10-01**.
This metadata is **not** source cadastral survey vintage and the row
count is not a verified count of physically distinct, insurable buildings.

**Next source index proof**: the same official ZIP declares its `.shx`
member at byte **166,448,184**, total local-member request **7,851,171
bytes**, of which **7,851,126** are ZIP-compressed index data. A single
original HTTP Range `bytes=166448184-174299354` can check original
CRC32 `f6d2bbb8`, the complete 21,629,988-byte Shapefile index,
source file-code 9994/version 1000/Polygon type 5, exactly **2,703,736**
index entries, and all index-record byte offsets for strict contiguity.
The final index offset must land at **501,212,696** uncompressed SHP bytes
as **claimed by ZIP central directory only**. The original SHP source
itself is **not independently downloaded or hashed**.

`research_runners/by_hausumringe_oberbayern_shx_v0.py` and synthetic
tests implement this exact bounded index-only proof. On PR heads there
is no network call; trusted `main` executes it only after original
ZIP prefix/central, projection and DBF checks all succeeded. Inspect
the provider-step outcome and original SHA/CRC receipt in main logs
before claiming index verification. Even after success, the 2.7 million
indices establish **structural source file consistency**, not actual
polygon geometry quality, observed 2019 building footprints, insured
TIV or CAT model admission.

## Original official SHP member: controlled full stream, restricted 2-window geometry (2026-11-12)

**Source-only scientific research, not model admission.**
Existing original primary source evidence was generated on trusted main at
[GitHub Actions run 43308079377](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43308079377):
fully decoded original DBF records **2,703,736**, all **2,703,736** original
SHX offsets continuous and ending exactly at **501,212,696** uncompressed
SHP bytes, and exact original projection EPSG:25832. Full original SHP
geometry had **not** been fetched or checked in those source runs.

The new `research_runners/by_hausumringe_oberbayern_shp_windows_v0.py`
and dedicated
[Actions workflow](../../.github/workflows/by-hausumringe-original-shp-munich-windows.yml)
introduce a carefully bounded and **one-time on `main` push** full-member
network stream of the *original* 166,172,236-byte DEFLATE ZIP SHP payload
(plus 45-byte local ZIP header, exact HTTP 206 `Range:
bytes=275903-166448183`; 166,172,281 source bytes total). No arbitrary
URL, downloads from private ALKIS, redirects, retry crawls, or full
ZIP files are authorized. It verifies the original ZIP member header,
CRC32 `55540a66`, complete source compressed/uncompressed SHA-256,
501,212,696 original unpacked bytes, binary Shapefile 9994/1000/Polygon 5,
and all 2,703,736 sequential record IDs and byte boundaries.

Streaming parser drops every original polygon except **at most 2,048
polygon candidates per independently GDAL-verified WSF native 32x32
Munich grid** (fixed bounding boxes for Neon research samples **#28 and
#29**). Selected footprints are processed exclusively in process RAM:
record 2D polygon geometry, original EPSG:25832 to EPSG:4326 using
independent `pyproj==3.7.2`, then fractional area coverage on
the original native 32x32 pixel grid using `shapely==2.1.2`.
The report may emit **only** aggregate source counts, area, fixed
2048-byte **uint16 little-endian 32x32 per-cell fractional footprint
coverage grids**, derived grid SHA256 and review metadata. Original
polygon vertices, record offsets, cadastral identifiers, raw SHP
source bytes and complete provider archive are never persisted in
Git, SQL, log output or workflow artifacts.

PR heads run **synthetic-only** geometry/stream tests with pinned numpy,
shapely and pyproj; only reviewed main push or explicit trusted manual
dispatch may fetch the full original public source.
The streaming job is a non-blocking diagnostic with an **explicit
actual provider-step SUCCESS/FAILURE** output, not a silently green
scientific approval. On failure keep original source incomplete
and record the scientific blocker without data admission.

After a successful source receipt, the per-cell derived coverage
must still be joined **outside Git** against the independently verified
Neon original DLR-WFS 2019 pixel masks (#28/#29), preserving their
immutable mask SHA256 fingerprints, to calculate real matched *area*
statistics. The two different source years introduce genuine
2019-vs-2026 capture/vintage confounding. No population-level
building-exposure validation, false-positive rate, insurance TIV or
model input can be inferred from two native 32x32 windows or from
the counts of shapefile records.

## Offline comparison method (synthetic-only until source acquired)

`research_runners/by_hausumringe_wsf2019_spatial_gate_v0.py` accepts:

1. A *local, uncommitted* JSON export of one original Neon `research.source_sample_v0` row with integer `sample_id` 28 or 29, `source_id`, `sample_kind`, `provider_response_sha256`, `model_input_approved=false` and the unmodified nested `sample_json` object. The inner 32x32 binary rows must exactly match the independently verified original source SHA-256 and row fingerprint.
2. A *local, uncommitted* source-framed FeatureCollection of 1–256 polygons extracted under review from the official **open-download** BVV Shapefile, *original* EPSG:25832 coordinates, `source_id="de.bayern.hausumringe"`, `source_crs="EPSG:25832"`, `original_format="Shapefile"`, `license="CC-BY-4.0"`, `source_is_official_open_data=true`, `source_snapshot_date`, and *reported* `original_archive_sha256`. Both `independently_verified_source_asset` and `roi_complete_for_frozen_bbox` MUST be `false`: this runner cannot attest independent provider identity or completeness. The non-RFC7946 FeatureCollection is **not** a claim of standard GeoJSON WGS84 coordinate semantics.

The script has **no network access** and does no database writes:

```bash
python -m research_runners.by_hausumringe_wsf2019_spatial_gate_v0 \
  --neon-sample /private/neon-wsf2019-verified-sample.json \
  --bvv-geojson /private/hu-by-extracted-utm32-polygons.json
```

After fail-closed identity, geometry, CRS, bounds, size and topology checks it converts original ETRS89/UTM32 polygons via pyproj to EPSG:4326 and then the precise native WSF pixel grid, clips them to the **same** 32×32 support, unions overlapping building polygons, and uses **fractional cell-area GEOS polygon intersections**, not centre-of-cell approximations. It emits only anonymous aggregate partial-reference area, intersection, IoU, recall, precision and exclusion area. It never outputs original polygon coordinates, feature IDs, raster pixels or individual addresses.

The dedicated [offline synthetic workflow](../../.github/workflows/by-hausumringe-wsf2019-spatial-gate.yml) pins Shapely 2.1.2 and pyproj 3.7.2, requires both modules to import, and tests positive/disjoint/offset polygon overlap, double-counting, invalid polygon topology, wrong EPSG/licensing and fabricated masks. **Green CI proves only the code's behaviour on synthetic fixtures; not official-source connectivity or actual spatial accuracy.**

## Outstanding admission barriers

- **Real original source and rights**: first obtain the public original BVV regional archive; independently verify licence/release, complete original SHA-256 and Shape member provenance. Do not contact paid ALKIS endpoints.
- **Vintage and completeness**: WSF 2019 vs recent quarterly Bavarian cadastral snapshot causes real temporal mismatch; a limited building excerpt cannot prove complete population-level coverage. All reported metrics intentionally say `partial_reference`. Never infer historical 2019 official building counts from 2026 data.
- **Semantics and independence**: WSF 255 means remotely sensed settlement-area positive pixels; it is **not** an individual cadastral building count, residential classification, TIV, site value or insurer loss. Bayerische LoD2 and HU-BY can share an ALKIS geometry origin; they are not independent survey confirmations of each other.
- **Science gates**: support alignment, full original reference validity, source vintage, survey coverage, omission/commission/false positives, geographic holdout regions and quantitative error before any exposure/calibration claim.
- **Status**: `model_input_approved=false`; zero new model approvals, no raw provider bytes in Git/Neon, no new rights grant.



## Original public BVV ATOM service and dataset feeds verified — 2026-11-12

Two **actual anonymous, read-only original issuer ATOM GETs** succeeded
independently of the existing original BVV ZIP/DBF/SHX investigations.
No building geometry, original KML-region layer, Shapefile or archive
bytes were downloaded, redistributed or inserted into Neon in these
two requests.

| Actual original XML feed | Official issuer URL | Exact original response byte count | SHA-256 of that response | Neon research sample |
| --- | --- | ---: | --- | ---: |
| INSPRE-defined Hausumringe **service** | [ATOM_SERVICE](https://geoportal.bayern.de/gdiadmin/ausgabe/ATOM_SERVICE/eb2bc103-d980-4c74-bb86-d850c92ebac6) | **2,946 bytes** | `152c3610d68d5288ffcc187ef4d89754336d3978fc10ee41f64cdf9efbff45d7` | **53** |
| Hausumringe **dataset** | [ATOM_DATASET](https://geoportal.bayern.de/gdiadmin/ausgabe/ATOM_DATASET/eb2bc103-d980-4c74-bb86-d850c92ebac6) | **1,801 bytes** | `187b873bc66a826b04bd275b3b106cc9e0a675bb167a2cd25c3212f891fb8b3f` | **54** |

Both exact provider responses declared `application/atom+xml`. This
live test established original issuer/feed identity, a traversable
service-to-dataset link, publication contact and a dataset-to-regional
KML index pointer. It **did not** independently expose HTTP status
headers via the delegated transport, and therefore does **not**
claim an original HTTP-200 status proof. The feed `updated` timestamps
are mutable catalogue-state metadata; the two hashes are original
response receipts, **not version-stable original Shapefile identities**.

**Important source-rights metadata asymmetry:** the top-level
Bavarian ATOM **service** expressly states `cc-by/4.0` plus
the exact mandatory attribution
**“Datenquelle: Bayerische Vermessungsverwaltung – www.geodaten.bayern.de”**;
the underlying **dataset ATOM** instead has `<rights>TODO</rights>`
at feed and entry level. This is **incomplete rights metadata** in
the dataset feed, *not* evidence that the publisher expressly prohibits
use. The official [BVV Gebühren- und Preisliste, §7.4](https://www.ldbv.bayern.de/mam/ldbv/dateien/gebuehren_und_preisliste.pdf)
and the issuer's [AdV product rights review](https://www.distributions.informationgrid.eu/freitextsuche?inspire=inspire_false&productgroup=at15&q=view&type=)
independently establish **CC BY 4.0 for the Bavarian HU-BY open
Hausumringe product** with attribution and modification notice.
That product-scoped verdict does **not** transfer to protected
ALKIS WFS, individual owners, federal HU-DE or third-party datasets.

Both live metadata receipts were added directly to the separate
insurance Neon `research.source_sample_v0` as
`sample_kind=public_metadata`, with source-response SHA-256 and
canonical JSONB SHA-256:

- `sample_id=53`, source `de.bayern.hausumringe`, source SHA above,
  canonical JSONB SHA-256
  `b2ab25ccfd07a6a2dd2f22e72f3b44f66d8729ed080918ec7f61eed47321b8b4`.
- `sample_id=54`, same candidate, source SHA above,
  canonical JSONB SHA-256
  `6b400c26ad40844207e733d831745939b71d4eaae714bb6841aeecb8c6729d1a`,
  with `dataset_atom_rights_field_todo=true`.

**No** original XML bodies persisted in Neon or Git, no new
original polygon/geometry interpretation, no historic 2020 building
snapshot and no scientific-model admission. The candidate remains
`actual_sample_state=metadata_only` with existing product-scoped
`commercial_reuse_verdict=allowed_verified` and
`admission_status=not_admitted`.

Read-only research evidence replay in `insurance-risk-core`:

```sql
SELECT sample_id, source_id, sample_kind, provider_response_sha256,
       sample_sha256=encode(sha256(convert_to(sample_json::text,'UTF8')),'hex')
         AS stored_jsonb_hash_valid,
       sample_json->>'feed_kind' AS original_feed,
       sample_json->>'dataset_atom_rights_field_todo' AS rights_placeholder,
       model_input_approved, source_byte_persistence_authorized
FROM research.source_sample_v0 WHERE sample_id IN (53,54)
ORDER BY sample_id;
```

The existing original **Oberbayern** ZIP index/DBF/SHX proofs remain
separate and stronger regarding actual official file structure:
2,703,736 active DBF entries and matching original index length
are now evidenced, with original **EPSG:25832** projection. Yet the
~501 MB *uncompressed original .shp polygon member* and its
individual geometries have **not** been independently validated.
Neither the pre-existing WSF2019 comparison preflight nor the separate
GHSL E2020/GDAL source-replay work should convert that archive-index
count into an asserted count of distinct insurable buildings or use a
2026 snapshot to imply unbiased 2020 validation.
