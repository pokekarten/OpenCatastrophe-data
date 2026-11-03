<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# German 2022/2025 district-building-to-carrier scope bridge: exact gates

**2026-11-03 research-only.** No copyrighted raw inputs, no original GDV mining, no observed district Allianz exposures, no production Neon writes, no model admission.

## Concrete, reviewed provider-product distinctions

1. **Destatis Zensus 2022 Regionaltabellen — Gebäude und Wohnungen.** Provider portal: https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/Publikationen/publikationen-akkordeon-regionaltabellen.html. It explicitly offers regional XLSX and machine-readable CSV for Bund/Länder/Kreise/Gemeinden with census date **2022-05-15**. The accompanying Excel workbook carries methodological footnotes and statistical symbols **not present in the CSV**. These symbols must be mapped to *unknown/suppressed* status, not zero. The exact CSV asset, its byte SHA, edition, tab/column identity, original rights and crosswalk are **not yet retrieved or verified here**.
2. **Separate Zensus 2022 building/dwelling grids** (100 m, 1 km, 10 km) are a distinct official product with separate coordinate, secrecy and lineage semantics. Its existence in the registry does **not** establish the regional table's exact numeric content or let an agent sum pseudonymized cells and claim true buildings at risk. Official overview: https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_inhalt.html.
3. **GDV Wohngebäude Elementardeckung**: https://www.gdv.de/gdv/statistik/datenservice-zum-naturgefahrenreport/sachversicherung-elementar/versicherungsdichte-bei-elementarschadenversicherung-regional-sehr-unterschiedlich-183592. An industry-wide relative percentage of residential building insurance against full elemental hazards (excluding certain stand-alone intense-rain cover) on approximately 400 districts. It is **not** a direct count of Allianz-insured properties, and its denominator/period must be bound to the exact dataset. The publisher's map is an interactive **23degrees.io** embed, not an explicitly reviewed redistributable raw district CSV. The page's publication/update metadata and the 2026 report's dataset vintage need independent reconciliation.
4. **Critical access decision, verbatim original terms reference**: https://www.gdv.de/gdv/statistik/nutzungsbedingungen-fuer-statistikdaten-und-deren-visualisierung-188704, last updated **2025-05-21**. Section 2.1 permits certain attributed uses and faithful transformations; Section 2.2 restricts stand-alone economic exploitation (including resale or charging for redistribution); Section 2.3 expressly reserves **text/data mining without express GDV consent**. This is **not** a blanket public-data licence to scrape the interactive map, download/extract all rows, bulk republish them or use them to train CAT/ML models. Section 1.3 allows differing rights for individually labelled PDF assets. Product-specific rights review, the contemplated commercial/model use, and the technical access path all remain required. **Do not run GDV automated extraction on the basis of a public website alone.**

## Why Zensus 2022 and insurer 2025 require a model bridge

| Universe | Year / geography | What actually is counted? | What cannot be inferred? |
| --- | --- | --- | --- |
| Zensus 2022 building table | 2022-05-15 Kreis geometry | Census-defined residential-use buildings or more specific categories | 2025 insured buildings or insurance contracts |
| Zensus 2022 dwelling table | 2022-05-15 Kreis geometry | Dwellings; several dwellings can be inside one building | Buildings or household insurance policies |
| GDV residential *full elemental* share | Exact 2025/vintage to be verified | Industry-wide percentage for a specific insured building reference universe | Individual insurer coverage or 2025 company building addresses |
| Allianz Versicherungs-AG 2025 HGB residential building | 2025-12-31 carrier solo | At-least-one-year **insurance contracts at year end**; and separately annual gross **written** premium | 1 contract = 1 residential building; regional market share; insured TIV |
| Allianz 2025 gross elemental loss expenditure | 2025 insurer accounting year | Published aggregate gross elemental-related expense | AEP, loss event IDs, GUL, ELT or event-specific YLT |

This prevents **five** quiet scientific errors: a 2022/25 vintage mismatch, a building/dwelling/contract denominator mismatch, territory-boundary mismatch, industry/issuer ownership confusion and GDV rights escalation.

### New executable synthetic study

`research_runners/synthetic_zensus_gdv_district_bridge_v0.py` consumes an **exact-schema, fully fictional** JSON study. Every input is invented and explicitly marked fictional or hypothetical. In particular it does **not** ingest actual GDV or Zensus data or claim insurer official regional observations.

