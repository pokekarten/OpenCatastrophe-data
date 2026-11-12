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

