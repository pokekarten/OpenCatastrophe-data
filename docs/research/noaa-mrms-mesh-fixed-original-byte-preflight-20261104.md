<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NOAA MRMS/MESH two historical original-byte preflight candidates (2026-11-04)

**Evidence class: research-only, not admission.** This extends [original-source research](exa-source-preflight-groundsource-landslide-mrms-20261104.md) and [issue #1242](https://github.com/pokekarten/OpenCatastrophe-data/issues/1242). A read-only web-content intermediary returned binary gzip bodies addressed at two exact public NOAA S3 object URLs. Separate **direct first-party acquisition** is not yet established by the repository's trusted provenance/byte-receipt runner; no GRIB raster pixel values were decoded; no third-party data bytes, insurer records or derived external bytes were committed to Git.

## Bounded observed evidence

The official public [NOAA MRMS AWS data listing](https://registry.opendata.aws/noaa-mrms-pds/) gives an anonymously readable public S3 bucket. Bounded ListObjectsV2 originally listed the following two fixed historical objects under `CONUS/`. Subsequent **binary original-object URL retrieval by an external web-content intermediary** returned bytes matching those listed compressed lengths. A self-tested SHA-256 implementation computed the following digests on the full delivered compressed bodies. The calculation function was checked against SHA-256 `abc` = `ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad`. These are **research-observed digests**, not publisher-posted SHA-256 or independent provider authentication.

| Source product | Exact 2020-10-14 UTC source basename | Delivered/published gzip size | Computed compressed SHA-256 | GZIP header and embedded name |
| --- | --- | ---: | --- | --- |
| 2-min **MESH** | `MRMS_MESH_00.50_20201014-000025.grib2.gz` | **40,186** bytes | `792b2b7961248f416b593c1fc1d8139f6709829472c1354c80d853417035f5e3` | Valid gzip magic/deflate, embedded name `MRMS_MESH_00.50_20201014-000025.grib2` |
| 30-min-window **MESHMax30min** | `MRMS_MESH_Max_30min_00.50_20201014-000025.grib2.gz` | **44,683** bytes | `5f139328e25c9b87b8c120a7b67dfb9128717e526c301a0f1b55046d11ca1337` | Valid gzip magic/deflate, embedded name `MRMS_MESH_Max_30min_00.50_20201014-000025.grib2` |

- Fixed source URLs: [MESH](https://noaa-mrms-pds.s3.amazonaws.com/CONUS/MESH_00.50/20201014/MRMS_MESH_00.50_20201014-000025.grib2.gz), [MESHMax30min](https://noaa-mrms-pds.s3.amazonaws.com/CONUS/MESH_Max_30min_00.50/20201014/MRMS_MESH_Max_30min_00.50_20201014-000025.grib2.gz).
- GZIP trailer **declares** CRC32 `71c4c524` and uncompressed length modulo 2^32 **56,052** for MESH; and CRC32 `dded88b3` and uncompressed length **60,078** for MESHMax30min. The source binary retrieval did **not independently verify** those CRCs or decode the GRIB2 envelope. Do not describe these values as validated until executing the new offline runner against a separately acquired, hash-matched source file.
- The original object listing and intermediary byte retrieval are not evidence that every two-minute time step from 2020 onward is available. The S3 prefix is **`CONUS/MESH_00.50/`**, not `CONUS/MESH/`.

## Provider interpretation, not observed loss

The [NOAA/NSSL operational GRIB2 table](https://www.nssl.noaa.gov/projects/mrms/operational/tables.php) identifies discipline **209**, category **3**, parameter **28** for `MESH` and **29** for `MESHMax30min`. Both report **millimetres** (not inch or count). That published operational table says it is current for **MRMS v12.2**, but the selected artifacts date to **2020** and therefore their algorithm/calibration/vintage must be treated separately. NOAA's [MESH guide](https://vlab.noaa.gov/web/wdtd/-/maximum-estimated-size-of-hail-mes-2) says MESH is a radar-derived maximum expected hail size, not a hailstone ground measurement. Beam/vertical-temperature and storm structure may bias its estimate. MESH swath maxima are not statistically independent extra events.

The existing discovery identity remains **`noaa.mrms.mesh`** in `landscape/sources-severe-convective-weather.json`. This is a **new exact access/byte research receipt for that identity**, not another independent source nor a new admitted hazard input. This does not measure building TIV, vulnerability or physical/insured damage.

## Executable fail-closed check

The [offline runner](../../research_runners/noaa_mrms_mesh_original_preflight_v0.py) accepts **only one of the two exact basename/versioned source objects** as a local `.grib2.gz` file and refuses drift in compressed length or SHA-256. It caps decoded size, uses zlib gzip CRC checks, and parses a single GRIB2 envelope for metadata including center/subcenter, reference date, section structure, grid count and discipline/category/parameter. It never calls the network and **never decodes field values** or infers a raster hazard footprint.

Example on an independently authorized local copy:

~~~sh
python research_runners/noaa_mrms_mesh_original_preflight_v0.py \
  --product mesh \
  --gzip /external-source-files/MRMS_MESH_00.50_20201014-000025.grib2.gz
~~~

Expected success exit `0` is strictly limited to the stated **byte and structural checks** and carries `direct_first_party_acquisition_authenticated=false`, `source_admission_granted=false`, `scientific_fitness_established=false`, `model_input_approved=false`. Rejection exit `2` means any expected identity/hash, gzip or selected metadata gate failed. The [synthetic tests](../../tests/test_noaa_mrms_mesh_original_preflight_v0.py) exercise malformed inputs, CRC, section-order, source identity, local SHA and non-admission flags. Full `python scripts/check_all.py` at exact PR head is mandatory before merge.

## Next causal science step

1. Acquire the **exact** fixed compressed originals via an authorized trusted direct HTTPS/S3 source runner, verify independent SHA-256 equality with the two research-observed digests; if mismatch, quarantine and investigate source-object drift rather than changing expected hashes silently.
2. Use NOAA-supported ecCodes or wgrib2 on these exact blobs, check the actual Section 3 grid origin/increments, Section 4 parameter semantics, missing/no-coverage codes, and decoded min/max/positive-cell counts; record command, version and provenance without publishing raw pixels.
3. Select a real historical **hail episode with positive independent ground reports** rather than assuming the first archival timestamp represents a severe hail event. Compare observed time/coordinates, MESH bias and overlapping 30-min swaths; use episode-disjoint evaluation before any hail frequency or vulnerability model.

No actual CAT loss, ELT/YLT or insurance portfolio has been generated by this evidence.
