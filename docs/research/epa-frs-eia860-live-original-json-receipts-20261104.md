<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Live US EPA FRS → EIA-860 original HTTP-body receipt — Delaware pilot (2026-11-04)

**Research evidence only; no original third-party payload stored in Git, no insured risk, no source admission, no EIA-2025 or GEM cross-link.** This is an incremental original-source experiment for [issue #1251](https://github.com/pokekarten/OpenCatastrophe-data/issues/1251) on top of merged [PR #1236](https://github.com/pokekarten/OpenCatastrophe-data/pull/1236).

## Primary source and exact observed original response body

On 2026-11-04, three **bounded, read-only** city queries to the live official [EPA FRS GetFacilities API](https://www.epa.gov/frs/frs-api) succeeded. A connected browser/fetch service performed fresh requests (`maxAgeMs=0`); the returned `application/json` original HTTP response bodies were supplied as base64 bytes and independently decoded before a SHA-256 digest was calculated. The SHA-256 implementation was cross-checked against the known `abc` vector. These hashes identify **the response bodies observed in this run**, not EPA-signed archives. The intermediary did not supply a separately authenticated HTTP status/ETag/Last-Modified or original EPA bulk-file identity.

| Fixed query | Response bytes | Original-response SHA-256 | FRS rows | EIA-860 programme links | FRS rows with >1 EIA plant ID |
| --- | ---: | --- | ---: | ---: | ---: |
| [Delaware / Dover](https://frs-public.epa.gov/ords/frs_public2/frs_rest_services.get_facilities?pgm_sys_acrnm=EIA-860&state_abbr=DE&city_name=DOVER&output=JSON&program_output=yes) | 7,620 | `e7ea81955158a1eea1b030b42e32c28a363838b5761a3d4c2d2d8c62a3bc8df6` | 6 | 6 | 0 |
| [Delaware / Wilmington](https://frs-public.epa.gov/ords/frs_public2/frs_rest_services.get_facilities?pgm_sys_acrnm=EIA-860&state_abbr=DE&city_name=WILMINGTON&output=JSON&program_output=yes) | 8,240 | `a0604befeb35eeadec1f2bafc7a8947aab4aff97ca8f6f54f8a8f224e551d00e` | 6 | 7 | 1 |
| [Delaware / Newark](https://frs-public.epa.gov/ords/frs_public2/frs_rest_services.get_facilities?pgm_sys_acrnm=EIA-860&state_abbr=DE&city_name=NEWARK&output=JSON&program_output=yes) | 2,279 | `21d2c3dfcdbe481abd28a346312899882ef9c2e9d0e1b5dd3a67ee6a4149ded6` | 2 | 2 | 0 |
| **Total, three nonoverlapping city-query cohorts** | **18,139** | **Three separately pinned responses** | **14** | **15** | **1** |

The counts refer to the original **FRS HTTP service claims**, *not* a verified 2025 EIA annual plant inventory. The Wilmington observation is a genuine **one FRS registry record ↔ two EIA-860 programme plant IDs** case. The crosswalk must preserve both associations and not silently duplicate one insured asset. None of these results identify a building, generator, owner, policyholder, insurer or replacement cost.

### Two independent single-plant probes

The following original provider response bodies were fetched separately, not added to the Delaware cohort totals:

| Fixed source query | Returned FRS records | SHA-256 of observed provider JSON body | Bytes | What can be concluded |
| --- | ---: | --- | ---: | --- |
| [EIA-860 ORIS 3136](https://frs-public.epa.gov/ords/frs_public2/frs_rest_services.get_facilities?pgm_sys_acrnm=EIA-860&pgm_sys_id=3136&program_output=yes&output=JSON) | 1 | `95d04a367074548af9218c8ada0c09b33753988633f49db9cdf72b4044a20dab` | 3,349 | EPA's EIA-860 programme row in this response refers to ORIS 3136 and FRS Registry ID `110000538525`; the historical [official EPA mashup example](https://github.com/USEPA/FRS-getfacilities-samples/blob/master/EIA-EPA_Mashup.md) gives the same pair |
| [EIA-860 ORIS 599](https://frs-public.epa.gov/ords/frs_public2/frs_rest_services.get_facilities?pgm_sys_acrnm=EIA-860&pgm_sys_id=599&program_output=yes&output=JSON) | 1 | `758b6513ad261d52bcf6e97f39ca2f74e334a7820eedee5bd1ab278b3e0e9dbd` | 2,393 | EIA-860 programme ID 599 appears in the response; **also included in Dover city cohort**, so never count it again as an extra plant |

**A significant contradictory-attribute challenge:** In the fresh ORIS 3136 response, the FRS top-level `FacilityName` is **“VS RUBBER”** and `CityName` is **“LEBANON”**, while the EIA-860 programme object is **“KEYSTONE”**. The reported latitude/longitude also must not be reconciled by assumption. The original 2014 EPA example describes **Keystone Power Plant near Shelocta**. The FRS **source-reported identifier link** is evidenced; the *top-level facility label/address/geocoding coherence* is not. A NextGen/physical-asset join must **fail closed** on such conflicts until original current source records and coordinate-quality metadata are independently resolved.

## Why previous research interfaces were not enough

1. [EPA ECHO FRS download dictionary](https://echo.epa.gov/tools/data-downloads/frs-download-summary) explicitly states that the weekly ECHO extract is **not the complete FRS** and selects from a limited list of environmental programme systems. The public [full FRS combined state/national CSV](https://www.epa.gov/frs/epa-state-combined-csv-download-files) has a different observation perimeter and is updated monthly. It is false to interpret an absent EIA-860 programme row in ECHO as proof of absence in full FRS.
2. The live [EPA API specification](https://www.epa.gov/frs/frs-api) explicitly documents `pgm_sys_acrnm` / `pgm_sys_id` identifiers and `Latitude83` / `Longitude83` in **NAD83**. The native ECHO `FRS_FACILITIES.csv` coordinates must still be independently characterized before applying that API datum claim to an unrelated file/product.
3. [EIA Form 860 annual 2025](https://www.eia.gov/electricity/data/eia860/) publishes a ZIP containing plant and generator workbooks. **No original 2025 ZIP bytes have been fetched or hashed in this pilot**; the 15 EPA programme links must not be passed off as 15 EIA-2025-confirmed plants. An independently versioned `2___PlantY2025` workbook and exact own source SHA and extraction receipt are required.
4. [GEM Global Integrated Power Tracker](https://globalenergymonitor.org/projects/global-integrated-power-tracker) is a separate product; neither a FRS/EIA record nor geospatial proximity proves a particular GEM unit/phase ID or an ultimate shareholder. Insurer and treaty/peril attribution are wholly out of scope.

## Reproducible checker and next gates

- Implemented [offline original-body parser and aggregate receipt](../../research_runners/epa_frs_eia860_original_json_city_v0.py), with [synthetic failure-mode tests](../../tests/test_epa_frs_eia860_original_json_city_v0.py).
- The checker takes only a previously acquired, original live-response JSON file and its **expected body SHA-256**, plus one of exactly three predeclared city queries. It rejects wrong state/city, duplicate site/program keys, malformed IDs, duplicate JSON keys, empty/oversized responses and unknown cohorts. It **never** downloads data, prints addresses/identifiers/coordinates, accepts arbitrary external domains or writes source bytes.
- Reproducing a live query requires independent source access/rights review, capturing the exact returned original bytes **outside Git**, and then running:
  
```bash
python -m unittest discover -s tests -p 'test_epa_frs_eia860_original_json_city_v0.py' -v
python research_runners/epa_frs_eia860_original_json_city_v0.py \
  --original-response /approved/local/dover-original-body.json \
  --response-sha256 e7ea81955158a1eea1b030b42e32c28a363838b5761a3d4c2d2d8c62a3bc8df6 \
  --cohort DOVER --observed-date 2026-11-04
```

This command only matches the recorded digest when the identical EPA response bytes are available; the live EPA service can change later, and a mismatch is a **source version change to investigate**, never a reason to disable the integrity gate.

**Next missing proof:** Read and independently hash the official 2025 EIA ZIP and plant worksheet for a bounded list, audit whether EPA EIA-860 plant IDs are in that annual vintage, review exact source terms, and then separately resolve GEM project identity. The existing issue remains open. No source-admission gate, CAT model or insurance database state was changed.
