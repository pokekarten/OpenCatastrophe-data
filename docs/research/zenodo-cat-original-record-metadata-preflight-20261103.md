<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Zenodo CAT original-record metadata preflight (2026-11-03)

**State:** fixed-source metadata validator plus original-public-API research and three bounded verified source-file probes. Three small original files were read *transiently*, not committed or ingested. No model/rights admission and no Neon or customer data writes.

## Provider record identity and scope

The offline runner at scripts/zenodo_cat_metadata_preflight_v0.py supports **five verified-open record identities**. The sixth, TRANSCLIMA catalogue concept DOI, now points to a restricted latest record and is explicitly blocked in the validator:

| Candidate | Original published record |
| --- | --- |
| European sparse multi-hazard event arrays | https://zenodo.org/records/22080546 |
| IH-STORM 12,000-year ENSO-conditioned tracks | https://zenodo.org/records/15097665 |
| TRANSCLIMA GTSMv3/GESLAv3 cyclone surge hydrographs | https://zenodo.org/records/18170693 |
| TRANSCLIMA catalogue concept (currently restricted latest 23736380) | https://zenodo.org/records/23736379 |
| GTSM-ERA5-E extreme coastal levels/statistics | https://zenodo.org/records/14671593 |
| GFSM 30 m derived global flood susceptibility | https://zenodo.org/records/20568218 |

The sixth candidate, Eurac EO4MULTIHAZARDS, is a separate PostgREST service and is intentionally outside this Zenodo preflight.

