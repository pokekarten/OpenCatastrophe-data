<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Census Grid 2021 V3: exact CSV ↔ GeoTIFF cell parity — offline gate

Date of contract review: 2026-11-13. Product is the [original Eurostat 2021 Census Grid, V3 dated 30 May 2026](https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution/population-grids), **not GEOSTAT 2006/2011/2018**. Product-specific [Eurostat 2021 Census Grid rights](https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution): EU copyright / **CC BY 4.0** with attribution. CC BY 4.0 data rights alone do not override the *separate* repository provider acquisition contract.

## The specific outstanding scientific check

The existing private `insurance-risk-core` Neon research samples already have:

- **#63:** an original positive 1-km, 14-band Census 2021 V3 GeoTIFF pixel, verified by an exact 49,152-byte original HTTP Range SHA256 `80238bea7841928b220fbf61c980bafd61290f4bf2214a997686441593c09155`; native EPSG:3035 cell (row 100, column 4118); no CAT admission.
- **#65:** original 2021 GISCO one-cell ID `NO_CRS3035RES1000mN5399000E5018000`, official country and NUTS3 metadata.
- **#66:** independent official 1-km GeoJSON source polygon that agrees geometrically with the TIFF original cell, within ~0.000145 m boundary difference. This **does not independently remeasure any population**.

The remaining numeric check is **the identical cell** in **the original same-release V3 CSV**, compared against **all 14 32-bit TIFF bands**, preserving confidentiality `-8888` and missing `-9999`. The corresponding V3 CSV source row would have `GRD_ID=CRS3035RES1000mN5399000E5018000` and `CNTR_ID=NO`. Do not infer an official source row or successful equality before actually processing it.

## Source-asset identity frozen from original provider central directory (Neon #60)

| Exact ZIP member field | Expected original source value |
| --- | --- |
| Original ZIP URL | `https://gisco-services.ec.europa.eu/census/2021/Eurostat_Census-GRID_2021_V3.zip` |
| CSV member | `Eurostat_Census-GRID_2021_V3/ESTAT_Census_2021_V3.csv` |
| Local ZIP header start | `209230036` |
| Compression | raw ZIP DEFLATE (method 8), **not gzip** |
| Compressed member bytes | **49,110,575** |
| Uncompressed member bytes | **339,625,996** |
| Original central-directory CRC32 | `54cdc404` |

The exact 14-field source fingerprint is `206185ef8953f67e5c8516a8b9d95b2e66907b28b5e5f1a4d98836e913ac7ec8`, a SHA256 of comma-joined decimal values in the fixed band order `T,M,F,Y_LT15,Y_1564,Y_GE65,EMP,NAT,EU_OTH,OTH,SAME,CHG_IN,CHG_OUT,POPULATED`, **computed from private verified raster research sample #63 in Neon**. It is a reference digest, not redistributed raw provider cell bytes. The target ID and source locale are independently supported by #65/#66.

## Why not run the live 49-MB acquisition automatically?

The canonical current [`access/eurostat.gisco.census-population-grid.2021.json`](../../access/eurostat.gisco.census-population-grid.2021.json) expressly sets:

- `status=documented_only`, `probe_contract.mode=none`, `implementation_decision=document_only`.
- `operational_constraints.max_probe_bytes=65536`, `max_sample_bytes=52428800`.
- `api_terms_status=unknown` and `commercial_automation_status=unknown` with explicit notes that **no automated HEAD/GET/Range call** was authorized by that original contract.

The 49.1-MB compressed member falls below the numeric 52.4-MB sample ceiling, **but byte-size fit alone does not grant request permission**. Existing small original research byte-range observations do not retroactively upgrade that documented-only provider acquisition contract. Therefore this contribution does **not** insert a `push`, `schedule` or `workflow_dispatch` live network action, and **does not** claim source CSV value parity or a full original ZIP SHA256.

## Implemented offline reproducible preflight

[`research_runners/eurostat_census_v3_full_csv_member_parity_v0.py`](../../research_runners/eurostat_census_v3_full_csv_member_parity_v0.py) takes only a **locally pre-acquired, externally validated raw DEFLATE byte stream of this exact single CSV ZIP member**, and uses a standard-library streaming inflater. It holds at most one compressed block, bounded inflated output and one original CSV line at a time.