Per 5-digit fictional German Kreis AGS, the study specifies:

- hypothetical 2022 residential-building count;
- explicitly hypothetical 2022 → 2025 building-stock growth factor;
- hypothetical maximum contract-equivalents per adjusted building (never an observed equality of contracts and buildings);
- **two** different fictional company geographic affinity weights;
- fictional full elemental-cover market rate plus separate assumed issuer/market multiplier;
- fictional annual direct gross-premium relativity.

It uses `research_runners/synthetic_regional_property_book_v0.py` as the conserved downstream engine, generating both books under **the same** synthetic nationwide end-year contract count and annual direct GWP in euro-cents. It challenges capacity infeasibility and quantifies **geographic total variation** between the two plausible fictional books, even though both obey the national totals.

A scientific comparison of those books against an actual cyclone/flood hazard cannot be called validated until local risk-site locations, cover terms, TIV, period alignment and an independently selected (not overfit) event-peril test are available.

### Exact test / readiness status

17 independent fictional test methods in `tests/test_synthetic_zensus_gdv_district_bridge_v0.py` exercise integer-and-cent conservation, prior nonidentifiability, five-digit district key validation, different Census/market/insurer dates, suppressed/zero buildings, forbidden source use and other negative scenarios. These tests are NOT an original dataset acquisition or jurisdictional licence decision.

**The next actual-data step:** acquire the selected **Destatis** *regional CSV plus its methodology workbook* in an access-approved external staging area; freeze original SHA-256/version and exact table/column identities; verify suppressed cells and Kreis AGS against the **15 May 2022** boundary release. Separately obtain an exact **GDV written permission or unambiguous scope-specific exception** before any automated district-table extraction or CAT product redistribution. Build at least two *independently justified* and uncertainty-labelled carrier priors rather than copying the industry-wide coverage map into a company portfolio. Only then move toward NextGen OED location/coverage and event-loss simulation gates.

No extraction in this work changes the production DB: zero `entity.published_metric`, `exposure.portfolio` and `exposure.exposure_unit` rows on last live check.

## Exact publisher file and original-byte receipt execution lane

**New exact XLSX URL independently resolved from official Destatis publisher site:**  
https://www.destatis.de/static/DE/zensus/gitterdaten/Regionaltabelle_Gebaeude_Wohnungen.xlsx

This is the official ~20 MB *regional* Buildings-and-Dwellings workbook
rather than the separately registered 100 m/1 km building-grid ZIP.
The publisher text calls out a machine-readable flat/CSV structure and
an "Erläuterungen zur Methodik" tab, while warning that nonnumeric
suppression/annotation markers still occur in CSV-like fields. **Do not
assert that a separately downloadable exact CSV URL has been found**
merely because the XLSX contains machine-readable worksheets.

**New exact-byte tool:** `research_runners/zensus_regional_original_receipt_v0.py`
only accepts the **single fixed publisher HTTPS URL** for an optional
network fetch. Redirects outside the publisher host fail. It caps source
body at 36 MB, recognizes a valid bounded OOXML package, enumerates real
Excel worksheet names from `xl/workbook.xml`, and emits the SHA-256 of
**complete raw workbook bytes**, file length, sheet names, presence of
methodology-labeled sheets and unambiguous non-admission flags. It
intentionally does not parse or republish building counts or any actual
Census/GDV/insurer row. The original XLSX is in memory on the test runner,
and no raw files or cell tables are added to the public repository.

**New separate GitHub Actions lane:**
`.github/workflows/zensus2022-original-workbook-receipt.yml` triggers on
its own code/doc changes, and can be manually dispatched. It first runs
ten entirely synthetic OOXML integrity/invalid-URL tests, then attempts
the single official source download in an isolated runner; the workflow
must **fail** if network acquisition, complete-byte hashing, package
format or source URL identity is not confirmed. The logs supply the
true SHA / sheet-title receipt only if the original source was actually
retrieved. No artificial "verified" status is emitted on a network
failure. This workflow makes progress on original-source identification
but still does **not** establish tabular column definitions, district
counts, Census code meaning, rights approval or model admission.

The current local container's DNS cannot resolve `www.destatis.de`.
For this reason the exact original download is being tested on the
separate GitHub Actions runner; consult the result of the **exact PR
head** before claiming that the PDF/XLSX source check passed.
