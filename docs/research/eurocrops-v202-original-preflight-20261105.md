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
- **Observed original DE4 2023 Parquet footer (2026-11-05):** the actual columns are `cropfield`, `original_code`, `original_name`, `off_area`, **`geometry`** and `area_ha`. Its GeoParquet `primary_column` is **`geometry`** (not `geom`), WKB, EPSG:3035. The provider's general README describes `geom`, but the exact original DE4 asset differs. `area_ha` is a computed area in hectares, not harvested production, insured value or event damage.
- Original copyright notice: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DRLL/EuroCropsV2/copyright.txt. The JRC says CC BY 4.0 with attribution and change notices. Admission to our project, national upstream rights and privacy require independent review.
- Provider release history describes initial gpqt, v201 stack correction and v202 overlapping-polygon geometry correction (mainly Spain). Do not silently mix vintages or compare flawed stacked outputs as independent truth.
- 2008–2023 observed national paying-agency declarations vary by region and year. Some fields may be missing, self-declared or overlapped. NL BRP is an underlying source for EuroCrops, so the two must not be treated as independent observations.

## Manual original-file acquisition path (operator opt-in only)

A fixed-origin, fail-closed original download helper is now available:

    mkdir -p /tmp/oc-eurocrops-originals
    python research_runners/eurocrops_jrc_acquire_v0.py \
      --live --destination-dir /tmp/oc-eurocrops-originals

It makes an explicit opt-in **GET** for exactly `gpqtv202/de4_2023.parquet` on the official JRC host over HTTPS (only the equivalent JRC public distribution URL may redirect); refuses a symlink directory, overwrite, Git-checkout destination, unexpected HTTP status/final URL or encoding; streams a maximum of **180 MiB**; verifies the Parquet magic before retaining the file; removes its partial file on error; emits only a JSON first-seen provenance receipt including observed SHA-256. The original bytes and resulting CSVs must **not be committed**.

**Important provenance limit:** SHA-256 observed during this transfer is a **first-seen download checksum**, not a separately published or publisher-signed checksum and therefore does **not** independently prove publisher authenticity or source immutability. Preserve source URL, retrieval timestamp, byte count and hash to enable repeatable re-download comparisons. The EuroCrops source, licence and scientific eligibility stay `NOT_ADMITTED`. The manual helper does not run in **default repository CI**, but the dedicated path-triggered source-only workflow `.github/workflows/eurocrops-de4-original-one-shot.yml` explicitly opted in, downloaded the original full file in ephemeral GitHub Actions runs and uploaded **aggregate JSON receipts only**. The independent local Linux environment continued to have JRC DNS problems, not the GitHub source-only runner. The six offline synthetic network-stub tests are in `tests/test_eurocrops_jrc_acquire_v0.py`.

Once the download succeeded on an authorized host, use the receipt's `original_sha256` with the file preflight below, then separately verify the original mapping CSV source pin and its HCAT4 coverage. Don't confuse a successful byte transfer with taxonomy, geographical completeness, insured value or risk-model readiness.

## Executable research-only quality gate

Run research_runners/eurocrops_v202_preflight_v0.py offline, against a locally acquired exact original JRC file and an independently captured original SHA256. It does not download data, put coordinates in Git or modify Neon. For a local sample it:

1. Requires matching annual region/year filename, checks size and header/footer and matches full-file SHA256 to the caller-pinned source digest.
2. Inspects the **original GeoParquet-declared primary geometry column** (`geometry` for DE4 2023; only `geometry` or `geom` permitted when independently declared), enforces WKB, original schema membership and EPSG:3035; rejects guessing a geometry name or interpreting `off_area` as projected polygon area.
3. Selects up to 5,000 rows **uniformly without replacement across the entire file** using a deterministic seed derived from the verified original full-file SHA-256. It reads only bounded batches from the selected Parquet row groups; the DE4 asset has only one row group, so this is still a sample, not a full geometric audit. Counts invalid crop codes, duplicate sampled cropfield identifiers, null/non-finite/nonpositive hectare areas, invalid WKB topologies, non-polygon shapes and area mismatch greater than 5%.
4. Emits only aggregate quality metrics and original file metadata in JSON; it never emits original parcel geometries, landholder identities or insured values.
5. Reports the exact sample selection method and sampled row-group count, but **never exports source row offsets, geometries or identities**. Keeps rights_and_scientific_admission = NOT_REVIEWED_NOT_ADMITTED and loss_or_insurer_exposure_model_ready = false on every successful preflight.

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