It independently checks total member compressed/uncompressed size, central-directory CRC32, complete DEFLATE EOF, column order, unique target grid/country, **all 14 original V3 population bands against the privately computed TIFF fingerprint**, and calculates SHA256 for both compressed and uncompressed exact CSV member. No rows, individual values or source payloads appear in its output; its receipt has `cat_model_input_approved=false`. A mismatch is a hard failure and never a partial admission.

```bash
python -m unittest tests.test_eurostat_census_v3_full_csv_member_parity_v0 -v
# Run only after the provider's exact-member acquisition has been separately
# authorized. Two locally verified inputs: exact ZIP local header (at
# offset 209230036), plus exactly 49110575 raw DEFLATE member bytes:
python -m research_runners.eurostat_census_v3_full_csv_member_parity_v0 \
  --original-local-header /private/provider-verified/v3-csv-local-header.bin \
  --raw-deflate-member /private/provider-verified/v3-csv-member.deflate
```

Only synthetic fixtures (not source values or bytes) occur in [`tests/test_eurostat_census_v3_full_csv_member_parity_v0.py`](../../tests/test_eurostat_census_v3_full_csv_member_parity_v0.py). The tests prove good synthetic matches, preserved missingness, CRC/length/deflate corruption, fingerprint mismatch, absent/duplicate/wrong-country target and bad schema fail closed. They **do not** prove the real 396-population TIFF cell equals the original V3 CSV cell. The production test has **not been executed** on original CSV bytes in this contribution.

## Next causal gate

Obtain provider-specific review/permission for a **single authenticated-or-anonymous, fully allowlisted, no-secret, bounded acquisition** of the exact *one* original ZIP CSV member: verify the original ZIP local header, exact archive version, original `Content-Range`, expected compressed member size, original central directory identity, no arbitrary redirects, and rate-limit policy before passing raw DEFLATE to this offline validator. Record **only hashes, checksum, row-count and parity Boolean** in private Neon. Keep full source bytes and personal/policy/claims data out of public Git. A completed one-cell CSV↔TIFF parity is still not whole-EU / insurer exposure approval.

### Streaming robustness added after first passing CI (13 November)

A previously untested **false rejection** was identified for a legitimate, very compressible Census CSV DEFLATE block: one bounded 65,536-byte compressed chunk can decode to more than 2 MiB. The validator now drains `zlib.decompressobj.unconsumed_tail` through repeated **2-MiB maximum output chunks**, while enforcing exact full-source uncompressed byte count, member CRC32, EOF, single-source-row limits and no-progress detection. It does **not** lift any source acquisition permissions or sample/production admission.

A new synthetic-only test contains **35,002 complete rows**, including exactly one matching target cell. The synthetic compressed fixture is under 65,536 bytes but the uncompressed source is over 2 MiB; the test exercises this bound and still checks that only one original target-row SHA fingerprint is used. The exact member length, CRC and ZIP local offset remain verified from the original provider central-directory metadata in private Neon **sample #60**.

The streaming change passed the previous CI head; subsequent modifications (including the local-header gate) require a fresh CI run.

### Provider-specific access evidence vs generic Eurostat Data Browser API (13 November)

Current original official pages, separately reviewed:

