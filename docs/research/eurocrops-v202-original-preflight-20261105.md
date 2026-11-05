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

Synthetic tests:

    python -m unittest discover -s tests -p test_eurocrops_v202_preflight_v0.py -q

## Execution boundary, observations and next step

JRC catalogue and directory listing, version history and original CC BY notice were reviewed. The actual 136 MB provider parquet was NOT downloaded or inspected here: the isolated Linux runtime could not resolve the JRC host over DNS. The synthetic preflight logic and tests were executed locally against fabricated polygons (3 unittest checks passed in a pilot copy; repository CI still unconfirmed). No original file SHA, actual parcel count, crop-code distribution, regional insured value or hazard overlay has been measured or claimed.

Next: acquire de4_2023.parquet from the exact JRC corrected folder in a permitted runner; record original download URL, date, byte length and SHA256; run the preflight; inspect unknown-code percentages/CRS and investigate the first bounded defects; only then explore crop taxonomy/WorldCereal/hail and flood spatial overlay as a synthetic scenario, never as a real German insurer portfolio.
