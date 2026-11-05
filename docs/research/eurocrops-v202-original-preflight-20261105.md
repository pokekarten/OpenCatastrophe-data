<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EuroCropsV2.02 original-file pilot: corrected agricultural parcel preflight

Research date: 2026-11-05. RESEARCH ONLY, NOT_ADMITTED. No insurance exposure, source bytes or provider-derived parcel records are committed.

## Provider and exact source family

- JRC dataset https://data.jrc.ec.europa.eu/dataset/b9fb9e67-78a9-4327-9d59-39a928d812d3
- JRC original corrected download folder: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DRLL/EuroCropsV2/gpqtv202/
- Exact pilot asset: de4_2023.parquet, region DE4 (Brandenburg; not all Germany), about 136 MB, folder listing timestamp 2026-07-02. Secondary German region DEA (Nordrhein-Westfalen) has a distinct 2023 file, about 302 MB.
- Provider fields: cropfield, original_code, area_ha, geom; GeoParquet CRS EPSG:3035. The unit area_ha means hectares; this is not harvested production, insured value or event damage.
- Original copyright notice: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DRLL/EuroCropsV2/copyright.txt. The JRC says CC BY 4.0 with attribution and change notices. Admission to our project, national upstream rights and privacy require independent review.
- Provider release history describes initial gpqt, v201 stack correction and v202 overlapping-polygon geometry correction (mainly Spain). Do not silently mix vintages or compare flawed stacked outputs as independent truth.
- 2008–2023 observed national paying-agency declarations vary by region and year. Some fields may be missing, self-declared or overlapped. NL BRP is an underlying source for EuroCrops, so the two must not be treated as independent observations.

## Manual original-file acquisition path (operator opt-in only)

A fixed-origin, fail-closed original download helper is now available:

    mkdir -p /tmp/oc-eurocrops-originals
    python research_runners/eurocrops_jrc_acquire_v0.py \
      --live --destination-dir /tmp/oc-eurocrops-originals

It makes an explicit opt-in **GET** for exactly `gpqtv202/de4_2023.parquet` on the official JRC host over HTTPS (only the equivalent JRC public distribution URL may redirect); refuses a symlink directory, overwrite, Git-checkout destination, unexpected HTTP status/final URL or encoding; streams a maximum of **180 MiB**; verifies the Parquet magic before retaining the file; removes its partial file on error; emits only a JSON first-seen provenance receipt including observed SHA-256. The original bytes and resulting CSVs must **not be committed**.

**Important provenance limit:** SHA-256 observed during this transfer is a **first-seen download checksum**, not a separately published or publisher-signed checksum and therefore does **not** independently prove publisher authenticity or source immutability. Preserve source URL, retrieval timestamp, byte count and hash to enable repeatable re-download comparisons. The EuroCrops source, licence and scientific eligibility stay `NOT_ADMITTED`. This manual helper does not run in GitHub CI and cannot bypass source review. No real publisher bytes were downloaded during the current isolated run (JRC DNS resolution failed). Its six offline synthetic network-stub tests are in `tests/test_eurocrops_jrc_acquire_v0.py`.

Once the download succeeded on an authorized host, use the receipt's `original_sha256` with the file preflight below, then separately verify the original mapping CSV source pin and its HCAT4 coverage. Don't confuse a successful byte transfer with taxonomy, geographical completeness, insured value or risk-model readiness.

## Executable research-only quality gate

Run research_runners/eurocrops_v202_preflight_v0.py offline, against a locally acquired exact original JRC file and an independently captured original SHA256. It does not download data, put coordinates in Git or modify Neon. For a local sample it:

1. Requires matching annual region/year filename, checks size and header/footer and matches full-file SHA256 to the caller-pinned source digest.
2. Inspects GeoParquet original schema and metadata; rejects non-EPSG:3035 or absent coordinate evidence.
3. Scans only up to 5,000 rows, counts missing codes, duplicate sampled cropfield identifiers, null/non-finite/nonpositive hectare areas, invalid WKB topologies, non-polygon shapes and area mismatch greater than 5%.
4. Emits only aggregate quality metrics and original file metadata in JSON; it never emits original parcel geometries, landholder identities or insured values.
5. Keeps rights_and_scientific_admission = NOT_REVIEWED_NOT_ADMITTED and loss_or_insurer_exposure_model_ready = false on every successful preflight.

Optional original-file runtime dependencies: pyarrow, shapely. These are not added to base repository requirements. Shapely is already present in validation requirements for synthetic offline tests.

Usage (after a trusted original file download and independent checksum receipt):

    python research_runners/eurocrops_v202_preflight_v0.py --input /external-originals/de4_2023.parquet --expected-sha256 <64-lowercase-hex-source-sha256> --sample-rows 512

### Optional exact source-taxonomy join for the bounded original sample

To measure how many **real JRC source codes would resolve** to the publisher's HCAT4 hierarchy, pass both of the original, commit-pinned source taxonomy CSVs; incomplete or unpinned inputs are blocked.

Source repository commit: b556d10651b98684d5d5269916f8f34c9e017151

- EuroCrops mapping: https://github.com/Martincccc/EuroCropsV2/blob/b556d10651b98684d5d5269916f8f34c9e017151/data/cropcodemapping/eurocrops.csv (Git blob SHA-1: 37a58061df29036300862dc680c769a1b2727e15)
- HCAT4: https://github.com/Martincccc/EuroCropsV2/blob/b556d10651b98684d5d5269916f8f34c9e017151/data/cropcodemapping/hcat4.csv (Git blob SHA-1: 7b4a7d1b5f3312d011958d0a1943c1324c3610ca)

    python research_runners/eurocrops_v202_preflight_v0.py \
      --input /external-originals/de4_2023.parquet \
      --expected-sha256 <trusted-original-parquet-sha256> \
      --mapping /external-originals/eurocrops.csv \
      --mapping-git-blob-sha1 37a58061df29036300862dc680c769a1b2727e15 \
      --hierarchy /external-originals/hcat4.csv \
      --hierarchy-git-blob-sha1 7b4a7d1b5f3312d011958d0a1943c1324c3610ca

The emitted `sample_taxonomy_crosswalk` is **counts only**: resolved, missing NUTS-specific mapping, mapping to an absent HCAT4 code, and blank/non-string original codes. A real JRC source code must be joined on **(NUTS, exact string original_code)**. Missing classification, upstream synthetic placeholder codes and missing actual original polygons must never become fabricated crop types, insured area, crop yield, TIV or loss. When taxonomy files are omitted, the output explicitly records `taxonomy_crosswalk_checked=false`, never a silent positive result.

Synthetic tests:

    python -m unittest discover -s tests -p test_eurocrops_v202_preflight_v0.py -q
    python -m unittest discover -s tests -p test_eurocrops_codebook_qc_v0.py -q

## Execution boundary, observations and next step

JRC catalogue and directory listing, version history and original CC BY notice were reviewed. The actual 136 MB provider parquet was NOT downloaded or inspected here: the isolated Linux runtime could not resolve the JRC host over DNS. The synthetic preflight logic and tests were executed locally against fabricated polygons (3 unittest checks passed in a pilot copy; repository CI still unconfirmed). No original file SHA, actual parcel count, crop-code distribution, regional insured value or hazard overlay has been measured or claimed.

Next: acquire de4_2023.parquet from the exact JRC corrected folder in a permitted runner; record original download URL, date, byte length and SHA256; run the preflight; inspect unknown-code percentages/CRS and investigate the first bounded defects; only then explore crop taxonomy/WorldCereal/hail and flood spatial overlay as a synthetic scenario, never as a real German insurer portfolio.
