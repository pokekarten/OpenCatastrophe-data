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
