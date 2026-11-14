<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin 2025: cross-insurer named corporate dwelling stock reference

**Research-only.** New [source-gated runner](../../research_runners/public_named_insurer_berlin_corporate_stock_report_v0.py) combines two existing, independently published facts without inventing real insured properties:

1. [April 2025 Senate Drucksache 19/22033](https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-22033.pdf): six named Berlin housing-company relationships with five original named insurer labels. The existing [source-bound insurer-report runner](../../research_runners/public_named_corporate_insurer_report_v0.py) confirms eight carrier-to-corporate-account associations.
2. [November 2025 Senate Drucksache 19/24229](https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-24229.pdf): official June 30 *dwelling* inventories by seven operators across twelve Berlin boroughs, including an unassigned/other category; Berlinovo September 30 inventory is **excluded** from this carrier-account join because no named carrier relationship was supplied.

The existing [R+V original PDF provenance gate](../../research_runners/rva_berlin_named_corporate_borough_opportunity_sensitivity_v0.py) has independent original-byte/SHA-256 receipts for the two official PDFs, with a separate source workflow. This new runner checks the pinned receipt, validates the published per-company and per-borough numbers and refuses any admission of insured individual buildings, TIV or treaty terms. It does **not re-download** the PDFs on each run, prove every source cell independently or infer 2026 renewal.

## Reproduce locally

```bash
python research_runners/public_named_insurer_berlin_corporate_stock_report_v0.py > /tmp/berlin_carrier_named_corporate_stock_reference.json
python -m unittest discover -s tests -p 'test_public_named_insurer_berlin_corporate_stock_report_v0.py' -v
```

Output is deterministic sorted JSON with SHA-256 checksums of both canonical *research observation input files*, original document URLs and dates, by-carrier company memberships, per-company borough dwelling counts and independent twelve-borough plus unassigned reconciliation. No third-party raw source data or local database updates are committed.

## Verified *corporate stock references*, not carrier exposures

| Original insurer label | Publicly named company accounts | 2025 published corporate dwellings incl. unassigned stock | In the 12 Berlin boroughs | Main ambiguity |
| --- | --- | ---: | ---: | --- |
| R+V Allgemeine Versicherung AG | GESOBAU, WBM, degewo | 165,731 | 162,883 | degewo consortium with Allianz; insurer covered-stock fraction and share unknown |
| Allianz AG | degewo, STADT UND LAND | 135,941 | 132,334 | degewo consortium; percentages unknown |
| ERGO | Gewobag | 75,091 | 74,762 | Another insurer also named, no documented split or consortium inference |
| Generali | Gewobag | 75,091 | 74,762 | Same corporate stock as ERGO; counts must **not** be added |
| Westfälische Provinzial Versicherung AG | HOWOGE | 82,152 | 81,876 | 2026 renewal, asset schedule and insured TIV unknown |

**These figures are published corporation-owned/managed stock opportunity references, not measured insured units for the named carriers.** Across carrier names the table counts overlapping corporate stock more than once. No weighted portfolio allocation, coin-share, TIV, insured address, CAT OEP/AEP, insurer loss or insurer 2026 policy assertion is made. The sum across table rows is explicitly invalid as an exposure measure.

### Scientific interpretation

- The comparison reveals **which company stock geography may be relevant to further research on each insurer**, but the April company insurer relationship is different from June company dwelling inventory and neither proves exact property coverage.
- A *dwelling* is not a physical building, and a housing company can hold multiple buildings under a corporate blanket contract. The master-policy carrier is not necessarily the carrier for every separate commercial property.
- For degewo the Senate explicitly describes Allianz/R+V consortium; an 0/50/100 share experiment is a separate fictional sensitivity, not revealed contract shares. For Gewobag ERGO and Generali are listed, but consortium status is not assumed.
- The names are **as reported** by the source, not verified Legal Entity Identifiers, modern ownership mapping or current insurer authorization; avoid silently converting group brand to solo legal entity.

## Next research promotion gates

1. Produce independent date-aware legal-entity ID mapping for *each* carrier from official regulator/LEI evidence, retaining original reported text and ambiguous aliases. Do not guess IDs from names.
2. Independently join publicly available named company property **buildings** and replacement-value priors with validated owner/company keys, reporting spatial and insurance-coverage uncertainty. The current Berlin public WFS does **not** expose verified company identifiers and cannot be directly attributed to the reported insurers.
3. For scenario portfolios, declare hypotheses for selection, per-building insured sums, policy conditions and original German peril event vulnerability. Only after licensed source/asset and model admission may company-level CAT run outputs be interpreted as modelled gross/net insurance losses.

**Boundary:** A reusable reports layer, not an admitted `manifests/` exposure source; no new legal/rights permission, external source bytes, personally identifying risk site addresses, actual insurance claims or customer schedules.
