<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Germany wind loss calibration – external observations and reuse rights

**Research reviewed on 2026-11-06. NO actual R+V insurer claim data or
new numerical wind vulnerability calibration admitted.**

We now have a six-source rights-and-scientific-kind register at
[research/observations/rva_germany_wind_loss_calibration_source_register_v0.toml](../../research/observations/rva_germany_wind_loss_calibration_source_register_v0.toml).
The corresponding fail-closed Python source-classification gate is
in research_runners/rva_germany_wind_loss_calibration_source_gate_v0.py
with eight independent regression/negative test cases in
tests/test_rva_germany_wind_loss_calibration_source_gate_v0.py.

## Highest-value observational sources

**EIOPA Catastrophe Data Hub (priority 1, regulator, observed but
nonexhaustive):**
https://www.eiopa.europa.eu/tools-and-data/catastrophe-data-hub_en

The Hub explicitly includes insured flood and windstorm building
exposure and insurance-entity-reported incurred building losses.
EIOPA identifies **35 large European insurance groups and 9 solo
undertakings** in an ad-hoc collection conducted in 2021, published
in 2023. The source explicitly warns it is **not 100% of the market**.
The regulator hosts original historical-loss and wind-exposure XLSX
attachments. The relevant workbooks have **NOT** been acquired,
checksummed, verified for product-specific reuse, modelled as a
complete denominator, joined to source NRW building locations, or
fed into our model. A public regulator aggregate does not identify
insured individual R+V buildings or company-specific losses.

**GDV Naturgefahrenreport 2026 (priority 2; aggregate actual reported
insurer losses, but limited data rights):**
https://www.gdv.de/gdv/statistik/datenservice-zum-naturgefahrenreport

