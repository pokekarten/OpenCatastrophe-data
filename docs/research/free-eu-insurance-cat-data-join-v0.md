<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Free European insured-CAT sources and NUTS2 windstorm comparison (v0)

Reviewed 2026-10-30. This adds no external data bytes, grants no additional rights and claims no calibrated insurance model. A free download, open access and Open Source are distinct conditions. EIOPA metadata-only admission in existing manifests/reviews is authoritative.

## Sources and precise integration limits

| Role | Official primary source | Access / rights | Scientific resolution |
| --- | --- | --- | --- |
| Insured sample exposure | https://www.eiopa.europa.eu/tools-and-data/catastrophe-data-hub_en | Two public XLSX links. Existing OpenCatastrophe admission is **metadata only**, raw and derived redistribution blocked until exact-file and third-party review | Year-end 2020 NUTS2 residential/commercial buildings and flood/windstorm cover; **35 groups + 9 solos, not 100% market**. Industrial is included in commercial and EIOPA exposure is net of reinsurance business/coinsurance, not total physical TIV |
| Historical insured claims | Same EIOPA hub, separate historical-loss XLSX | Same metadata-only limits | June 2013 Central Europe flood, June 2017 Portugal wildfire, February 2020 Ciara/Sabine storm; aggregate incurred claims from sample rather than insurer-unique losses |
| Historical storm footprints | https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-reanalysis | C3S CC BY, free ECMWF account / terms acceptance; freeze download query + bytes before scientific use | Event-specific 72-hour maximum 10-m wind gust NetCDF (0.25 degree ERA5 or downscaled 0.016 degree), tracked extratropical cyclones since 1940. Annual NUTS wind summaries are **not individual storm footprints** |
| Geocoding | https://gisco-services.ec.europa.eu/distribution/v2/nuts/ | Public GISCO NUTS files/API subject to explicit access/use terms | Multiple incompatible NUTS vintages. EIOPA's own converted NUTS version must be inspected, not guessed as 2021 or 2024 |
| German observed insured losses | https://www.gdv.de/gdv/statistik/datenservice-zum-naturgefahrenreport | Free presentation, but GDV explicitly reserves text-and-data-mining without written permission: https://www.gdv.de/gdv/statistik/nutzungsbedingungen-fuer-statistikdaten-und-deren-visualisierung-188704 | State-level hail/storm and elemental claims, claims frequency and insured penetration; not individual insurers and **not** automatically NUTS2 |
| European economic and insured country losses | https://www.eea.europa.eu/en/datahub/datahubitem-view/1fac8253-3df7-4408-b5fa-a6f2dc524182 | Public CSV/XLSX indicator. Check dataset-specific rights and upstream RiskLayer/CATDAT restrictions | Country-by-year economic and insured loss statistics, 1980–2024 product version; do not coerce economic losses into insured incurred losses |
| Buildings, not insurance | https://e.geoservice.dlr.de/web/datasets/wsf_3d and https://docs.overturemaps.org/guides/buildings/ | DLR WSF 3D states CC BY 4.0; Overture uses release/component-specific terms. Exact dataset review required | DLR 90m gridded area/height/volume or Overture building footprints. Neither identifies insurer or insurance attachment |
| Flood hazard / hydrology | https://european-flood.emergency.copernicus.eu/data-download | EFAS historical data >30 days are available on registration under Copernicus terms; live forecasts restricted | Hydrology model output, not insured claims or flood financial losses |

The public EIOPA hub links to:
- Historical loss XLSX: https://www.eiopa.europa.eu/document/download/50e6b095-174c-4d9c-b9dd-1376dc1d43eb_en?filename=Historical+loss+data.xlsx
- Windstorm/flood exposure XLSX: https://www.eiopa.europa.eu/document/download/d2be6f79-3e44-47f1-821f-97ff41e9d7b6_en?filename=Flood+and+Windstorm_exposure_data.xlsx

Attempted acquisition in the present runtime **failed** (HTTP 429 on EIOPA downloads via browsing; Linux download DNS unavailable). No actual XLSX sheet, actual EIOPA row, insurer location or vendor CAT footprint was acquired or rehosted. Do not claim this is an integrated real-data benchmark. Exact workbook bytes/sha256, sheet fields, source licence and snapshot version remain unchecked.

## Executable preflight and candidate join

Implemented at research_runners/regional_exposure_hazard_join_v0.py, tested with standalone synthetic tests in tests/test_regional_exposure_hazard_join_v0.py.