The [official Zenodo records API](https://developers.zenodo.org/) documents anonymous GET /api/records/:id metadata access. Zenodo [explains](https://support.zenodo.org/help/en-gb/2-content/21-can-i-get-permission-to-use-a-specific-record) that record metadata is CC0, while source files retain their declared license. Individual upstream data rights must be checked separately.

## Operator command with permitted public record metadata

This command is an example for an operator with normal HTTPS/DNS access. It could **not** run in the Linux sandbox because of DNS resolution failure; the official API was separately read by a connected read-only web source in this investigation:

~~~sh
curl --fail --silent --show-error --location --max-time 20 --max-filesize 5242880 \
  -H "Accept: application/json" \
  "https://zenodo.org/api/records/22080546" -o /tmp/zenodo-22080546.json
python scripts/zenodo_cat_metadata_preflight_v0.py \
  --source-id nl.vu.european-multihazard-sparse-events.v1 \
  --metadata /tmp/zenodo-22080546.json
~~~

All CLI work is local and offline: the input is a JSON file, not a URL; the runner performs no network access. It rejects unknown or mismatched record IDs/DOIs, inaccessible record metadata, missing declared license, paths with traversal, duplicate file keys, missing or malformed original publisher checksums, non-Zenodo or cross-record download links, suspicious URL parameters, or an input exceeding 5 MiB. The receipt includes a SHA-256 of **the metadata response bytes**, not the original asset files; any MD5/SHA256 reported for source files is merely the publisher-listed digest, not an independently computed digest. It cannot prove downloadable source bytes, scientific adequacy, insurer commercial reuse permission, or admission.

## Scientific boundaries and next executable evidence

1. Sparse European compound events: four input source families (C3S/ERA5-Land wind/heat, EFFIS wildfire, JRC satellite-derived flood depths) are previously known. The original wind event-summary CSV explicitly calls intensity **Mean wind speed (m/s)**, not maximum gust. Track exact version, original event ID, spatial-grid/sparse index, hazard-specific unit, start/end, affected-cell overlap and all upstream lineage. Pair overlaps are *not* independent observed claims or a loss correlation parameter.
2. IH-STORM: retain stochastic basin, climate regime (historic/neutral/El Niño/La Niña), simulated year and storm ID. These tracks do not supply wind-field intensities at property coordinates, frequency calibration independent from IBTrACS, vulnerability, or insured loss.
3. TRANSCLIMA surge: distinguish modelled GTSMv3 from gauge-derived GESLAv3 stations, source SID, UTC times, storm/tide/water-level reference and vertical datum. A hydrograph is not a 2D inundation map.
4. GTSM-ERA5-E return levels and GFSM susceptibility are screening/model challenge surfaces; neither is a true simultaneous historical damage event or CAT payout.

**Original provider evidence:** In the Linux sandbox, a bounded GET was blocked by DNS resolution. A separate read-only web source successfully fetched official Zenodo API responses and three public small original files on 2026-11-03. Exact file receipts below. No NetCDF/large ZIP bytes, model inputs or Neon rows were acquired.

**Validation:** python -m unittest discover -s tests -p 'test_zenodo*preflight_v0.py' -v (synthetic negative tests). The repository CI runs all test*.py and must pass at the new head SHA; do not merge before full check, scoped rights review, and scientific quality review.

## Live official Zenodo metadata and original byte receipts (2026-11-03)

Read-only official Zenodo JSON metadata (not full data archives) confirmed these exact record identities and access states:

| Original record | File count | Dataset access field | Record license field | Selected file size or access note |
| --- | ---: | --- | --- | --- |
| 22080546 European compound events | 7 | open | cc-by-4.0 | sparse_hazard_data.zip 6,047,379,085 bytes; hazardinfows.csv 32,210 bytes |
| 15097665 IH-STORM ENSO | 6 | open | cc-by-4.0 | four climate-regime ZIPs plus README and city return-period workbook |
| 18170693 TRANSCLIMA surge hydrographs | 13 | open | cc-by-4.0 | 12 basin/GTSM-GESLA ZIPs and README.txt |
| 14671593 GTSM-ERA5-E statistics | 1 | open | cc-by-4.0 | ds_GTSM-ERA5-E_1950-2024_stats.nc, 9,652,424 bytes |
| 20568218 GFSM | many regional ZIPs | open | cc-by-4.0 | large tiled product, no complete archive acquired |
| 23736379 TRANSCLIMA catalogue concept | 0 in latest version | **restricted** | cc-by-4.0 metadata label | concept resolved to actual version record 23736380, DOI 10.5281/zenodo.23736380; no public file entries |

The restricted catalogue is not a source-data download despite its public metadata and CC BY label. Do not circumvent the restricted file access or treat its discovery list as 262 admitted data sets.

Three fully delivered, bounded original files were independently hashed from their actual fetched bytes in the read-only connector. Each recomputed MD5 matched the publisher's official record checksum, and SHA-256 was computed separately:

| Original source file | Size (bytes) | Independently computed SHA-256 | Evidence |
| --- | ---: | --- | --- |
| 22080546/hazardinfows.csv | 32,210 | 35f10da966ad8b6f0bc5fd9dba904bb8251ae11a9f52fe7e10f4f6ff9e2bf787 | 234 distinct ws event IDs, first start 2015-01-08, last end 2025-01-01, intensity unit Mean wind speed (m/s) |
| 15097665/README.txt | 3,800 | 80c913ae6d46f58a8ab9c6dc435e552e5743f3a3edca618c59841acaea00280e | Original track columns: year, month, storm ID, 3-hour time step, basin ID, latitude/longitude (0-360), pressure, 10-min sustained wind (m/s), RMW |
| 18170693/README.txt | 7,005 | c06107caa6aea8de4116b8fbc264547dd2b6696ac1030ae75b4de0d78d867abd | Original IBTrACS SID and basin-partitioned gauge/model hydrograph variables, storm surge expressed in metres |

A separate attempt to inspect fl_ws.csv returned an incomplete response of 59,465 bytes, versus the publisher's listed 801,138 bytes. **Reject this result as truncated**: no validation, no checksum match, no observed pair-event count, and no eligible model consumer may use it. This can be a reader-size cap rather than a Zenodo defect.

### Exact original wind-event CSV gate

After a separately authorized, controlled download of the **one** 32,210-byte file, the new scripts/zenodo_eu_wind_events_csv_preflight_v0.py accepts the local file only if its 32,210-byte size, independently verified SHA-256, publisher MD5, exact CSV header, 234 unique ws event IDs, date range, bounding boxes, intensity unit and positive finite speeds agree. It emits aggregate QC only, not event rows or new rights claims. This is intentionally narrower than access to the 6 GB sparse NetCDF ZIP.

Run with an already acquired authorized original file:

~~~sh
python scripts/zenodo_eu_wind_events_csv_preflight_v0.py --csv /tmp/hazardinfows.csv
~~~

All other files remain source candidates. No source bytes are committed in this PR, no direct insurer TIV is inferred, no original ZIP/NetCDF has been validated, and no source becomes a model-ready exposure or historical loss solely from an available API, CC BY label, or passing receipt.

