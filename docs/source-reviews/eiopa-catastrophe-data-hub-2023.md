<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: EIOPA Catastrophe Data Hub public files, 2023-12-05

- Review date: **2026-08-10**
- Admission state: **metadata only**
- Manifests:
  - `manifests/eiopa.catastrophe-data-hub.exposure.2023-12-05.json`
  - `manifests/eiopa.catastrophe-data-hub.historical-loss.2023-12-05.json`
- Provider: European Insurance and Occupational Pensions Authority (EIOPA)
- Product family: Catastrophe Data Hub
- Public resource date: `2023-12-05`

## Why this source is useful

The Catastrophe Data Hub contributes public, aggregated **insurance-sector exposure and incurred-loss evidence**. The two public XLSX resources remain separate source identities because insured exposure and historical incurred loss are different scientific layers.

This review does not treat either workbook as a complete European market view, an insurer portfolio, or a transferable calibration target.

## Public identity

EIOPA lists the following resources with publication date 5 December 2023:

- `Flood and Windstorm exposure data - catastrophe data hub.xlsx`;
- `Historical loss data - catastrophe data hub.xlsx`;
- Technical Description EIOPA-BoS-22/505, dated 27 November 2023.

At this source review time, no workbook bytes had been acquired. A publication date or resource-page identity does not replace byte size plus SHA-256 for a future raw admission; later external receipts do not retroactively alter this review-time statement or authorize Git publication.

## Rights: metadata cleared; workbook redistribution blocked

EIOPA's general legal notice authorises reproduction of information/documents from its website with EIOPA acknowledged as source and provides conditions for transformed material and material incorporated into documents that are sold. The same notice excludes third-party material.

The Catastrophe Data Hub workbooks are based on information reported by insurance undertakings/groups and, for some country-specific exposure data, other contributors. Because the exact XLSX files were not inspected for embedded notices or third-party conditions, OpenCatastrophe does **not** infer raw or derived workbook redistribution rights from the general website notice.

The engineering rights ceiling is therefore:

- public EIOPA resource metadata: cleared with source acknowledgement;
- commercial context for EIOPA website material: allowed under the legal-notice conditions;
- raw workbook redistribution: not approved;
- derived workbook content: not approved;
- repository scope: metadata only.

This is a conservative engineering release decision, not legal advice.

## Sample and aggregation limitations

EIOPA states that the data are based on a subset of insurance companies and do not represent a 100% market view. The technical description identifies 35 large European non-life groups and 9 non-life/composite solo undertakings in the sample. Aggregate sample coverage is reported at about 59% of EEA-wide 2020 gross premiums for fire and other damage to property, with material country variation.

Those sample percentages are not a gross-up factor.

The public data are aggregated to NUTS2 for anonymity. The loss view also uses an aggregation rule under which each displayed point represents at least three company-submitted values; some residential/commercial values are combined.

## Insured exposure semantics

The technical description defines the exposure view as overall/replacement value of insured residential and commercial buildings. The public view covers flood and windstorm and uses year-end 2020 data.

Key boundaries:

- industrial properties are included in commercial for this analysis;
- the aggregated monetary replacement value is called sum insured;
- values are described as net of reinsurance business and coinsurance;
- original collection can be CRESTA low resolution or NUTS3 depending on country/reporting scheme;
- EIOPA converts the analysis to NUTS2.

This is insured exposure, not total physical building stock, a 100% market TIV, or a confidential policy/location schedule.

## Historical loss semantics

The loss view contains incurred claims reported by the undertakings/groups in the sample for three initial events:

- Central European flood, June 2013;
- Portugal wildfire, June 2017;
- European windstorm Ciara/Sabine, February 2020.

Claims are split where available by residential/commercial and building/other coverage. EIOPA notes that other claims can include contents or business interruption.

These aggregates are not ground-up economic loss, insurer-specific claims history, or universal vulnerability functions.

## Requirements before workbook admission

For each XLSX independently, a future proposal must:

1. re-check the current hub page, legal notice and any file-specific terms;
2. acquire the exact workbook outside Git;
3. inspect workbook-level copyright, third-party and confidentiality notices;
4. resolve raw/derived redistribution for that exact file;
5. record byte size and SHA-256;
6. record workbook/sheet names, field semantics, currency/units, suppression/missing rules and geographic identifiers;
7. preserve sample/anonymity limitations; and
8. obtain explicit asset-specific publication review.

Until then, no EIOPA Catastrophe Data Hub XLSX bytes or derived tables belong in this repository.

## Authoritative public references

- Catastrophe Data Hub: `https://www.eiopa.europa.eu/tools-and-data/catastrophe-data-hub_en`
- EIOPA legal notice: `https://www.eiopa.europa.eu/legal-notice_en`
- Technical description: linked from the Catastrophe Data Hub page.