1. Obtain the EIOPA *sample* buildings sum-insured extract only after source-rights review. Keep region code, **verified** NUTS vintage, country/coverage, currency/units, residential/commercial category and year-end 2020 exposure date. Do not gross up the sample to 100% market by assumption.
2. Acquire historical **event-specific** C3S windstorm footprint under its CC BY licence with dataset version, track algorithm, event ID, query and raw checksum pinned. Aggregate 10-m max gust values into the *same verified* NUTS2 polygons with an explicit max-of-grid-cells operation. Annual NUTS indicators and event footprint cannot be substituted.
3. Supply locally prepared rights-cleared JSON with two arrays called exposures and hazards, matching the Python contract. Its event physical peril is extratropical_windstorm, an explicitly narrower phenomenon than broadly labelled insurance windstorm coverage.
4. The script refuses duplicates, unverified NUTS years, invented full-market flags, unsupported perils, ambiguous occupancy, invalid numbers and unaggregated grid values; unresolved geography stays explicitly unmatched.
5. **Temporal safety:** 2020-12-31 exposure cannot be treated as pre-event exposure for windstorm Ciara in February 2020. To study Ciara, an independently justified prior-year exposure snapshot/backcast would first be required.
6. Output is only a reproducible, input-hashed **observation-pairing** with unresolved rows and scope flags. It does NOT estimate claims, vulnerability, insurance policy loss, 100% market sums, company TIV, reinsurance or CAT capital.

Run the offline executable from the repository root with a locally prepared input:

    python research_runners/regional_exposure_hazard_join_v0.py /path/to/local-source-cleared-input.json
    PYTHONPATH=research_runners python -m unittest discover -s tests -p test_regional_exposure_hazard_join_v0.py -v

## Research roadmap

Priority P0: license-clear and pin C3S event data plus GISCO geographic version; verify the two EIOPA source workbooks (existing metadata-only manifests). Pilot DE/FR NUTS2 windstorm regional pairing and a separate explicit historical event claims validation lane. Never infer company allocation from EIOPA sample or substitute PERILS industry totals.

Priority P1: compare **separately** national GDV insured losses, EEA economic/insured country totals, and building stock from DLR/Overture. GDV text/data mining requires express permission; a documentation link does not grant an ingestion licence.

Priority P2: a genuine risk model for FFBK/NextGen requires peril-specific damage-to-value functions, insurance attachment/coverage terms, synthetic insurer scenario assumptions, shared event IDs and Monte Carlo years, then separate treaty and retrocession stages. This code intentionally does none of them.


## Further zero-price benchmark paths discovered 2026-10-30

**EIOPA 2025 Protection Gap input XLSX** — https://www.eiopa.europa.eu/tools-and-data/dashboard-insurance-protection-gap-natural-catastrophes_en: a **separate** public 4 December 2025 input workbook (240.73 KB) for the insurance protection gap dashboard; country-level economic/insured losses and coverage context across 30 European countries, historic window 1980–2024. It is not the 2020 NUTS2 exposure workbook. Check exact file contents and rights before local ingestion, and **do not double-count** EIOPA/EEA results or treat potentially shared upstream RiskLayer CATDAT and EM-DAT evidence as independent claims data.

**US FEMA OpenFEMA NFIP Redacted Policies and Claims** — https://www.fema.gov/openfema-data-page/fima-nfip-redacted-policies-v2 and https://www.fema.gov/openfema-data-page/fima-nfip-redacted-claims-v2. Free publicly available anonymised NFIP programme transaction data; coverage, premiums and paid flood claims support a potentially unusually useful **US flood insurance** validation lane. FEMA explicitly says these two released datasets are **not intended** for an exact record-by-record policyholder or structure join. Spatial fields are coarsened for privacy (e.g. census tract/ZIP), and claims vs policy experience require **aggregate matched-geography + insured-time** and distinct definitions. FEMA's official FAQ: https://agents.floodsmart.gov/flood-maps-and-data/faqs-about-nfip-data . API/page access and dataset rights still need asset-specific review before processing.

**USACE National Structure Inventory (NSI 2026)** — https://www.hec.usace.army.mil/confluence/nsi/technicalreferences/latest/technical-documentation . Modelled structure-point inventory with occupancy, attributes and **estimated full replacement costs**, available via data files/API. Not observed insured value and not exact structure truth; NSI 2022–2026 changes reflect model revisions, so do not infer 2022–2026 real growth by differencing records: https://www.hec.usace.army.mil/confluence/nsi/technicalreferences/2026/release-notes . A synthetic-flood portfolio can aggregate NSI **physical** stock to census tract/region and separately calibrate sample **insured attachment** using NFIP totals, with missingness and uncertainty visible.