### Exact original area-only verification (optional, requires full source file)

The original JRC DE4 2023 footer **declares `area_ha` minimum 0.0**. A 512-row random sample will not reliably find rare zero-valued fields. After downloading the exact corrected Parquet and independently pinning its **full-file** SHA-256, run:

    python research_runners/eurocrops_v202_preflight_v0.py \
      --input /external-originals/de4_2023.parquet \
      --expected-sha256 <full-original-file-sha256> \
      --sample-rows 512 --scan-full-area

This **additional opt-in scan** reads only the entire `area_ha` attribute column in batches of at most 4,096 values and checks exact footer row-count conservation. It returns aggregate counts of zero, negative, nonfinite, null and nonnumeric source areas, plus the minimum/maximum positive source value. It never emits parcel IDs, original code values, geometries or crop values, and it does **not** validate the complete geometry or unique agricultural area. The existing polygon WKB sample remains a separate, bounded QA step. Absence of Parquet page/column offset indexes in the observed footer prevents trivial page-index lookup of the zero-area record.

The original metadata/zero-area warning and its footer-only SHA-256 are documented in [the exact original JRC footer receipt](eurocrops-v202-de4-2023-original-parquet-footer-20261105.md). **Subsequent original-provider runs have now acquired the full file on ephemeral GitHub runners and executed the complete area-column scan:** [run 42115645801](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42115645801), followed by all 65 zero-area WKB checks and the complete 285,606-row original topology/codebook QC. See [the full source report](eurocrops-v202-de4-2023-original-full-qc-20261105.md).

Synthetic tests:

    python -m unittest discover -s tests -p test_eurocrops_v202_preflight_v0.py -q
    python -m unittest discover -s tests -p test_eurocrops_codebook_qc_v0.py -q

## Execution boundary, observations and next step

The JRC catalogue, version history and CC BY notice were reviewed. Since the initial synthetic preflight, **targeted original provider byte-range requests succeeded** through a separate web retrieval route: header magic `PAR1`, trailer `PAR1`, a 16,258-byte Parquet footer, actual six-column schema with `geometry` rather than `geom`, EPSG:3035/WKB, and **285,606 original footer-declared records in one row group**. Footer column statistics report zero nulls across all six columns; these are metadata claims, not individual original row validation. Full provenance and the partial-byte-only footer SHA-256 are recorded in [the exact original JRC footer receipt](eurocrops-v202-de4-2023-original-parquet-footer-20261105.md).

The complete **143,006,611-byte** provider Parquet was successfully downloaded and repeat-hashed on isolated GitHub Actions runners, even though the separate local Linux environment still cannot resolve the JRC hostname. First-seen original file SHA-256: `4fc38f688a117db6cd0821c7aafc71fbbd2e7a493044c51266ae289929d7b2b6` (NOT a publisher-signed hash). All **285,606** original WKB/area/code rows have now been scanned: **285,541** valid positive-area polygons, **65** empty WKB geometries, **zero** invalid polygon topologies, **zero** original duplicate IDs, and **six** HCAT4 hierarchy-reference gaps. The results and scientific limits are in [the complete original QC report](eurocrops-v202-de4-2023-original-full-qc-20261105.md). There is still no independent geographical overlap/coverage validation, insured agricultural TIV or real hazard-event overlay.

Next: quarantine the 65 verified empty geometries; retain the six original HCAT4 hierarchy gaps as unknown taxonomy rather than inventing a valid crop. Verify true source seasonality, original licence rights, missing coverage and spatial polygon overlaps or independent national land-use controls before linking any real flood/hail hazard. Crop values, insurer allocation, financial terms and genuine annual OEP/AEP remain separate unapproved model inputs.