The 2026-10-09 data service provides state-level residential
storm/**hail combined** claims, long time series and selected
county/event maps. These are valuable independent reference
signals, but they are not the source Daria 1990 wind-only
claims-to-current-site data needed to calibrate our model.

**Crucial rights limit:** the official
[GDV statistical usage terms](https://www.gdv.de/gdv/statistik/nutzungsbedingungen-fuer-statistikdaten-und-deren-visualisierung-188704)
sections 2.1–2.3 allow bounded own use with conspicuous GDV credit,
require disclosing one's own changes to its published statistics,
restrict commercial resale of statistics and **reserve text/data
mining without express GDV consent**. Individual PDF usage terms may
supersede these general terms. We therefore have **not** scraped,
automated extraction from, or trained on these GDV datasets.

**HANZE windstorm 1950–2020 (priority 3; storm/event outcomes but
mixed economic-loss scope and missing displayed licence):**
https://zenodo.org/records/15266959 (DOI 10.5281/zenodo.15266959)

This 2025-04-23 v1 release, produced for the EC JRC by researchers,
collates 1950–2020 European storm reports, dates/areas, economic loss,
injuries, forest and infrastructure impacts. Those are **not
insured-only claims or actual household policy sums**. The Zenodo
record displays a 292.1 kB XLSX with external MD5
0a523543adf76003916186623812ab74 but its visible **License**
field is blank. We do not infer CC BY or raw-row republication rights.
The MD5 is a publisher display, not our downloaded full SHA-256.
No external workbook bytes or event rows were ingested.

## Context and pseudo-observation safeguards

**Copernicus C3S ERA5 1979–2020 Tier 3 wind impact:**
https://confluence.ecmwf.int/spaces/CKB/pages/253724006/Loss%2Bindicators%2BTier%2B3%2BProduct%2BUser%2BGuide

The published loss indicators are **model outputs**, generated using
meteorology, OSM-derived building/exposure and public fragility curves.
They are not independent insurer loss observations. The official
guide explicitly warns of **ODbL** obligations from OSM-derived
inputs and identifies the product as historical static NUTS3 and
building-level windstorm simulations. The legacy CDS product is
now marked unsupported/retired:
https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-indicators?tab=overview
Do not use it as observed truth or import ODbL data directly into
Apache-2.0 code/data without a license study.

**EEA 1980–2023 climate loss estimates:**
https://sdi.eea.europa.eu/catalogue/srv/api/records/7bab0fee-9353-45ff-b2b5-35a2973b07d9

Economic/insured losses are aggregates partly derived from
RiskLayer CATDAT source material received **under institutional
agreements**; no inferred right to download or republish those
raw underlying claims/event datasets.

**Geobasis NRW official 2022 historical building footprints:**
https://www.opengeodata.nrw.de/produkte/geobasis/lk/hist/hist_hu_shp/2022_hu_EPSG4647_Shape.zip

The complete official 901,092,946-byte archive SHA-256
10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da
was independently verified in the
[artifact-free full-source workflow](../../.github/workflows/rva-nrw-hu22-daria-fresh-independent-replay.yml).
It comprises 11,232,755 original physical candidate objects.
Our research sample is 10,000 official geosites over 53 NRW Kreise,
and EUR 4,826,029,500 fictional 2025-like building value.
It is NOT an insured-claim dataset, gives no roof-specific
vulnerability and is not actual R+V exposure.
Exact product/year-specific reuse rights and attribution for any
persistent publication of site-level derivatives still require
verification; unrelated generic NRW or BKG HU-DE licence pages are
not legally identical to the historical 2022 HU file metadata.

## Non-negotiable model calibration gates

1. Verify actual source-specific reuse and TDM permission; record
   the original dataset SHA-256, origin, vintage and provenance.
2. Separate **measured wind** from combined wind/hail and inspect
   gust units, averaging/height, event identity and duration,
   claims vs total economic loss vs insurer net loss.
3. Reconcile the **insured policy or insured-value denominator** and
   carrier sample coverage. EIOPA is a nonrepresentative
   European insurer sample, not a national or R+V property inventory.
4. Split event years (including observed no-loss years), storms and
   regions into independent train/test partitions; never fit on
   C3S-derived model outputs and call them observed validation.
5. Independently validate German roof/construction/age mix,
   repair-price vintage, policy coverage, insured GUL/IL and
   outward RI contract chronology. Annual gross/net OEP/AEP requires
   an independently modelled full event frequency catalogue,
   not the three same-event wind variants of XWS Daria 1990.

Supporting published methodological research:
[Cusack (2023), European storm losses and validation](https://doi.org/10.5194/nhess-23-2841-2023);
[Koks & Haer (2020), transparent European building wind damage](https://doi.org/10.1038/s41598-020-63580-w).

**Decision:** GO for catalogued external reference research and
previously completed original-source numerical method parity;
NO-GO for external-data copying, GDV text/data mining,
German/R+V claims calibration or annual gross/net OEP/AEP.

## Original EIOPA 2023 technical note: exact event identity and original attachments

Original dated publisher references:
- [EIOPA Catastrophe Data Hub official publication](https://www.eiopa.europa.eu/tools-and-data/catastrophe-data-hub_en), 5 December 2023.
- [EIOPA-BoS-22/505 original 14-page technical note](https://www.eiopa.europa.eu/system/files/2023-12/Technical%20description%20-%20Catastrophe%20Data%20Hub.pdf), 27 November 2023, particularly pages 3, 6, 8–11.
- [Historical loss data — exact EIOPA publisher XLSX link](https://www.eiopa.europa.eu/document/download/50e6b095-174c-4d9c-b9dd-1376dc1d43eb_en?filename=Historical+loss+data.xlsx), publisher listing **27.55 KB**.
- [Flood and Windstorm exposure data — exact EIOPA publisher XLSX link](https://www.eiopa.europa.eu/document/download/d2be6f79-3e44-47f1-821f-97ff41e9d7b6_en?filename=Flood+and+Windstorm_exposure_data.xlsx), publisher listing **5.33 MB**.
- [EIOPA-specific legal notice](https://www.eiopa.europa.eu/legal-notice_en): general website-source reproduction with EIOPA credit; additional explicit attribution/nonendorsement disclaimers for transformed publication; original third-party rights are not overridden, and EIOPA-branded tooling may have special licence conditions.

The original EIOPA technical note resolves a major **NO-GO for direct
Daria calibration**:

1. **Only one observed insured wind-event set is provided: the
   extratropical windstorm *Ciara / Sabine / Elsa* of early February
   **2020**.** The other two claim events are the Portugal wildfire in
   June 2017 and the June 2013 Central European flood. **There are no
   1990 Daria insured claim-event observations in this released EIOPA
   dataset.** Our physical XWS Daria 1990 source and this EIOPA
   Ciara 2020 loss sample must **not** be event-matched or directly
   numerically fitted.
2. Insured **windstorm/flood building sums insured** use the
   **year-end 2020** exposure vintage, originally received at
   CRESTA-low resolution / NUTS3 and subsequently **published at
   NUTS2** for anonymous public use. The publication's
   description of sum insured specifies netting of reinsurance
   business and coinsurance. This cannot be assumed equivalent to
   our hypothetical per-asset EUR4.826bn *gross* building
   replacement TIV or a particular policy GUL/IL/RI basis.
3. Only **35 European insurance groups and 9 solo undertakings**
   contributed. EIOPA reports **about 59% EEA-wide** (table:
   **58.3%**) and **63.6% Germany** **2020 direct-business
   fire/property gross-written-premium** sample representation.
   This coverage fraction is **not** a physical building count,
   contractual sums-insured market share, annual expected loss,
   R&V market share or per-location insurer probability.
4. Each public loss data point comprises **at least three
   submitting insurance entities** for anonymity; some
   residential/commercial splits are withheld and shown as
   **RES+COM** instead. Inferring a particular R&V insured building,
   individual company loss, postcode or NRW Kreis claim from
   these aggregates is not scientifically or ethically supported.
5. The public EIOPA site lists both original XLSX attachments,
   but direct workbook access **did not succeed** during this
   research (web extraction unsupported and the direct historical
   loss XLSX transfer failed). Therefore **no original XLSX
   workbook was downloaded, parsed, hash-authenticated or stored
   in this repository**; no workbook sheet names, data columns,
   original byte SHA-256, row-level event loss amounts or further
   EIOPA-specific redistribution permissions are asserted.

Reproducible metadata-only original-source receipt:
`research/observations/eiopa_catastrophe_hub_2023_original_dossier_v0.toml`.
Its checks:
`research_runners/eiopa_catastrophe_hub_2023_original_dossier_gate_v0.py`
and `tests/test_eiopa_catastrophe_hub_2023_original_dossier_gate_v0.py`.
They are **offline and source-bound**, prevent erroneous
Ciara→Daria mapping and false insurer exposure or licence
claims, and do not fetch or cache third-party XLSX bytes.

**Next eligible scientific model case:** first source an
independent, rights-cleared *Ciara-2020* wind-footprint definition
with matching wind metric and 2020 population/repair-cost
denominators. Only then review whether EIOPA's NUTS2
residential/commercial observed-loss aggregates can support a
**regional holdout or plausibility bound**, not a building-level
R&V claim-function fit. The actual Daria-1990 research
remains a separate original-source technical demonstrator.