**NOAA IBTrACS v04r01** — https://www.ncei.noaa.gov/products/international-best-track-archive . Free, regularly updated worldwide tropical cyclone **track** archive with downloadable CSV, NetCDF and Shapefiles and a citable DOI (10.25921/82ty-9e16); multiple originating agencies/provisional updates require storm ID and edition freeze. This does NOT supply insured claims, hazard wind footprints or full event-loss costs. OpenCatastrophe already has a reviewed IBTrACS source manifest and access contract, so **no duplicate source record is needed**.

Suggested independent US flood prototype after source rights review: NSI physical regional stock + FEMA NFIP aggregate programme policy coverage/claims, retaining programme and aggregation scope. Suggested EU refinement: EIOPA 2020 NUTS2 insured *sample* + C3S footprints + GISCO, then EIOPA 2025 protection gap **country-level** benchmark as a separate comparison. Both are independent from the 2026 PERILS **market-wide licensed** exposure benchmark. Never invent insurer identity or silently up-scale samples to market totals.


## Executed real-data inspection: official Eurostat NUTS-2 2021 and 2024

Live source read on **2026-10-30** through the connected GitHub reader. Data provider: **Eurostat**, [Nuts2json](https://github.com/eurostat/Nuts2json). Only source-level counts, immutable Git blob IDs and limits are recorded here; no source data bytes.

| Source | Actual GeoJSON file | Git content blob SHA | Actual features |
| --- | --- | --- | --- |
| 2021 | [pub/v2/2021/4326/nutspt_2.json](https://github.com/eurostat/Nuts2json/blob/master/pub/v2/2021/4326/nutspt_2.json) | 2aefe66cc5425d018e14702dfc4be04348258898 | **328** |
| 2024 | [pub/v2/2024/4326/nutspt_2.json](https://github.com/eurostat/Nuts2json/blob/master/pub/v2/2024/4326/nutspt_2.json) | eb9ef7743b1bd8bd524427fc5f6a883451c901f2 | **293** |

Git blob SHA identifies source bytes, **not** SHA256. The publisher's project includes an EUPL-1.2 licence file; the original GISCO geographical data have independent download/use conditions. No raw or derived geographic data, or licence upgrade, are committed.

Inspection of **all 328 + 293** features:
- **282 shared NUTS-2 region IDs**, **46 seen only in 2021**, **11 only in 2024**. The changes also reflect territorial coverage (UK codes occur only in the older set); they do **not** imply 46 physical border changes.
- Germany has **38 NUTS-2 codes** and France **22 codes** in each data vintage. Stable codes/counts do not prove polygon-boundary equivalence.
- The area attribute **ar** is null for one point in 2021 (NO0B) and three points in 2024 (BA01, BA02, BA03). Null means **unknown**, not zero or an invented allocation weight. The points represent **map labels**, not full regions or spatial centroids; differences between point positions are not proof of region-boundary migration.

New tested offline auditor: research_runners/nuts2_point_vintage_audit_v0.py. It validates the precise 2021/2024 source shape and country-prefixed region codes, rejects malformed points/duplicate IDs, permits explicitly missing area without replacing it, and produces a provenance-SHA256 code-drift summary. CLI accepts local original source files only when their **independently reviewed SHA256 hashes** match flags. No network access or source data bytes needed inside repository.

Offline commands after source-specific licensing / source-byte acquisition:

    python research_runners/nuts2_point_vintage_audit_v0.py /local/2021.json /local/2024.json --expect-baseline-sha256 APPROVED_2021_SHA256 --expect-successor-sha256 APPROVED_2024_SHA256
    PYTHONPATH=research_runners python -m unittest discover -s tests -p test_nuts2_point_vintage_audit_v0.py -v

**Execution status:** 14/14 local standard-library unit tests passed using synthetic records, and the committed Python/test Git content blob IDs were checked against executed local files. The two *complete real Eurostat* source JSON files were independently inspected through GitHub connector code, but the **Python script was not run on those complete real source files** in the offline local environment. This separation is intentional and auditable.

**Next physical CAT join requires** GISCO **NUTS2 polygons**, verified region vintage, coordinate systems, defensible footprint–polygon intersection/area/insured-value weighting and matching coverage/event time. NUTS-2 label points or one region's maximum gust alone do not generate market losses or insurer portfolios; EIOPA coverage remains a 2020 sample, not the whole market.
