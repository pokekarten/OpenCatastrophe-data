<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NYC 2024 building inventory: verified local archive-byte/header preflight

**Work date:** 2026-11-05. **Decision:** Research-only fail-closed intake contract. There is **no verified original complete 2024 BUILDING snapshot acquired** and no source data admitted to CAT modelling.

## What changed after the historical archive canary

The earlier [PR #1367](https://github.com/pokekarten/OpenCatastrophe-data/pull/1367) verified that NYC's current `BUILDING_HISTORIC` archives changed/demolished building features, **not** the stock of buildings existing on 2024-12-31. A zero match against a historic-change archive is not proof of survival. The 30-row research pilots #1354, #1357 and #1365 remain current-geometry convenience-cohort identity checks, not 2024 insurer exposures.

New original-provider checks have now separated the **archive retrieval workflow** from the **archive acceptance workflow**:

- The current [NYC BUILDING source 5zhs-2jue](https://data.cityofnewyork.us/d/5zhs-2jue) exposes a Dataset Changelog with `Export Archive` actions and weekly changes. The source page's 2024 creation date **does not prove** that a complete 2024 release, let alone the 31 December stock, is available to the public.
- The [official NYC Open Data 101 documentation](https://www.nyc.gov/opendata/get-started/user-guides/open-data-101) says enrolled datasets can expose prior archive versions, and **archives are exported as complete files, not partial record extracts**.
- The [Socrata / Data & Insights original archiving documentation](https://support.socrata.com/hc/en-us/articles/9486838238743-Introducing-Dataset-Archiving) explains that `Export Archive` generates a prior full **CSV** from accumulated changes; it may require a generation step. A version shown on a page is therefore distinct from a downloaded file whose actual bytes are hashable.
- The older official [NYC Building Footprints map 3g6p-4u5s](https://data.cityofnewyork.us/d/3g6p-4u5s) states that previous versions are retained under Local Law 106 of 2015 and can be requested from Open Data. It is a map backed by the current source, **not itself a date-pinned 2024 inventory**. The [NYC Open Data contact page](https://www.nyc.gov/opendata/contact-us) is the official route if the exact date is not accessible in Changelog.

No purported 2024 source archive export was downloaded, requested from the provider, or incorporated into the project during this research. The date nearest 2024-12-31 available for export must be read from the actual platform history or confirmed by NYC Open Data; do not invent it.

## Implemented offline source-byte integrity gate

`research_runners/nyc_building_archive_receipt_v0.py` accepts a local **CSV** or **ZIP containing one CSV**. It requires a *separately recorded* whole-container SHA-256 and an explicit claimed provider-version date in the year 2024. It hashes the full local file in 1-MiB chunks and compares its bytes with the expected fingerprint. It reads **only the CSV header** (no original source data rows) and requires the reviewed fields `the_geom`, `bin`, `doitt_id`, `base_bbl`, `mappluto_bbl`, `feature_code`, `construction_year`, `last_edited_date` (normalizing known Socrata export header spellings).

Example once a **real** provider export, date and original independent SHA-256 receipt have been obtained:

```bash
python research_runners/nyc_building_archive_receipt_v0.py \
  /secure/local/archived-nyc-building.csv \
  --expected-sha256 <independently-recorded-64-hex-sha256> \
  --provider-version-date 2024-MM-DD
```

**The example date is deliberately not an actual release date.** The tool will reject a nonnumeric placeholder until a genuine YYYY-MM-DD value is provided. It performs no network access and prints neither original IDs nor geometry nor local file path. It never copies source bytes into Git, logs source rows, uploads anything to Neon, or creates OED/NextGen exposures.

For ZIP input it rejects traversal paths, multiple CSVs, encryption, unsupported compression, implausible compression ratios and excessive archive members; there is **no extraction**. Byte/header caps and required source-view pinning apply. Incorrect source dates, missing headers, wrong SHA, or use of the historic-only view fail closed. `tests/test_nyc_building_archive_receipt_v0.py` contains **eight synthetic/offline tests**.

## Exactly what a passing gate means

| Result flag | Meaning |
| --- | --- |
| `entire_container_sha256_matches_expected=true` | The local file matched the **provided** fingerprint; this does not authenticate the source or timestamp |
| `required_header_fields_found=8` | All eight expected *names* are present; source row contents are **not** validated |
| `date_is_caller_declaration_not_provider_verified=true` | Date provided by operator is **not** independently attested by file or provider |
| `full_csv_record_count_verified=false` | Full row-count conservation has **not** been tested |
| `official_snapshot_release_authenticity_verified=false` | No original provider archival-version certificate/ID has been matched |
| `historic_inventory_year_2024_admitted=false` | Source remains outside historical inventory and CAT models |

**Passing is only local integrity plus header readiness, never proof that the supplied bytes belong to 2024.** A current 2026 export can pass with an arbitrary caller date if the caller also supplies a matching SHA; this is why the official-provider date/version gate is explicitly independent and stays false.

## Next source-specific steps before building any 2024 insurer exposure

1. Inspect the NYC BUILDING Dataset Changelog for the precise closest archive version at/before 2024-12-31. If no such version can be exported, use the NYC Open Data request channel and capture the provider's response, exact view identity and archive timestamp.
2. Download actual original archive bytes **outside the repository**; record complete file size and independently pinned SHA-256. Confirm that the archive has the same semantics and expected field schema; early source versions may lack current `DOITT_ID` / `MAPPLUTO_BBL`, which requires a new reviewed historical crosswalk rather than weakening this gate.
3. Run the local byte/header gate; separately verify the **official archived release identity** and rights, then implement an authenticated full-row-count conservation check, coordinate reference, geometry topology checks and independent date-aligned identifiers. None of these checks are done by this script.
4. Reconcile historical building additions, demolitions and alterations with the 2024 LL84 property grain and only then derive synthetic insured value/cost/occupancy priors with explicit uncertainty. No claim of actual insurer policy membership or insured loss is justified by footprint presence.

**Why separate gates:** source discoverability, local byte integrity, provider version authenticity, scientific building identity and insurance-model admission are independent claims and must not be collapsed into one green result.