- [GISCO original product release directory](https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution/population-grids): version 2021 dated **30 May 2026** includes the exact V3 static ZIP; this is the source-asset identity for our future CSV/TIFF comparison.
- [GISCO census population grid 2021 rights](https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution): specifically EU copyright / **CC BY 4.0**; the older GEOSTAT 2006/2011/2018 product rights and the separate generic GISCO `TOT_P_2021` grid dataset are **not interchangeable**.
- [Eurostat Statistics API introduction](https://ec.europa.eu/eurostat/en/web/user-guides/data-browser/api-data-access/api-introduction) allows programmatic queries for **Eurostat's dissemination database**, not a promise that the static `gisco-services.ec.europa.eu/census/2021/*.zip` file shares that service's quotas, version guarantees or API contracts.
- [Eurostat fair-use guidelines for asynchronous statistical API](https://ec.europa.eu/eurostat/en/web/user-guides/data-browser/api-data-access/api-detailed-guidelines/asynchronous-api) recommend **one extraction at a time** and avoiding parallel scripts. These are relevant operational principles, but **do not establish** an enforceable rate-limit budget for this separate GISCO static ZIP.
- [GISCO ID service API specification](https://gisco-services.ec.europa.eu/id/api-docs/) supports **cell geometry/ID reverse lookup**, not V3 CSV's 14 individual numerical census variables. Samples #65/#66 are independent geographic identity checks only.

**Status remains** `api_terms_status=unknown` and `commercial_automation_status=unknown` for the *exact GISCO static ZIP service* under the repository's documented-only access contract. General Eurostat public API permission must not be used to silently promote this different GISCO interface.

### Original ZIP local header verification added

The offline command now **requires two separately reviewed local inputs**, not one:

1. The exact bounded local ZIP member header from original ZIP absolute offset **209,230,036**, including its original file name and any extra fields (up to 512 B). The validator enforces ZIP signature, DEFLATE method 8, version 20, no encryption, fixed member name, central-directory compressed/uncompressed lengths and CRC32. A ZIP data-descriptor flag is permitted only with central-directory-compatible zeros or exact original sizes/checksum; unsupported flags are rejected. The validator calculates the **exact absolute start offset of raw compressed bytes** from the authenticated local header length; it does not guess a fixed 30-byte header.
2. The exact **49,110,575-byte raw compressed CSV member** beginning at that calculated offset, separately obtained after a provider-specific legal and technical access decision. The full member is never committed to Git. Its offline CRC32 and 14-field cell fingerprint must both match to pass.

Synthetic tests cover a normal local header, a valid data-descriptor layout, and deliberate violations (wrong member, encryption, wrong CRC, truncated/extra header, wrong size). These tests contain **no original Eurostat ZIP header bytes** and do not authorize a provider GET. A successful local-header check by itself cannot prove an external fetch came from the claimed original host without a separately verified source request, TLS endpoint and HTTP Content-Range receipt.

### CI evidence

The previous source-branch head `453949f74e20deb2da072e89240fdd21883c50b6` passed [GitHub CI #43459064715](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43459064715). The newly introduced ZIP-local-header gate has a **different head**, which requires its **own** passing CI run before declaring the full PR ready.

### Private Neon source-readiness projection (13 November)

Applied a read-only evidence projection in the private insurance-risk-core database and reproduced the **exact running SQL definition** in [`sql/research_eurostat_census_v3_csv_tiff_parity_readiness_v0.sql`](../../sql/research_eurostat_census_v3_csv_tiff_parity_readiness_v0.sql).

`research.eurostat_census_v3_csv_tiff_parity_readiness_v0` joins exactly verified private source-evidence records #60 (original ZIP central-directory inventory), #63 (original V3 TIFF 14-band pixel), #65 (official GISCO ID) and #66 (official GISCO polygon geometry). The view internally recomputes the **private 14-field raster fingerprint from the retained original cell JSON**, validates source sample canonical SHA-256 and checks exact CSV member compressed/uncompressed sizes, CRC32 and ZIP local-header offset against the frozen CSV contract. **No original row values, raw GISCO bytes, claims or policyholder data are added to Git.**

Read-only current database result (2026-11-13):

| Exact evidence/gate | Result |
| --- | --- |
| ZIP metadata and pixel/ID/polygon sample SHA checks | **Pass** |
| ZIP entry expected sizes, CRC32, original offset | **Pass** |
| Pinned 14-band GeoTIFF fingerprint | **Pass** |
| `offline_reference_preflight_ready` | **true** |
| `gis_static_zip_acquisition_contract_state` | **documented_only** |
| `gis_static_zip_automation_rights` | **unknown** |
| `original_full_v3_csv_observed` | **false** |
| `original_14_band_csv_tiff_parity_verified` | **false** |
| `production_cat_model_input_admitted` | **false** |

`offline_reference_preflight_ready` **does not equal** actual same-release population parity or permission to fetch the original source. It merely proves that all current *pre-existing* published metadata/byte-range evidence is internally consistent before the blocked full-member operation.

**Service-maintenance caveat:** The original Eurostat website on **13 November 2026** displays a notice that Eurostat web services/APIs, Data Browser and related services are scheduled to be unavailable **14:00–23:00** (site-local time). This is a limitation on interpreting fresh service-probe failures; it does not establish any separate downtime or service terms for the GISCO static ZIP host. The present work makes **no** new bulk/provider live requests.


### Alternative complete preapproved original ZIP — new strictly offline gate

An additional [`research_runners/eurostat_census_v3_offline_complete_zip_parity_v0.py`](../../research_runners/eurostat_census_v3_offline_complete_zip_parity_v0.py) removes the risky manual step of carving a 49.1-MB raw DEFLATE member out of a 566.1-MB ZIP. If the **separate GISCO access review later explicitly authorizes acquisition** and the original ZIP has been obtained as a private local file, use:

```bash
python -m unittest tests.test_eurostat_census_v3_offline_complete_zip_parity_v0 -v
# This command uses only an already-acquired, rights-reviewed LOCAL file:
python -m research_runners.eurostat_census_v3_offline_complete_zip_parity_v0 \
  --preapproved-v3-zip /private/reviewed-original/Eurostat_Census-GRID_2021_V3.zip
```

This new path **never opens a network connection or persists original bytes to Git/Neon**. The local original archive must be **exactly 566,125,577 bytes**, have **exactly nine frozen original ZIP central-directory filenames** (from original source evidence sample #60), no duplicate entries, no comment, no encrypted or unsafe paths, and an exact original `ESTAT_Census_2021_V3.csv` ZIP entry: **local offset 209,230,036, method 8, CRC32 `54cdc404`, compressed 49,110,575 B, uncompressed 339,625,996 B**.

The script computes the full original **local** ZIP SHA-256 by reading the file in 1-MiB chunks, independently checks the ZIP local member header and any data descriptor against the source central directory, then seeks directly into the exact compressed CSV member and runs the same streaming source CRC/SHA/14-field single-cell parity procedure. The entire ZIP/CSV never enters RAM at once. The output is just the source-integrity/parity receipt and hashes, with **`provider_origin_independently_authenticated=false` and `provider_acquisition_rights_verified=false`**, since computing a digest of a local file does not prove a provider-signed official archive or clear service terms.

[Synthetic, entirely offline ZIP tests](../../tests/test_eurostat_census_v3_offline_complete_zip_parity_v0.py) exercise a tiny newly constructed ZIP with correct same-release-like **synthetic values**; wrong central-directory file name, duplicate member, incorrect local-header magic/CRC/offset, absent target cell, reporting-country mismatch, ZIP comment and symlink input all fail closed. Test-only size and CRC overrides do not exist in the production command; the original V3 constants are fixed by default.

**Important distinction:** a complete local ZIP SHA is not a previously published provider SHA unless it is independently attested with fixed original provider URL/HTTPS, content length, final redirects, HTTP identity and access timestamp. A source archive digest, a verified single-cell CSV/TIFF numerical match and legally approved NextGen/CAT model use are **three distinct gates**. None has been promoted by these synthetic tests.

### All nine original ZIP central-directory entries frozen (13 November, further integrity hardening)

The original bounded ZIP central-directory receipt in **private Neon #60** records not only the CSV member but the exact **compressed bytes, uncompressed bytes, CRC32, compression method and local-header offset for all nine V3 members**. The complete-local-ZIP validator now includes these **original source metadata-only invariants**, so a substituted V3 GeoPackage, Parquet, TIFF, README, national-country CSV ZIP or SDMX metadata ZIP cannot pass source ZIP identity merely because it retains the right filename.

| Original ZIP member | Local header offset | Compressed bytes | Uncompressed bytes | Original CRC32 |
| --- | ---: | ---: | ---: | --- |
| V3/ directory | 0 | 0 | 0 | `00000000` |
| Country CSV nested ZIP | 91 | 203,478,177 | 257,389,035 | `84ee38b8` |
| LAND_SURFACE TIFF | 203,478,408 | 5,751,483 | 5,977,689 | `b8d826f9` |
| Census V3 CSV | 209,230,036 | 49,110,575 | 339,625,996 | `54cdc404` |
| Census V3 GeoPackage | 258,340,742 | 221,469,461 | 1,302,953,984 | `fe282818` |
| Census V3 Parquet | 479,810,335 | 55,211,012 | 76,307,745 | `205a238f` |
| Census V3 TIFF | 535,021,482 | 30,762,675 | 32,327,795 | `1f5a582f` |
| Census SDMX metadata nested ZIP | 565,784,289 | 337,508 | 343,891 | `682bc27f` |
| read.me | 566,121,942 | 2,390 | 5,428 | `8653c53b` |

This **directory-only** integrity check is O(nine entries) and does **not** inflate or independently recheck all non-CSV members. Those CRCs are frozen expected metadata, not proofs of those members' complete compressed data integrity. The full-archive SHA is still computed from a separately acquired local source ZIP, not independently supplied/signed by Eurostat. A new synthetic regression deliberately modifies an auxiliary README while preserving the original synthetic CSV bytes; **directory identity must fail**. The original source remains `documented_only` for automated acquisition, and the actual V3 numeric CSV ↔ TIFF match has **not** been performed.


### Original ZIP End Of Central Directory (EOCD) pinned, no hidden trailer

Independent primary original-source **Neon sample #60**, a hashed 32,768-byte tail of the original Eurostat V3 566,125,577-byte ZIP, recorded its real ZIP End Of Central Directory:

| Source property | Frozen original value |
| --- | ---: |
| Original ZIP total length | **566,125,577 bytes** |
| Original central directory offset | **566,124,446** |
| Central directory byte length | **1,109** |
| ZIP end-of-central-directory record | **22 bytes** |
| Number of ZIP members | **9** |
| Disk count and ZIP comment | Single disk, zero comment bytes |
| EOCD accounting | `566124446 + 1109 + 22 == 566125577` |

The offline complete ZIP validator now independently reads the **last 22 bytes** of any separately reviewed local V3 archive and checks classic EOCD signature, no ZIP64/segmented-volumes, zero comment, exactly nine entries, and **the exact original central-directory offset and length**, then cross-checks against the entire original nine-member CRC/offset/size identity table. This prevents a nominally 566 MB local archive with an arbitrary trailing comment, hidden appended payload, moved directory or changed total entry count from passing simply because Python `zipfile` can read it.

All these values were already independently observed in original provider byte-range sample #60. No new original provider request or archive download was performed to obtain them. New **synthetic-only** tests exercise successful exact EOCD, altered declared central directory offset, ZIP comment and hidden trailer with the CSV unchanged. A matching EOCD is **not** an independently signed checksum of source data and cannot establish V3 CSV-to-TIFF population parity.

CI evidence for the new EOCD commits must be checked separately; previously passing CI predates this added gate.


### Offline HTTP acquisition-receipt consistency (not provider-authentication or rights clearance)

Before processing a separately approved **complete** V3 archive, require a fixed schema receipt from the **actual authorized downloader** and verify its consistency against the ZIP already saved privately. New fully offline script [`research_runners/eurostat_census_v3_offline_http_receipt_v0.py`](../../research_runners/eurostat_census_v3_offline_http_receipt_v0.py) requires two **local** inputs and has **no network access**:

```bash
python -m unittest tests.test_eurostat_census_v3_offline_http_receipt_v0 -v
python -m research_runners.eurostat_census_v3_offline_http_receipt_v0 \
  --receipt-json /private/audit/reviewed-provider-full-get.json \
  --preapproved-v3-zip /private/reviewed-original/Eurostat_Census-GRID_2021_V3.zip
```

The receipt must be **one small (2–4096 B) UTF-8 JSON object**, with the exact keys below and strict JSON duplicate-key rejection:

| Exact key | Expected provenance rule |
| --- | --- |
| `schema` | `eurostat-gisco-census-2021-v3-offline-http-receipt-v0` |
| `source_url`, `requested_url`, `final_url` | All equal the exact official [2021 V3 archive URL](https://gisco-services.ec.europa.eu/census/2021/Eurostat_Census-GRID_2021_V3.zip); no other domain, older release, mirror, query string or redirect |
| `http_method`, `http_status`, `redirect_count` | `GET`, integer `200`, integer `0` |
| `content_encoding`, `content_type` | `identity`, `application/zip` / `application/octet-stream` / `application/x-zip-compressed` |
| `content_length_bytes`, `saved_bytes` | Both exact **566,125,577** integer bytes, matching the actual local file |
| `local_file_sha256` | SHA-256 of locally saved **whole ZIP**, independently recomputed in 1-MiB bounded I/O chunks |
| `retrieved_at_utc` | RFC3339 canonical UTC seconds `YYYY-MM-DDTHH:MM:SSZ`, not in the future and not before V3 publication on **30 May 2026** |
| `source_access_review_reference` | Non-empty stable manual, source-specific legal and operational review reference; the string itself is **not proof** that such approval is valid |

The script outputs only receipt/digest integrity flags, no original provider body, download credential or insured source data. A syntactically consistent receipt, even with a matching complete ZIP SHA, is **not a digitally signed provider attestation** and **does not itself validate the stated source legal permission**. An authorized downloader, separate approval record, original response headers, HTTPS/final-URL evidence and preferably an independently published original-provider checksum must be reviewed **outside** this script before labeling the file original/legally automatable. The transport consistency gate, original ZIP nine-member/EOCD structural gate, original V3 14-band CSV↔TIFF numeric gate, and commercial CAT-model admission remain independent.

[Synthetic-only tests](../../tests/test_eurostat_census_v3_offline_http_receipt_v0.py) reject wrong exact source URL or release, redirects, HTTP 206/HEAD, gzip transformation, altered saved/expected byte count or SHA, non-ZIP content types, extra/missing/duplicate JSON keys, invalid/future/pre-release dates, and missing approval references. No real original ZIP or provider receipt was obtained by adding these tests.

**Provider-service distinction, official evidence:** The [GISCO distribution v2 interface](https://gisco-services.ec.europa.eu/distribution/v2/) does expressly document scripted HTTP GETs, but it explicitly lists geographic **reference data themes** (coastlines, communes, countries, LAU, NUTS, postal codes, urban audit), **not** this separate [Census Grid V3 original static ZIP](https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution/population-grids). That generic distribution statement must **not** silently change the source-specific `access/eurostat.gisco.census-population-grid.2021.json` from `documented_only` to `allowed`. The dataset's distinct [CC BY 4.0 data licence](https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution) remains verified; the exact static ZIP service's commercial automation/rate/request approval remains **unknown**.


### Optional full-byte-content validation of all nine ZIP members

The previous offline ZIP verifier compared **all nine original central-directory CRC/size/offset records** but only **decompressed the original CSV member itself**. A corrupt non-CSV payload can retain identical metadata. The complete-local-ZIP runner now offers an explicit *opt-in* content-level pass:

```bash
# Both commands are wholly OFFLINE. The source ZIP must already have been
# separately approved and acquired; this is not an authorization or downloader.
python -m research_runners.eurostat_census_v3_offline_complete_zip_parity_v0 \
  --preapproved-v3-zip /private/reviewed-original/Eurostat_Census-GRID_2021_V3.zip \
  --verify-all-members
```

The new `--verify-all-members` flag streams and independently rehashes **every ZIP entry's *uncompressed contents*** in 1-MiB chunks, checks full decompression EOF (via `zipfile.ZipExtFile`'s CRC verification), frozen per-member uncompressed length and separately computed CRC32. It returns a **per-member SHA-256 / CRC32 / byte-count receipt** for each of the nine entries, with no original bytes or original numeric population cells in the output. The default, faster check still runs only the CSV contents and explicitly returns `all_original_zip_member_contents_verified=false` and `verified_member_count=0`, rather than falsely claiming every payload passed. A full check on the original source reads/decompresses roughly 2 GB of source-member content and is computationally expensive, but holds only bounded streaming buffers.

This **fully checks bytes of non-CSV TIFF/GeoPackage/Parquet/readme/nested ZIP members**, not their semantic correctness, CRS or privacy model. Nested ZIP payloads are checked as *opaque bytes* and are not recursively parsed. External provider authenticity, legal acquisition authorization, scientific CAT input approval and full-data modeling remain **separate and false** even when every member's CRC and SHA is verified. The source ZIP archive's full SHA is still locally computed, never purported to be a signed Eurostat checksum.

New pure synthetic tests prove (a) the optional pass emits a source-limited full-member receipt only after actually reading a complete member and (b) an **altered non-CSV ZIP payload with *unchanged original central-directory metadata*** passes the old metadata inspection but **fails** the new optional complete-content CRC test. No original Eurostat ZIP/data was downloaded or saved in Git to test this.
