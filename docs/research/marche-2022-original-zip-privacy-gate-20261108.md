<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Marche 2022 building damage – original-source frozen survey QA (2026-11-08)

**Scope:** authenticated original Zenodo record and exact immutable bytes; ZIP/XLSX **structural** audit. This is not source admission, data anonymization, commercial rights clearance, an empirical fitted damage function, independent hydrodynamic verification, a stochastic flood catalog, or a reproducible insured CAT-loss curve. **No third-party survey bytes, identifiers, coordinates or property-level values were committed.**

## DOI/version correction to the existing source record

- Paper: Rrokaj et al. (2025), *Survey data of damaged residential buildings and business premises from the 2022 record-breaking flood in the Marche region, Italy*, https://doi.org/10.5194/essd-17-6487-2025 .
- **Concept/all-version DOI:** https://doi.org/10.5281/zenodo.15591850 (links to latest known version, not an immutable asset identity).
- **Frozen original dataset/release:** https://doi.org/10.5281/zenodo.17457884 , Zenodo API https://zenodo.org/api/records/17457884 , release **v1.0.1**, published **2025-10-27**, release metadata declares **CC BY 4.0**.
- For source identities, use immutable v1.0.1 DOI, **two separate** exact original ZIPs, MD5 reported by publisher and independent computed SHA-256. The source may carry personal/business-sensitive coordinates, narrative descriptions and survey material; CC BY 4.0 cannot be interpreted as consent to circulate individual-property data elsewhere or as an insurance portfolio.

