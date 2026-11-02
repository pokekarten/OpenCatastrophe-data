<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Overture global building crosswalk candidate preflight (2026-11-02)

## Pinned official upstream

- Publisher: Overture Maps Foundation; [official buildings guide](https://docs.overturemaps.org/guides/buildings/).
- Reviewed example release: **2026-10-21.0**, not a moving latest pointer.
- Exact original cloud prefix: https://overturemapswestus2.blob.core.windows.net/release/2026-10-21.0/theme=buildings/type=building/ (Azure); S3 bucket overturemaps-us-west-2, release/2026-10-21.0/theme=buildings/type=building/.
- [Official attribution and licensing](https://docs.overturemaps.org/attribution/): buildings theme ODbL, with source-lineage and obligations including OpenStreetMap, Esri, Microsoft and Google. Dataset availability is not permission for all derivatives; review actual source rights and commercial use per final use.
- [Official GERS reference](https://docs.overturemaps.org/gers/): a valid UUID is not proof of GERS registry membership, and building_part IDs do not carry the same GERS stability guarantee. Verification requires original registry, bridge and changelog evidence.
- Existing discovery candidate: overture.maps.buildings in landscape/sources-exposure-impact-validation.json. Do not duplicate or promote it.

## Shipped technical component

The offline script scripts/overture_building_identity_preflight_v0.py checks bounded local and Overture building polygon lists supplied as strictly structured JSON. It rejects duplicate JSON keys, nonfinite coordinates, invalid/self-intersecting polygons, impossible WGS84 coordinates, mixed release IDs, duplicate entities, UUID syntax problems, oversized batches, unexpected insurance fields and self-declared approvals.

It computes polygon intersection-over-union with fixed cutoff 0.75; **only reciprocal one-to-one pairs** become geometric *candidates*. A one-to-many or many-to-one fit is ambiguous. Any matching result remains research-only, and the output explicitly states:
- model_input_approved = false
- raw_data_import_authorized = false
- gers_registry_membership_verified = false
- geometry_crs_evidence_verified = false
- independent_validation_approved = false
- insured_value_estimated = false

Source families are caller-supplied, not independently verified. Identical OSM/Google/Microsoft-derived footprints in different products are **not** independent validation.

### Reproducible synthetic example

Save this entirely synthetic sample outside the repository as /private/synthetic-buildings.json:

    {
      "schema": "opencatastrophe-overture-building-crosswalk-preflight-v0",
      "overture_release": "2026-10-21.0",
      "geometry_crs": "EPSG:4326",
      "local_source": "synthetic-cadastre",
      "local_buildings": [
        {"local_id":"SYNTH-1","source_vintage":"2026-10-21",
         "geometry":{"type":"Polygon","coordinates":[[[10,50],[10.001,50],[10.001,50.001],[10,50.001],[10,50]]]}}
      ],
      "overture_buildings": [
        {"gers_id":"fea28f69-7afa-460c-b270-61ef74cd340c",
         "source_families":["synthetic-other"],
         "geometry":{"type":"Polygon","coordinates":[[[10,50],[10.001,50],[10.001,50.001],[10,50.001],[10,50]]]}}
      ]
    }

Run:

    python -m scripts.overture_building_identity_preflight_v0 --input /private/synthetic-buildings.json --expected-release 2026-10-21.0
    python -m unittest tests.test_overture_building_identity_preflight_v0 -v

The UUID is only an illustration, not proof of a real external building.

### Scientific and operational limits

- Polygon IoU is calculated in geographic WGS84 coordinate-plane units as a **local screening proxy**, not ellipsoidal equal-area geodetic matching. Real matches require a reviewed projected-geometry method, geodetic edge-case controls, verified CRS/source year, and manual adjudication of split/merge ambiguities.
- No source GeoParquet is downloaded by the script; no insurer portfolios, policies, insured values, loss curves, CAT runs or database writes.
- The script cannot grant licences, validate provider data provenance, establish GERS registry membership or certify an insurer-specific model.
- All inputs must come from independently legally authorized sources; never commit insurer/customer/claims or raw provider bytes to Git.

## Overture 2026 building source-ID bridge (additional offline preflight)

Official [bridge file documentation](https://docs.overturemaps.org/gers/bridge-files/) confirms that release `2026-10-21.0` exposes building crosswalks under the **new August-2026 partition layout**:

- `s3://overturemaps-us-west-2/bridgefiles/2026-10-21.0/provider=osm/theme=buildings/type=building/`
- Do **not** use the old `dataset=OpenStreetMap` directory path; partition key is `provider`, and `dataset` remains a column.
- The original Parquet file schema was verified from its footer: `id`, `dataset`, `record_id`, `update_time`, `resource`, `version`, `between`, `dataset_between`. Crucially, `provider`, `theme`, and `type` are **S3/Hive partition keys**, not row columns. Read exact partition identity from the pinned original object path, and project only `id`, `record_id`, and `dataset` into the narrow bridge preflight.
- Bridge files omit selected input families, including Microsoft ML Buildings, Google Open Buildings, USGS Lidar and one Zenodo buildings dataset. No matching row does **not** prove that the building is absent from Overture.
- Official [registry](https://docs.overturemaps.org/gers/registry/) is updated in place and is distinct from release-pinned bridge files. A UUID and a matching bridge row do not independently prove current registry membership or the source Parquet checksum.

`scripts/overture_osm_building_bridge_preflight_v0.py` validates a deliberately narrow read-only **normalization** of just the **three original row columns** `id,record_id,dataset`, with the three partition fields `bridge_provider`, `bridge_theme`, and `bridge_type` supplied separately in the outer envelope. It requires exact OSM IDs such as `w123@5` (never silently strips source versions), source provider `osm`, building theme/type, release `2026-10-21.0`, and explicit source dataset `OpenStreetMap`. An input can contain *at most* 100 local records and 500 bridge rows. This is not a real Parquet reader and does not initiate an external download.

Example entirely synthetic JSON input:

    {
      "schema": "opencatastrophe-overture-osm-building-bridge-v0",
      "release": "2026-10-21.0",
      "bridge_provider": "osm",
      "bridge_theme": "buildings",
      "bridge_type": "building",
      "bridge_dataset": "OpenStreetMap",
      "local_records": [{"local_id": "SYNTH-1", "record_id": "w123@5"}],
      "bridge_rows": [{
        "id": "fea28f69-7afa-460c-b270-61ef74cd340c",
        "record_id": "w123@5",
        "dataset": "OpenStreetMap"
      }]
    }

Run against the local **synthetic** JSON only:

    python -m scripts.overture_osm_building_bridge_preflight_v0 --input /private/synthetic-osm-bridge.json --expected-release 2026-10-21.0
    python -m unittest tests.test_overture_osm_building_bridge_preflight_v0 -v

The output keeps `gers_registry_membership_verified=false`, `source_file_original_bytes_verified=false`, `physical_geometry_crosschecked=false`, `independent_model_input_approved=false` and `raw_data_import_authorized=false`. Its reciprocal one-to-one records are *candidate joins only*. One-to-many and many-to-one matches are ambiguous. A missing source ID is reported as absent **from the supplied bounded slice only**.

For an actual ingestion chain, first pin and verify original Parquet byte hashes and the correct provider/dataset semantics, then validate a bounded source sample, then verify GERS registry membership and candidate geometry against the national original. Keep unrelated commercial source rights separate. Do not import any original source rows or inferred insured exposure into Neon without review.

## Original public OSM bridge Parquet access receipt (2026-11-02)

This receipt records a **live original-provider HTTP metadata and range verification**, not acquired source records. The official [2026-10-21 Overture release notes](https://docs.overturemaps.org/blog/2026/10/21/release-notes/) pin the release and AWS/Azure bridge prefixes.

On 2026-11-02, the public AWS S3 ListObjectsV2 endpoint at `https://overturemaps-us-west-2.s3.us-west-2.amazonaws.com/` was queried with `list-type=2`, the exact `prefix=bridgefiles/2026-10-21.0/provider=osm/theme=buildings/type=building/` and `max-keys=2`. Original XML confirmed **IsTruncated=true** and these first two provider keys:

| First two original objects | Size, bytes | LastModified UTC | Parquet footer metadata size |
| --- | ---: | --- | ---: |
| `part-00000-5eacc0d5-7529-4a0a-85fa-1c7fe4b343e0.c000.snappy.parquet` | 390230643 | 2026-10-21T17:36:57Z | 4281 |
| `part-00001-5eacc0d5-7529-4a0a-85fa-1c7fe4b343e0.c000.snappy.parquet` | 390145222 | 2026-10-21T17:38:14Z | 4282 |

For **each** exact key, the separate original `Range: bytes=0-3` returned the four ASCII bytes `PAR1`, and the separate `Range: bytes=-8` returned a little-endian footer-metadata length plus final `PAR1`. Thus 12 original byte-range body bytes per file (24 total) were inspected, not their contents. The listing also reported multipart ETags: these are **not** whole-file MD5/SHA256 checksums and do not establish original content identity for model admission.

Reproduce using the explicitly opt-in, hardcoded, bounded original-source script:

    python -m research_runners.overture_osm_bridge_original_probe_v0 --live
    python -m unittest tests.test_overture_osm_bridge_original_probe_v0 -v

The read-only script caps listing XML at 32768 bytes, checks exactly the first one or two partition keys, and requests exactly 4+8 bytes per listed object. It validates `Content-Range`, response status `206`, source ETag consistency, original file size, Parquet boundary magic and a bounded footer-size integer. No credentials, caller-chosen endpoint, listing pagination, full provider file or original row acquisition are used. Only explicit `--live` enables networking; the CI tests are 100% offline and mocked.

**Original footer metadata (first object only):** a bounded 4,281-byte footer read was independently decoded with Parquet Thrift CompactProtocol. It reports 7,852,618 source rows in 3 row groups, root `spark_schema` with eight fields (`id`, `dataset`, `record_id`, `update_time`, `resource`, `version`, `between`, `dataset_between`), and creator `parquet-mr version 1.13.1`. This is verifiable **original file metadata only**; source records/values, object SHA256, GERS identities, provider licence and model suitability were **not** validated. The three partition keys are source path identity, never appended as falsely claimed original columns. This corrected a preflight schema mismatch before an import could be attempted.

**Result:** public cloud object metadata and bounded Parquet-format boundaries verified, but **original GeoParquet source rows NOT inspected, SHA256 not validated, source-record rights NOT approved, GERS membership NOT verified, model input NOT admitted, and no Neon database write**. Before any rows are stored, independently verify the relevant complete source, attribution, licence and scientific bridge; this receipt is not a completed provider-data import.

## Original Overture building Parquet source metadata pilot (2026-11-02)

In addition to the OSM bridge, the actual **Buildings** dataset was inspected directly from the public original AWS S3 bucket, frozen at Overture release `2026-10-21.0` under
`release/2026-10-21.0/theme=buildings/type=building/`. A deliberately bounded S3 ListObjectsV2 response with `max-keys=2` returned `IsTruncated=true`, so this is a **two-object sample**, not a global inventory.

| Original object suffix | Original bytes (S3 listing) | Parquet footer length | FileMetaData.num_rows |
|---|---:|---:|---:|
| `part-00000-85375c54-5dfb-57c7-b21d-8b5e5245ad06-c000.zstd.parquet` | 533137080 | 668264 | 5002132 |
| `part-00001-25a868c6-9ddc-5e1c-8e0e-8286ae2005d9-c000.zstd.parquet` | 533341551 | 703774 | 5001978 |

The original first four bytes and final eight bytes were obtained by independent exact HTTP Range requests on **both** objects; all boundary checks returned `PAR1`. A further **32768-byte read at the start of each original Parquet metadata footer** allowed a bounded Thrift CompactProtocol decode of `FileMetaData.version=2`, the nested original file schema and `FileMetaData.num_rows`. Both files report the same schema structure of 63 nested schema entries with a root building schema declaring 24 children. Actual original nested schema names include `id`, `sources`, `record_id`, `geometry`, `bbox`, `height`, `num_floors`, and `xmin/ymin/xmax/ymax`.

**This is access and schema evidence only.** The 10,004,110 sum counts stored *rows in two files*, not distinct buildings, country coverage, eligible insurer addresses or actual insured exposures. No data-row pages were fetched, geometry WKB validated, feature identities proved, source/file SHA256 measured or downstream ODbL compliance signed off. The two file-specific multipart ETags are **not cryptographic whole-object SHA256**. Height and floors in the schema do **not** establish non-null values, surveyed truth or commercial insurance sums.

Reproducible bounded tool, with an opt-in network switch and no source-row ingestion:

    python -m research_runners.overture_building_original_metadata_probe_v0 --live
    python -m unittest tests.test_overture_building_original_metadata_probe_v0 -v

This original-data runner uses hardcoded provider host, release and prefix, no credentials and no redirects, with at most 2 keys and per-object only 4+8+8192 bytes. Range responses require exact HTTP 206, Content-Range, Content-Length and unchanged ETag; the schema parser is bounded and fails closed. All 19 synthetic tests are offline; no live AWS access occurs in PR CI. Before using actual building records for valuation, separately verify source rights, original whole object checksums, row-group selection/CRS, reference years, individual source lineage, GERS and loss model calibration.

## Neon isolated metadata-only pilot (2026-11-02)

On the existing CAT-only Neon project `insurance-risk-core`, a **new isolated branch** `overture-buildings-metadata-pilot-20261102` (ID `br-bold-unit-baf2smqf`) was created from insurance `main`. No production database migration or source-row import was performed.

The reviewed reproducible SQL is `research_runners/sql/overture_buildings_metadata_receipts_v0.sql`. On this **isolated branch only**, the table `research.overture_original_building_file_probe_v0` holds two rows of *metadata receipts*, including exact public source keys, immutable release, provider-reported S3 sizes, Parquet footer sizes, schema-entry counts (63), provider-reported Parquet row counts and S3 ETags. The SQL enforces `original_rows_ingested = false`, `entire_object_sha256_verified = false`, `source_rights_approved = false`, `actual_geometry_validated = false`, `insurer_exposure_admitted = false`, `cat_model_input_approved = false`.

**Actual isolated SQL readback:**
- Stored original file receipts: **2**.
- Source Parquet row-count sum in those two files: **10,004,110**.
- Reported original file-byte total: **1,066,478,631** (files themselves were **not** copied into Neon).
- Inadvertently approved input/source/import statuses: **0**.

**Production countercheck:** `insurance/main` does **not** have `research.overture_original_building_file_probe_v0`; original raw artefacts and real insured exposure units still count **0**. The other Neon project for Pokémon cards was not accessed.

This work demonstrates the first **tested database storage of original-source metadata** for the global building pilot, **not** an actual building-footprint, policy, insurer TIV, hazard or damage import. The next *causal scientific step* is an authorized, bounded original Parquet **row-group geometry** read (with correct WKB/GeoParquet CRS, source lineage and per-feature rights) followed by a strict country pilot and separate source/model admission.

## Geodesic research-only building geometry quality gate (2026-11-02)

`scripts/overture_building_geojsonseq_qc_v0.py` adds a **local-only bounded actual-geometry preflight** for a previously independently obtained `GeoJSONSeq` projection from one exact Overture Buildings release object. It never fetches original rows itself and never writes to Neon or a git-tracked provider-data file.

- Requires release `2026-10-21.0` and an *exact original S3 Parquet file key* matching `release/2026-10-21.0/theme=buildings/type=building/part-...zstd.parquet`; the supplied key is an unverified provenance claim, **not** proof of source-object checksum or authorized model use.
- Accepts at most **64** GeoJSONSeq features and **256 KiB**, including RFC-8142 record separators; rejects duplicate JSON fields, nonfinite values, invalid/oversized geometry, wrong polygon CRS coordinate ranges, conflicting/duplicated Overture feature IDs, incompatible supplied `bbox`, implausible heights/floors and insurer/customer fields.
- Calculates WGS84 **ellipsoidal geodesic footprint area in square metres** using pyproj.Geod, including oriented holes and separate MultiPolygon components; reports aggregate minimum/median/maximum area, source lineages present, height/floor field presence and exact normalized-polygon duplicate candidates.
- Does not echo source coordinates, building IDs, source records, private insurance data or raw polygons in its JSON output. Output contains only aggregate QA and a hash of the local sample. A duplicate polygon is an **adjudication candidate**, not permission to deduplicate independent buildings.
- Explicitly emits `admitted_model_input=false`, `insured_value_inferred=false`, `original_file_sha256_verified=false`, `gers_registry_identity_approved=false`, `independent_source_rights_approved=false` and `neon_written=false`.

**One possible *manual, separately reviewed* original-data sample source:** After independently confirming ODbL/attribution obligations, a pinned DuckDB/Spatial/httpfs environment can run this deliberately one-object, max-25-output-row query. It is an **example not executed in the PR**, and `LIMIT 25` does not cap Parquet network bytes. Rows sampled from the first global shard **do not** establish coverage of any particular country.

~~~sql
LOAD httpfs;
LOAD spatial;
SET s3_region = 'us-west-2';
COPY (
  SELECT id, height, num_floors, geometry
  FROM read_parquet(
    's3://overturemaps-us-west-2/release/2026-10-21.0/theme=buildings/type=building/part-00000-85375c54-5dfb-57c7-b21d-8b5e5245ad06-c000.zstd.parquet'
  )
  LIMIT 25
) TO '/tmp/overture-local-research-only.geojsonseq'
WITH (FORMAT GDAL, DRIVER 'GeoJSONSeq', SRS 'EPSG:4326');
~~~

`/tmp/overture-local-research-only.geojsonseq` stays **outside the repository**. Do not ingest raw rows into insurance Neon. A restricted and reviewed local sample can be checked as follows:

~~~sh
python -m scripts.overture_building_geojsonseq_qc_v0 \
  --input /tmp/overture-local-research-only.geojsonseq \
  --release 2026-10-21.0 \
  --source-object-key 'release/2026-10-21.0/theme=buildings/type=building/part-00000-85375c54-5dfb-57c7-b21d-8b5e5245ad06-c000.zstd.parquet'
python -m unittest tests.test_overture_building_geojsonseq_qc_v0 -v
~~~

The geodesic QC is an improvement over geographic-degree-space IoU in the *earlier* polygon candidate crosswalk; it **does not** turn that older IoU into geodesic matching. A subsequent identity harmonization phase should change the matching routine only after a reviewed, equal-area/geodesic polygon overlap contract and independent source ID evidence are established.

Review and permission to fetch exact original source rows, row-group/column bytes, attribution and a genuine geography-specific source pilot remain outstanding. **No real feature-level original geometry has yet passed this QA in Neon.** The purpose of this stage is to make any such pilot measurable, bounded and fail-closed.

## Path to real insurer CAT models

1. Freeze an original source object identity, schema version, byte hashes and attribution/rights before a bounded cloud retrieval. Document authoritative GERS ID registry/bridge checks separately.
2. Obtain original locally applicable building polygons, vintages, use, construction materials, floor/height information and replacement-value evidence. Do not count conflated sources as distinct buildings.
3. Construct peril-specific original hazard intensities and region/peril coverage for flood, wind, earthquake, hail, wildfire, etc., with calibrated vulnerability and independent damage/claim data.
4. Keep physical building-stock estimates separate from insurer-owned or ceded exposure. Only legitimately available insurer portfolios and contractual terms can establish insurer-specific TIV, coverage and retro.
5. Ingest separately approved inputs and provenance into CAT-only Neon insurance-risk-core on a reviewed branch. Never use tcgp2p-core. Full scientific admission and native model runs remain separate gates.

This contribution introduces *code and synthetic tests only*, not a real-data acquisition or an approved CAT model.
