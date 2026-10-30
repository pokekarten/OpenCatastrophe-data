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


### Real NUTS-2 polygon comparison, not just label-point metadata

The matching **actual region-polygon** GeoJSONs (Eurostat/Nuts2json; projection CRS84/EPSG:4326; intended generalization scale **1:20M**) were also read from their *complete* GitHub source documents on 2026-10-30:

- **2021 polygons:** [pub/v2/2021/4326/20M/nutsrg_2.json](https://github.com/eurostat/Nuts2json/blob/master/pub/v2/2021/4326/20M/nutsrg_2.json), **328 polygon features**, Git content blob **a0726c3eca5b6f4326dcbc42f0fff98d5789f0ce**.
- **2024 polygons:** [pub/v2/2024/4326/20M/nutsrg_2.json](https://github.com/eurostat/Nuts2json/blob/master/pub/v2/2024/4326/20M/nutsrg_2.json), **293 polygon features**, Git content blob **a16d0bb84852a9b0607138f8820a838ab5c9e735**.
- **Shared IDs 282; all 282** shared IDs have nonidentical serialized **polygon geometry coordinate arrays** between 2021 and 2024; specifically **38/38** Germany IDs and **22/22** France IDs. This is a check for byte/coordinate inequality of the 1:20M generalized polygons, **not a geometric overlap or land-boundary change analysis**. Different coordinate values can result from source processing, rounding or generalized geometry at the same display scale and are not evidence of actual administrative border change. No geometric union, area intersection or loss overlap was calculated.

Scientific decision: even when the NUTS2 region code is stable, **2021 and 2024 polygon source geometries cannot be silently substituted** in the insured CAT spatial overlay. The exact matched vintage, reproducible polygon asset and geometry-operation contract must precede all area/exposure allocation. In particular, using the geographic **label points** as building locations would be scientifically invalid.


## Implemented optional geometry stage: EPSG:3035 wind-footprint / NUTS2 polygon intersection

Research module: research_runners/regional_wind_footprint_overlay_v0.py.
Tests: tests/test_regional_wind_footprint_overlay_v0.py.

This is the first **spatial intersection implementation**, rather than a list of expected data joins. It requires the already-pinned optional Python geometry profile in requirements-eu-flood-spatial.txt (Shapely 2.1.2; PyProj 3.7.2). The module imports Shapely only when invoked; its tests explicitly skip when Shapely is absent from the core environment. No new dependency was added.

**Contract and correctness boundaries:**

- Regions are an explicitly source-hashed, prepared NUTS2 region list with Polygon or MultiPolygon geometries. Storm data are explicitly source-hashed **individual preprocessed** event grid cells containing maximum 10-m gust in m/s. The event is an extratropical windstorm, not arbitrary convective-storm or hail loss. **Both layers must have been independently converted to EPSG:3035 metres**. CRS transformation and NetCDF ingestion are not implemented by this module; input CRS declaration alone cannot prove the underlying geometries were converted correctly.
- Strictly rejects geographic label points, unreviewed NUTS vintage (only 2021 or 2024 input currently), invalid/self-intersecting polygons, missing event date, invalid wind gusts, duplicate cell/region keys and event cells that overlap within a region (which would double-count weighted coverage).
- Uses spatial index and actual Shapely polygon intersections, respecting MultiPolygon parts and polygon holes. Summarises **area-weighted weather gust on the *covered* part only**, peak gust over intersecting cells, region area, actually covered area and coverage fraction. Uncovered region has **unknown weather**, never wind speed zero. Coverage by storm-footprint grid is not equivalent to insurance attachment or risk assets; the grid cell maximum is not a footprint-wide observed maximum loss speed.
- The output is **weather-only, no exposure, no policy data, no claims**. Do not use the area-weighted average gust as an insured-value-weighted gust; locations/assets would need their own density profile.
- The two input files are accepted only after exact **caller-approved input-file SHA256 checks**, and each input declares the independently sourced raw-data SHA256. Declared raw source hash must be checked against acquired raw assets outside the module; a well-formed string is not independent provenance verification.

With independently prepared local rights-cleared geo inputs, invoke:

    python research_runners/regional_wind_footprint_overlay_v0.py /local/regions-epsg3035.json /local/event-grid-epsg3035.json --regions-input-sha256 EXPECTED_LOCAL_REGIONS_SHA256 --footprint-input-sha256 EXPECTED_LOCAL_FOOTPRINT_SHA256

### Checks executed

The three newly scoped suites run **together under repository-root import semantics**, without PYTHONPATH modifications:

    python -m unittest discover -s tests -p 'test*.py' -v

On a locally reconstructed subset consisting only of these three Python source/test pairs, **45/45 tests PASS** (15 NUTS2 observation pair tests + 14 NUTS source-vintage tests + 16 geometry intersection tests). Earlier two test files were also fixed to import their target source from the repository-root research_runners namespace. The repository-wide check_all.py still requires an actual full checkout / license/project tests and **was not run**.

For the new geometry module and tests, the exact GitHub blobs were read back and independently compared against the SHA of locally executed content: module 9d480655d5ad6f65bcec10a0cc6090e28554db7d; tests 00284add2a09c565bb4f01bdcfd64a9b27f33a6d, both matching. All new fixtures are deliberately synthetic with source ID SYNTHETIC-NOT-C3S.

**Not yet integrated with real event grids**: Real GISCO or Nuts2json Polygon / MultiPolygon geometries were examined from the official Eurostat repository via the connected reader, but the full original files could not be locally downloaded in the sandbox. Likewise C3S event-specific NetCDF and EIOPA insurance workbooks are not yet locally available / approved. No real event raster-cell intersections, no EIOPA exposure join and no insurer CAT Monte Carlo are claimed.

The next technical adapters should be: (1) exact-source GISCO/Nuts2json EPSG3035 Polygon input normalization and pinned geographic-licence review; (2) exact-source C3S NetCDF cell bounds and CRS transformation with 72-hour-window/event/track provenance; (3) a new bridge that conveys coverage fractions and no-data into the sample insured-exposure join rather than silently treating partially covered areas as fully exposed; (4) a separate vulnerability and deductible/coverage loss stage for NextGen.


### First locally executed mixed real/synthetic geometry pilot: Oberbayern (DE21)

A single **real region polygon** was read from the complete official eurostat/Nuts2json 2021 EPSG:3035 1:20M GeoJSON source through the connected GitHub reader and copied *locally only* into an inspection fixture. Exact original Git blob: 9cbb7e97afc48965b0bd6a05d0121eb1f41987a1, path pub/v2/2021/3035/20M/nutsrg_2.json, NUTS2 **DE21** (Oberbayern). In the provider's 2021 dataset, the source has **327** regions in this specific EPSG3035 generalized representation. No real source geometry data bytes are committed to this repository.

The region was intersected by Shapely using the new committed algorithm with **two synthetic 10-m wind-gust grid rectangles** (20 m/s western cell, 40 m/s eastern cell). The rectangles cover the region completely by construction. Executed local result: **17,457.126642 km2** physical region and covered area, **coverage 1.0**, regional peak cell gust **40 m/s**, covered-area-weighted gust **28.866698 m/s**. The geographic area matches an independent sum-of-cross-products (shoelace) of the actual official EPSG3035 DE21 polygon coordinates (17,457.1266425 km2). The regional wind speed is **not** an observed or C3S-derived storm measurement, and is **not** exposure-weighted.

For this first manual local pilot, the original Git blob is a source pointer but the local extracted polygon's raw-source SHA256 field was filled with an explicit placeholder; **full source-byte hash and transformation lineage have not been independently frozen**. No source bytes, extracted polygon fixture or fake wind data were checked into Git. Do not promote this test to a real CAT event validation or claim source SHA256 clearance on its basis.


## Eurostat dual-projection source adapter, implemented 2026-10-30

The new executable research_runners/eurostat_nuts2_3035_adapter_v0.py now prepares the **exact five-field polygon input accepted by** regional_wind_footprint_overlay_v0.py. It never downloads files, computes insurance claims, guesses missing region geometry, or substitutes label points for polygons.

**Two real and separate official file identities** are required for the *same NUTS vintage* (2021 or 2024), at Eurostat's simplified 1:20M map scale:
- Projected polygon source in metres: https://raw.githubusercontent.com/eurostat/Nuts2json/master/pub/v2/2021/3035/20M/nutsrg_2.json (change 2021 to 2024 for that vintage)
- Independent reference-code source: https://raw.githubusercontent.com/eurostat/Nuts2json/master/pub/v2/2021/4326/20M/nutsrg_2.json (change 2021 to 2024)
- Official publisher https://github.com/eurostat/Nuts2json; its project contains a EUPL-1.2 licence file. Separately inspect GISCO underlying geographical data terms at https://gisco-services.ec.europa.eu/distribution/v2/nuts/ before acquisition, processing or any derived-data publication. No third-party source bytes have been committed.

**Full source-file region-code audit, run using the connected GitHub reader**:

| NUTS year | Projected polygons 3035 | Reference polygons 4326 | Germany region IDs | France region IDs | Other projection coverage gaps |
| --- | ---: | ---: | --- | --- | --- |
| 2021 | 327 | 328 | 38/38 identical | 22/22 identical | PT20, PT30 missing in projected; ES70 extra in projected |
| 2024 | 292 | 293 | 38/38 identical | 22/22 identical | PT20, PT30 missing in projected; ES70 extra in projected |

Real source Git blob SHA identifiers: projected 2021 9cbb7e97afc48965b0bd6a05d0121eb1f41987a1, geographic 2021 a0726c3eca5b6f4326dcbc42f0fff98d5789f0ce, projected 2024 5ea9c1ab73dd03addb83a568aa4b089c6d2f1f30, geographic 2024 a16d0bb84852a9b0607138f8820a838ab5c9e735. **Git blob SHA1 is not SHA256.** The caller must verify and pin an independently approved **full raw file SHA256**, and should freeze an immutable source commit rather than relying on mutable GitHub master branch.

The converter refuses invalid/duplicate country or region identifiers, unsupported NUTS year, nonpolygon or malformed geometry, obviously unprojected degree coordinates, and any missing/extra region within the **explicitly selected countries** when comparing both source projections. This means DE/FR can be prepared without claiming complete PT/ES coverage. It produces a separate local provenance receipt with the two SHA256 hashes and a selected-code list. The source files themselves omit a self-authenticating CRS property: projected coordinates are accepted only in combination with the separately verified source path and the pinned raw bytes. A source URL in the receipt does not itself prove that a user's downloaded file came from that URL.

Example run with independently reviewed, local, licensed source files:

    python -m research_runners.eurostat_nuts2_3035_adapter_v0 \
      /local/2021/3035/20M/nutsrg_2.json \
      /local/2021/4326/20M/nutsrg_2.json \
      --vintage 2021 --country DE --country FR \
      --expected-3035-sha256 APPROVED_RAW_3035_SHA256 \
      --expected-4326-sha256 APPROVED_RAW_4326_SHA256 \
      --out /local/private/de-fr-regions.json \
      --receipt /local/private/de-fr-receipt.json

Only the output from this code has the geometry schema needed for the existing physical C3S storm-overlay stage; local, rights-cleared footprint cells must be supplied separately. The 20M polygon data are simplified map geometries, **not cadastral precision** or insured site polygons. The converter and its local weather-overlay validation do **not** claim real C3S event ingestion, EIOPA XLSX ingestion, insured-loss calibration or treaty/retro simulation.

**Actual local tests:** 63 tests PASS via normal repository-root unittest discovery on a reconstructed test subset. This includes 16 new strict adapter tests, two additional subprocess tests which prove correct source-SHA256 pinning and fail-without-writing if checksums disagree, and the previously existing 45 scoped tests. GitHub committed Python and test code content was fetched and independently checked against the local executed files' Git blob SHAs. The complete OpenCatastrophe-data repository check_all.py and its entire validation suite have **not** been executed.

### Separate annual-C3S NUTS2 route without full NetCDF storm grids

C3S's official Enhanced Windstorm Product User Guide confirms **annual NUTS-0/1/2 CSV storm indicators**, including yearly storm count, mean gust, SSI and NSSI by wind threshold:
https://confluence.ecmwf.int/spaces/CKB/pages/462911116/Windstorm+tracks+and+footprints+derived+from+reanalysis+over+Europe+between+1940+to+present+Product+User+Guide

Official data catalogue and CC-BY citation DOI 10.24381/bf1f06a9:
https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-reanalysis?tab=overview

This provides a faster **regional validation** track once the *actual CSV and its NUTS vintage* are inspected. An annual storm index **is not** an event footprint or insured loss and must never be passed as a per-event storm to the spatial overlay or used to reconstruct annual treaty event sequences. C3S CSV/NetCDF and EIOPA XLSX source bytes have not yet been ingested.

**Next required sources:** pin GISCO polygon and C3S event NetCDF exact bytes, project real weather grid boundaries to EPSG3035 with actual event/time/track metadata, spatially overlay with projected region polygons, acquire/rights-review EIOPA insured sample exposure, preserve NUTS and as-of temporal constraints, then apply a separate event vulnerability + insurance terms + joint Monte Carlo/treaty/retro pipeline.