| Original archive and product | Byte count | Publisher MD5 independently matched | Original bytes SHA-256 independently computed |
| --- | ---: | --- | --- |
| \`Industrial activities dataset.zip\` | **929,330** | \`a96690a9037dd11cf6cdaae414998dc9\` | \`a4e5a142450e3a9c63e0dcb964b674a55ca180a7c44ec852ecd8e48638d29847\` |
| \`Residential building dataset.zip\` | **891,047** | \`ddd017a153d38cb042e4cf2bcf59adf4\` | \`4785f5eae8940e5c8033758aac11d1b2d8b7e5f75fe19efab497dfd5453802cd\` |

Original publisher asset URLs (for operator-local retrieval; **not** downloaded by the runner):
- https://zenodo.org/api/records/17457884/files/Industrial%20activities%20dataset.zip/content
- https://zenodo.org/api/records/17457884/files/Residential%20building%20dataset.zip/content

The source ZIPs were acquired in isolated temporary processing only and **not stored in the repository or database**.

## Original structural findings – 256 unique primary surveys

Each archive contains five Form workbooks A–E, its corresponding data-dictionary workbook, source PDF forms and a README. Industrial archive contains 15 ZIP entries, residential archive 14 entries (including source directories). The Form A worksheets have **three header rows**, so populated worksheet rows must **not** be counted as building records directly. There are additionally **one** (industrial) and **three** (residential) formatting-only empty rows: these are not missing-ID survey cases.

| Metric | Industrial / commercial | Residential |
| --- | ---: | ---: |
| Distinct Form A parent IDs, source original | **133** | **123** |
| Duplicate Form A parent IDs | 0 | 0 |
| Form A header rows | 3 | 3 |
| Styled but entirely blank Form A rows ignored | 1 | 3 |
| Form A sheets | 1 | 1 |
| Form B sheets | 2 | 2 |
| Form C sheets | 2 | 2 |
| Form D sheets | 1 | 2 |
| Form E sheets | 1 | 2 |
| Data dictionary sheets | 7 | 9 |

Both Form A headers independently contain a specific row 3 key declaration: \`A3=ID\`, \`E3=Latitude\`, \`F3=Longitude\`. The QA code looks only at the uniqueness/existence of the Form A identifier (and these **static header labels**), and deliberately returns **no source identifier, coordinates, precise site information or survey text**.

The paper reports measured/reconstructed floodwater depth at **247 out of 256** buildings; the current structural preflight does **not** independently validate numeric water-depth accuracy, asset valuation, denominator TIV, engineering cost, damage ratios, or damaged-vs-undamaged site selection. Do not claim otherwise.

A separate metadata-only Form A probe found a column labelled **`Water surface elevation`** in both sectors (`AZ` for industrial, `AH` for residential), but it is **not an immediately usable numeric flood-depth target**: a basic numeric parsing attempt yielded numeric values for only 76 of 133 industrial records and 102 of 123 residential records, with the remainder carrying non-numeric content. These counts are solely a **typing/cleaning warning**, not a claim about whether any particular water depth exists or is missing. Do **not** equate this ambiguous field to the article's 247 depth-observation claim or use it as a modeled water-depth/TIV ratio without the source dictionary's unit, datatype and missing-code semantics. No original field values were logged.

## Reproduction: non-mutating original ZIP source check

Source code: [\`research_runners/marche_2022_survey_original_preflight_v0.py\`](../../research_runners/marche_2022_survey_original_preflight_v0.py).

Synthetic tests: [\`tests/test_marche_2022_survey_original_preflight_v0.py\`](../../tests/test_marche_2022_survey_original_preflight_v0.py).

\`\`\`bash
python -m unittest discover -s tests -p 'test_marche_2022_survey_original_preflight_v0.py' -v

python research_runners/marche_2022_survey_original_preflight_v0.py \
  --industrial-zip /secure/local/Industrial_activities_dataset_v1_0_1.zip \
  --residential-zip /secure/local/Residential_building_dataset_v1_0_1.zip
\`\`\`

The paths are caller-owned examples outside Git. The code verifies exact original ZIP size, MD5 and SHA-256; rejects traversal, symlinks, duplicate archive names, broken CRC, unexpected form/dictionary structure, unknown headers, blank populated parent IDs and duplicate Form A parent IDs, while ignoring purely formatted empty worksheet rows. Only **aggregate, privacy-safe** source metadata is emitted.

**Executed using the frozen GitHub PR code and original Zenodo archives:** 11/11 synthetic tests passed, original two-archive CLI exit 0 and output \`original_parent_surveys=256\` (133 industrial, 123 residential). A deliberately mismatched archive argument fails with nonzero exit, as intended. This is a targeted runtime validation, **not** a full GitHub Actions CI execution. The scientific review/admission status remains unchanged.

## How these observations can and cannot validate CAT models

The original event was the **2022-09-15 Marche region flood**; the surveys were performed October–December 2022 in Ostra, Senigallia and Trecastelli. Form A covers event/hazard, building/business vulnerabilities and observed damage types; other forms contain damage across floors/components, direct assets, recovery, and indirect business interruption or residential common/attached structures. They have different 1-to-many cardinalities, so **do not** join raw spreadsheets on ID without inspecting their form/section-level relationship rules; a row is not necessarily one property or one contract.

The paper used **Copernicus EMSR634** flood maps to select and navigate survey sites: https://mapping.emergency.copernicus.eu/activations/EMSR634/ . Thus a comparison with this same source footprint is **not** an independent validation of the field-sample selection. Field floodwater heights and damage information may help test depth/damage relationships but need original data dictionary review, units, valid/unknown values and special privacy gating. Not all assets were sampled, and there are **no survey observations of unaffected exposures** in these two ZIPs sufficient to estimate regional unconditional hazard probability.

To construct a proper independent building-flood vulnerability evaluation, later steps must establish legally permitted de-identified depth/severity targets, a **distinct** vulnerability fitting sample and held-out event/geography, physical damage valuation versus TIV denominators, commercial-use permissions where needed, and a truly independent exposure census. **One 2022 event cannot calibrate annual flood frequency, insured gross/net, or OEP/AEP.**

No database mutations, admission status changes, coordinate exports, commercial release, production OED conversion or loss-model calibration are performed by this pull request.
