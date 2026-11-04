<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Industrial physical-asset identity: EPA FRS × GEM research preflight (2026-11-04)

**Status: synthetic-only executable research; no source acquisition, original-byte authentication, licence admission, database write, insurer assignment or CAT model input.** Three new source candidates remain in [the discovery shard](../../landscape/sources-owner-facility-business-priors-20261104.json), not accepted manifests.

## Why a separate crosswalk is needed

- [EPA ECHO Exporter](https://echo.epa.gov/tools/data-downloads) is a US regulated-facility collection. Its [FRS dictionary](https://echo.epa.gov/tools/data-downloads/frs-download-summary) describes `REGISTRY_ID`, location fields, NAICS codes and agency-specific linked programme IDs. FRS identity does not prove insured physical buildings, ownership or replacement values.
- [GEM Global Energy Ownership Tracker](https://globalenergymonitor.org/projects/global-energy-ownership-tracker) October 2026 tracks physical project IDs and direct/ultimate entity owners. It exposes company identifiers including LEIs where available, and ownership connection sources. Its definition of an ultimate "parent" is not equivalent to an insurance group or a solvency consolidation perimeter.
- GEM **imputes some missing ownership percentages**. Those synthetic shares must not be represented as observed equity stakes, insured percentages, underwriting retentions, or treaty shares.
- **No original verified generic EPA FRS ↔ GEM asset cross-ID was found.** Shared names, industrial category or close coordinates alone do not prove a common asset.

## Executable, synthetic-only contract

The [runner](../../research_runners/industrial_frs_gem_identity_v0.py) and [14 tests](../../tests/test_industrial_frs_gem_identity_v0.py) audit caller-prepared *normalized projections*, **not native publisher data schemas**:

- FRS CSV: `frs_id,country_code,latitude,longitude`
- GEM CSV: `gem_asset_id,country_code,latitude,longitude`
- Link CSV: `frs_id,gem_asset_id,evidence_kind,evidence_url,evidence_sha256`

Callers must supply exact projection SHA-256s and explicit source snapshot dates. Each projection is capped at 1 MB / 10,000 rows. The runner does not fetch, write, export or approve any external data.

Link evidence kinds: `publisher_explicit_cross_id`, `independent_document` and `name_or_proximity_only`. Stronger assertions require a fixed HTTPS evidence URL without query parameters, credentials or fragments, plus a claimed original-evidence digest; **the script does not verify the original publisher bytes, URI content or rights**. A name/location-only link cannot qualify as an identity candidate.

Every FRS record ends in exactly one aggregate disposition: no link in selected subset, ambiguous cardinality, referenced GEM missing, unsupported name/proximity link, country contradiction, missing coordinates, distance greater than 5 km, or unique *research-only* candidate. More than 5 km is a **screen for review**, not a calibrated scientific or geographic rule; industrial sites can be large. Even unique linked records do not establish a building, parent company, LEI, insurer, policy, claim, TIV, or exposure admitted to a CAT model.

The output contains only totals, explicit source-vintage fields and SHA-256s of the supplied projections; it does not echo identifiers, company names, site coordinates, original evidence or assets.

Run on authorized local input after legal/scientific review:

```bash
python -m unittest discover -s tests -p 'test_industrial_frs_gem_identity_v0.py' -v
python research_runners/industrial_frs_gem_identity_v0.py \
  --frs-projection /approved/local/frs.csv --frs-sha256 HASH \
  --gem-projection /approved/local/gem.csv --gem-sha256 HASH \
  --links-projection /approved/local/links.csv --links-sha256 HASH \
  --frs-vintage YYYY-MM-DD --gem-vintage YYYY-MM-DD --link-vintage YYYY-MM-DD
```

Each native-to-normalized transform still needs a pinned original source version, audited column mappings, coordinate reference system and original-byte receipt. Projection hash validation is not source authenticity. No record in the subset does not mean no physical asset or no insurance exists. Multiple EPA identifiers can represent one physical site and one site can encompass multiple GEM projects: those links require typed n:m relationship modeling, not premature deduplication.

## Next falsifiable real-data test

1. Review exact GEM October 2026 download-product rights and EPA FRS selected original ZIP rights. Pin exact asset identity, file bytes, release dates and published field mappings before making small local projections; keep third-party files out of Git.
2. Check at most **5–10 real US sites** with individually documented third-party FRS↔GEM mapping evidence. Reject mere proximity, carry identity confidence and cardinality, and report genuine nonmatches/unknowns separately.
3. For GEM entities that carry **observed** LEIs, validate the IDs via existing GLEIF tools and keep GLEIF accounting consolidation distinct from GEM ownership. Separately preserve observed versus GEM-imputed stakes.
4. Only after independent asset geometry, actual vs imputed owner identity, economic asset-value priors and insurer financial constraints are approved, hand **distributions of synthetic scenarios** into NextGen. Do not reconstruct a claim that any public facility is insured by a named company.

**Execution evidence:** 14/14 new deterministic local unit tests and compilation passed in ChatGPT Linux on 2026-11-04. Repository-wide CI must be checked on the exact latest PR head. No provider original data, live site crosswalk or production database integration was executed.

## Original EPA FRS CSV projection pilot (added 2026-11-04)

The original [EPA ECHO FRS download dictionary](https://echo.epa.gov/tools/data-downloads/frs-download-summary) documents native `FRS_FACILITIES.csv` columns `REGISTRY_ID`, `LATITUDE_MEASURE`, `LONGITUDE_MEASURE` and facility name/address attributes. Its ECHO subset differs from EPA's separately downloadable full FRS inventory; do **not** merge their observation perimeters or vintages without a crosswalk.

The new [bounded native adapter](../../research_runners/epa_frs_native_projection_v0.py) and [synthetic tests](../../tests/test_epa_frs_native_projection_v0.py) consume an **already legally acquired, manually bounded native-format FRS facilities CSV slice** (max 2 MB / 10,000 rows), validate the caller-supplied slice SHA-256, real release date, mandatory native headers, unique source identifiers and syntactically valid coordinate pairs, and generate deterministic sorted `frs_id,country_code,latitude,longitude` rows for the existing FRS-GEM crosswalk. Raw names and addresses are **not** projected; no source bytes are committed or downloaded by this script. The CLI writes the projection only to an explicitly supplied, previously nonexistent file *outside* the repository and prints aggregate receipts.

**Important geographic restraint:** The currently consulted provider dictionary confirms the native latitude/longitude fields, but not sufficient coordinate datum, coordinate quality and transformation evidence for this audit. Therefore the CLI **suppresses all coordinates by default** and only produces an ID-safe projection. A direct Python caller can set `coordinates_approved=True` for a separately reviewed, exact-source, datum-verified local experiment, but that flag is a caller assertion, **not independently authenticated provider evidence** and does not grant any model admission. Never interpret coordinate suppression as a statement that the facility lacks a location. This stage cannot produce a geospatially accepted crosswalk.

Example with local pre-reviewed input (the placeholders are not usable file identities):

```bash
python -m unittest discover -s tests -p 'test_epa_frs_native_projection_v0.py' -v
python research_runners/epa_frs_native_projection_v0.py \
  --native-facilities-slice-csv /reviewed/private/FRS_FACILITIES_slice.csv \
  --native-slice-sha256 NATIVE_SLICE_SHA256 \
  --release-date YYYY-MM-DD \
  --output /reviewed/private/frs_id_only_projection.csv
```

This is a verified *transform contract*, not an EPA original dataset acquisition or an actual FRS-GEM match. A useful next measurement is the exact original ECHO-FRS ZIP or full-FRS source identity, the native facilities projection coverage, and an independent fixed coordinate reference/accuracy receipt before enabling geospatial comparison.

**Original-file identity correction:** The hash of a manually bounded native-format FRS CSV slice proves only the supplied *slice* bytes, not the EPA provider ZIP/file, its publisher version, or the original extraction process. The adapter machine report explicitly sets `publisher_original_file_bytes_authenticated=false` and `native_csv_slice_is_publisher_original=false`. Original provider hashes, exact licence and audited extraction provenance remain separate prerequisites before a real asset join.

## Native FRS NAICS multiple-activity audit (added 2026-11-04)

The [EPA ECHO original source dictionary](https://echo.epa.gov/tools/data-downloads/frs-download-summary) identifies native `FRS_NAICS_CODES.csv` columns `REGISTRY_ID`, `PGM_SYS_ACRNM`, `PGM_SYS_ID`, and six-digit `NAICS_CODE`. A single facility can carry multiple regulatory program IDs and multiple NAICS classifications. Converting each NAICS row into one unique building would **multiply physical assets and potentially insured TIV** incorrectly.

The [standalone offline aggregate audit](../../research_runners/epa_frs_naics_multiplicity_v0.py) and [synthetic-only tests](../../tests/test_epa_frs_naics_multiplicity_v0.py) compare an *FRS normalized research projection* against a separately supplied native-format NAICS CSV slice. The audit enforces original-column names, unique FRS projection identifiers, six-digit NAICS notation, distinct programme+system+facility+NAICS combinations and caller-claimed SHA-256 of each **slice**, without asserting these hashes authenticate EPA original ZIP files. It reports distinct facilities with codes, multiple distinct codes, duplicates of a code across different programmes, out-of-perimeter NAICS rows and **at-most-once per facility per two-digit sector** membership counts.

Sector counts can sum to **more than the total number of facilities**. A two-digit NAICS prefix is neither a Solvency-II line of business, a building occupancy assigned to one structure, nor an insured asset value. No insurer company, NAICS-to-OED occupancy, TIV or CAT business-interruption vulnerability is inferred. A missing NAICS link in a bounded slice does not mean the facility has no economic activity.

Execute offline on approved local slices (placeholders are nonfunctional):

```bash
python -m unittest discover -s tests -p 'test_epa_frs_naics_multiplicity_v0.py' -v
python research_runners/epa_frs_naics_multiplicity_v0.py \
  --frs-csv /reviewed/private/frs_id_only_projection.csv --frs-sha256 FRS_SLICE_SHA256 \
  --naics-csv /reviewed/private/FRS_NAICS_CODES_slice.csv --naics-sha256 NAICS_SLICE_SHA256 \
  --frs-vintage YYYY-MM-DD --naics-vintage YYYY-MM-DD
```

**Snapshot and taxonomy gate:** The facility projection and NAICS sample must be sourced from one explicitly shared release date; different reported vintages are rejected instead of silently combined. A six-digit code is not enough to identify the NAICS taxonomy *revision*; the audit marks codebook version as unverified pending original provider documentation.

**Next empirical decision:** freeze the original source archive identity and exact native extraction/perimeter before using any numerical NAICS-sector distribution in a synthetic company portfolio. This research audit is designed to expose join multiplication and source gaps, not to assign insurance risk.


## Native EPA FRS EIA-860 / ORIS identifier bridge (added 2026-11-04)

**This is the best current non-geospatial identity lead, but it is not yet a validated GEM match.**

- [Official EPA-owned FRS/EIA mashup example](https://github.com/USEPA/FRS-getfacilities-samples/blob/master/EIA-EPA_Mashup.md) documents that the FRS program acronym `EIA-860` and `PGM_SYS_ID` identify an EIA ORIS plant code. The official example uses Keystone plant **ORIS 3136** and **FRS Registry ID 110000538525**, illustrating the *historical meaning of the crosswalk*, not current site membership or an authenticated 2026 data response.
- [Official EIA-860 annual 2025](https://www.eia.gov/electricity/data/eia860/) publishes plant, utility, generator and generator-owner worksheets. An EIA plant ID is **not** an individual generator ID or an insured building. The generator ownership table omits generators wholly owned by their operator, so an absent ownership row is not absence of owners.
- [GEM Global Integrated Power Tracker September 2026](https://globalenergymonitor.org/projects/global-integrated-power-tracker) provides GEM unit/phase and location identities, but its official methodology does **not** prove a universal EIA ORIS field on every row. The FRS↔EIA plant link and EIA↔GEM project link are separate evidence questions.

The [fail-closed ORIS bridge](../../research_runners/epa_frs_eia860_oris_crosswalk_v0.py) and [synthetic-only tests](../../tests/test_epa_frs_eia860_oris_crosswalk_v0.py) accept caller-supplied *native-format* FRS `FRS_PROGRAM_LINKS.csv` slice (columns `REGISTRY_ID`, `PGM_SYS_ACRNM`, `PGM_SYS_ID`) and a separate **normalized** deduplicated plant-ID projection from the EIA 2025 annual plant workbook. Each projection/slice is bounded and hash-checked, but provider original files are **not** authenticated by this audit. It canonicalizes numerical plant-ID zero padding, allows a many-to-many relation to be observed without multiplying plants, and reports one-to-one *research candidates*, cardinality conflicts, missing IDs within the selected subset and out-of-scope matches. No IDs or coordinates are printed. `eia_to_gem_asset_ids_confirmed=false`, `facility_ownership_or_insurance_inferred=false`, `source_rights_or_model_admission_granted=false` are permanent fail-closed outputs.

```bash
python -m unittest discover -s tests -p 'test_epa_frs_eia860_oris_crosswalk_v0.py' -v
python research_runners/epa_frs_eia860_oris_crosswalk_v0.py \
  --frs-program-links-slice /reviewed/private/FRS_PROGRAM_LINKS_slice.csv \
  --frs-sha256 FRS_NATIVE_SLICE_SHA256 --frs-release YYYY-MM-DD \
  --eia-plant-projection /reviewed/private/eia860_2025_plant_ids.csv \
  --eia-sha256 EIA_NORMALIZED_PROJECTION_SHA256 --eia-reporting-year 2025
```

The exact original 2025 EIA workbook/sheet header, EPA source ZIP timestamp and source-specific data reuse rights must be reviewed before a genuine run. It is **forbidden** to infer that a current EIA plant is a GEM unit, the owner is an insurance group, or that capacity/revenue equals TIV. This bridge is intended to provide independently inspectable *candidate identity*, and nothing further.

## First real original-response receipts (2026-11-04)

The first bounded live [EPA Delaware EIA-860 facility proof](epa-frs-eia860-live-original-json-receipts-20261104.md) has **three individually SHA-256-hashed original API HTTP response bodies**: 14 FRS facility records and 15 EIA-860 program IDs across three disjoint Delaware city queries, including one FRS record referring to two EIA plant IDs. This validates only source-reported *FRS ↔ EIA-860 program links*, not independent EIA 2025 annual-workbook membership or a GEM project mapping. The fresh ORIS 3136 standalone answer also exhibits contradictory provider site labeling; do not promote location, owner or insured-risk fields.

The ECHO FRS weekly programme-filtered download is not the complete EPA FRS registry. A blank EIA-860 link within that ECHO subset cannot be interpreted as evidence of a missing power plant in full FRS. Original-data access/usage rights, exact annual EIA file bytes, and geospatial accuracy remain separate gates.
