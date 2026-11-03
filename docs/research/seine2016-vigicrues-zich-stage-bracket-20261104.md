<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Paris 2016 flood – official retrospective scenario bracket and metadata-only gate

**Research review 2026-11-04.** This is **NOT** an accepted hazard model, original geodata acquisition, observed inundation footprint, source-licence approval or insurance loss calculation. Public report and published scenario *PDF metadata* only; no provider geospatial bytes, PDF contents, property coordinates or policies are committed.

## Direct original-source basis

- The previously merged [2016 Hub'Eau stage review](hubeau-seine-2016-peak-quality-and-lag-20261103.md) verified that official `HIXnJ` at `F700000103` reports **6,098 mm** on **2016-06-03**, a *validated, good-quality, measured* daily maximum of instantaneous gauge height. This is a **relative station-level height, not local ground inundation depth**, even when its unit is metres.
- The original [Vigicrues ZICH 5,660 mm PDF](https://www.vigicrues.gouv.fr/ftp/pdf/ZICH_F700000103_5660.pdf) documents `idZip=6198`, ZIP version **4**, hydraulic `modélisation`, **relative local vertical reference**, source simulations produced **2014** from IGN 2012 LiDAR and the Alphée/Hydratec modelling lineage. The PDF is a cartographic **representation and source metadata**, not the original GIS ZIP.
- The original [Vigicrues ZICH 7,190 mm PDF](https://www.vigicrues.gouv.fr/ftp/pdf/ZICH_F700000103_7190.pdf) independently documents `idZip=6201`, ZIP version **4** and the same type of modelled scenario rather than a post-event observed extent.
- A **government-commissioned 2017 post-event report**, [*Inondations de mai et juin 2016 dans les bassins moyens de la Seine et de la Loire – Retour d'expérience*, CGEDD 010743-01 / IGA 16080-R](https://portail.documentation.developpement-durable.gouv.fr/pub/CGEOUV00243323-inondations-mai-juin-2016-dans-les-bassins-moyens.html), Annex 9, table `1-1 - Connaissance de l'aléa`, synthesizes Hauts-de-Seine prefecture findings. For the actual approximately **6.10 m** event it explicitly reports historical **5.66 m and 6.31 m** scenario references (`R0.6/R0.7`) and approximate **±30 cm cartographic uncertainty**. It reports missing river-affluent effects and several failure modes of the then-existing models. This was an evaluation of *actual 2016 performance*, not a new source licence or a formal probabilistic error distribution.
- The **6,310-mm scenario is at present only corroborated by that historical government report** in this review. The simple guessed URL `https://www.vigicrues.gouv.fr/ftp/pdf/ZICH_F700000103_6310.pdf` was tested by a live public page-content service on 2026-11-04 and did **not** return an existing document. This **does not prove** no such geodata exist under another provider path or in historic VIGINOND; it proves only that *this expected public PDF path could not be confirmed*.

## Executed finite comparison

The [offline-only bracket checker](../../research_runners/vigicrues_stage_bracket_v0.py) was exercised against a manually reviewed, transient metadata input with three evidence categories: published PDF at **5660**, government-report mention at **6310**, published PDF at **7190** millimetres. Output:

| Statement | Result |
| --- | --- |
| Observed daily maximum 2016, Paris-Austerlitz | **6.098 m** |
| Nearest lower currently documented PDF scenario in this bounded cohort | **5.660 m**, gap **0.438 m** below peak |
| Historically used upper scenario in official 2017 retrospective | **6.310 m**, gap **0.212 m** above peak; **not** a currently verified PDF/geodata asset |
| Nearest upper verified *PDF-metadata* scenario among the tested live documents | **7.190 m**, gap **1.092 m** above peak |
| Two documented metadata-PDF levels bracket observed height | **Yes** (5.660, 7.190); this is a **wide bracket**, no interpolation |
| Historic 6.310 m geodata asset available and rights reviewed | **Not established** |
| Rights, original geometry, observed-event extent and insured loss model admission | **All blocked / false** |

The retrospective's **±30 cm** is *not* a deterministic scenario interpolation allowance, a model confidence interval, an insurer flood-depth error bound, nor any universal region-wide uncertainty. Its original wording is a contextual cartographic margin and must remain labelled as such. In particular, no transfer from one *station stage* to a parcel inundation depth follows from these facts.

## Executable evidence and regression contract

The module reads only a local, explicitly supplied **research candidate metadata** JSON array. It performs **zero HTTP requests**, no downloads and no writes to production. Candidate records must state one station, integer level in mm, product `ZIP`/`ZICH`, and one of exactly two evidence types: `official_pdf_metadata` or `historical_report_only`. Official-PDF metadata URLs must have the reviewed Vigicrues hostname and a station/stage/product-specific path. A retrospective scenario can be reported, but **cannot serve as a confirmed currently published PDF**. Duplicates, cross-station identifiers, invalid numerical types, malformed URL identity, extra approval fields and unsupported evidence classes are rejected.

Reproduce with an independently reviewed metadata JSON file (this repo does not commit a data-catalogue fixture) and:

```sh
python -m unittest discover -s tests -p 'test_vigicrues_stage_bracket_v0.py' -v
python research_runners/vigicrues_stage_bracket_v0.py \
  --metadata-json /local/research-only-scenarios.json \
  --station F700000103 --observed-mm 6098 --product ZICH
python scripts/check_all.py
```

The checker **always** returns `depth_interpolation_permitted=false`, `asset_inundation_or_loss_calibration_permitted=false`, `geodata_reuse_rights_established=false`, `full_geodata_bytes_verified=false` and `observed_2016_flood_geometry_validated=false`, including an exact metadata-stage match. The output is a *negative scientific-readiness gate*, never a source licence/admission contract. Historical report references are not treated as downloaded original provider bytes; manually supplied metadata are not cryptographic attestation.

## Independent 2016 flood validation alternatives (discovery, not admission)

A separate source search identified three distinct evidence families, which must **not** be conflated:

1. [**Cerema: 2016 observed flooded-area reconstruction on the Fusain**](https://www.documentation.eauetbiodiversite.fr/fr/notice/cartographies-des-zones-inondees-par-le-fusain-crue-de-mai-et-juin-2016-119425). The 2021 scientific report describes witness accounts, photographs, flood marks and high-water traces used to reconstruct a 2016 waterline and inundation atlas for the **Fusain tributary** in Seine-et-Marne. The public bibliographic record labels the **report** Licence Ouverte Etalab. This may be a more independent historic event *validation methodology*, but it is **not** a contemporaneous Paris-Austerlitz observed GIS flood mask and this review did not establish a downloadable exact vector layer, its original bytes, or rights for a geospatial model asset. Keep its distinct basin/AOI.
2. [**DRIEAT historic highest-known floods (PHEC) GIS**](https://www.drieat.ile-de-france.developpement-durable.gouv.fr/atlas-des-zones-inondees-par-les-plus-hautes-eaux-a244.html). The authority expressly offers historical flood cartography and a downloadable GIS archive, but its examples include the Seine **1910** and Marne **1955** events: it is **not** 2016 observed ground truth merely because it is open or geographically overlaps. It is a separate long-term flood-history/coverage benchmark, subject to exact asset terms, valid vintage and a GIS byte receipt.
3. [**Copernicus EMSN028 2016 observed/estimated mapping**](https://mapping.emergency.copernicus.eu/activations/EMSN028/). The original activation covers **17 areas and 51 products**, including SAR-based observed extent and separate estimated maximum extent/water depth. Our existing [original FileGDB topology audit](cems-emns028-filegdb-topology-audit-20261101.md) already demonstrates an **invalid original flood polygon**, unresolved AOI04 identity and mixed third-party/restricted data. It is a valuable independent scientific lead, not a currently admissible 2016 building flood-depth surface.

**Selection rule:** prefer *same event + same physical mechanism + same area/time + independently verified observed geometry* for independent holdout; treat historical atlases, retrospective/modelled ZIP/ZICH products, tributary-only maps and regulatory PPRI zones as **separately labelled context**. No source or source-rights state was upgraded on the basis of this discovery.

## New primary-source finding: peak-period Paris-Austerlitz instrument outage

The **official HydroPortail station event chronology** for [`F700000103`](https://hydro.eaufrance.fr/stationhydro/F700000103/evenements) records an instrument/telemetry incident **during the 2016 Seine flood crest**, independently of the `obs_elab` data. The authority states that its automatic station feed failed around **2016-06-02 23:00 local reference in the incident text**; from **3 June** observed *stage heights* were entered from observers' staff-gauge readings. A **6 June 2016** notice additionally says velocity-sensor cable damage disrupted **discharge measurement**. The incident listing gives UTC timestamps for the notices; it does **not** independently establish an exact station-recovery timestamp or full outage interval. Do not infer that the daily maxima were simultaneously and continuously measured by an unbroken automatic sensor.

This reconciles two facts that are otherwise easy to misuse: `HIXnJ` stage on **2016-06-03** is labelled `Mesurée` by the published API, while `QmnJ` / `QIXnJ` **discharge** is labelled `Reconstituée` at Paris. A station-stage *measured* code can reflect **manual readings**, not uninterrupted telemetry. A validated/reconstructed discharge is not an independently measured physical river flow at the same moment. The underlying direct sensor sequence and the operator's reconstruction method still require separate original-source evidence.

An additional **actual read-only Neon execution** of [the incident/method cross-check](../../research_runners/sql/hubeau_2016_flood_peak_station_incident_audit_v0.sql) compared the exact five-day **3–7 June 2016** window, *not* a claimed full outage duration:

| Station | 3–7 June rows | Method codes | Qualification codes | Validated | Model input admitted |
| --- | ---: | --- | --- | ---: | ---: |
| `F700000103` (Paris) | 5/5 | **5 reconstructed** | **5 good** | 5 | 0 |
| `F447000302` (Ponthierry) | 5/5 | **5 calculated** | **5 doubtful** | 0 | 0 |

These flags are not subjective estimates: the [official Hub'Eau v2 hydrometry API](https://hubeau.eaufrance.fr/page/api-hydrometrie) labels its recorded `obs_elab` values and provenance methods, and an earlier [complete 94-row live QmnJ source-parity check](source-usability-cohort-20261103.md) matched every stored value/status/method/quality/production timestamp. The incident is a distinct, **new contextual provenance signal** that does not downgrade the authority's own `Bonne` label; it does block **our separate stronger scientific claim** of an uninterrupted, direct 2016 flow measurement at the crest. The original historical incident event response was read as an official public rendered page, **not** independently acquired original bytes with a SHA-256 receipt; the incident metadata are not copied as raw provider bytes.

**Model implication:** no source here can be used as a sensor-exact observed peak discharge, independent flood-depth observation, or verified insurance loss benchmark. Distinguish reliable staff-gauge stage chronology from independently validated discharge, seek the hydrograph's official reconstruction/uncertainty evidence and provider revision history, and only then build a separate hydraulic model and validation holdout. Treat all authority-specific timestamps and references with original timezone/revision metadata rather than assigning a hypothetical continuous outage duration.

## Independent instrument-failure corroboration

An official February 2017 government investigation documents two station problems during the June 2016 flood:

- Paris-Austerlitz: the measurement well stopped tracking the river level, with discrepancies up to 30 cm over about 18 hours. A temporary station was installed on 3 June.
- Saint-Fargeau-Ponthierry: floating debris interfered with a velocity sensor path, causing calculated discharge to be underestimated.

Source: https://igedd.documentation.developpement-durable.gouv.fr/documents/Affaires-0009575/010743-01_rapport.pdf (printed page 131). These findings do not establish per-day corrections, flood depths or source licensing.

An executed read-only audit is available at [SQL](../../research_runners/sql/hubeau_2016_flood_peak_station_incident_audit_v0.sql). During 3–7 June it found five reconstructed, validated Paris daily flows and five calculated, doubtful Ponthierry daily flows. Neither series is model-admitted. The 30 cm station discrepancy is distinct from cartographic uncertainty.

## Open data licence: observational source versus flood geometry

The [official BRGM Hub'Eau FAQ](https://assistance.brgm.fr/fr/aide/HubEau) states that environmental data exposed through the API may be reused under the French interministerial Open Licence. The French [hydrometric station source listing](https://www.data.gouv.fr/datasets/donnees-aux-stations-hydrometriques) specifically publishes **Licence Ouverte v2.0**, with archived station records and accompanying quality-code documentation. This is positive, authoritative service- and dataset-level rights evidence for **hydrometric observations**, distinct from scientific suitability.

The already stored 94 QmnJ observations still carry **zero rights-review/admission flags** in Neon, and no flags were modified here. Before changing the canonical model-input permission, preserve the exact version/date/query, attribution, original-byte receipts and review of any source-specific exceptions. Independent hydraulic and instrument-failure review is necessary even for lawfully reusable observations.

The licence conclusion must **not** be applied to Vigicrues/VIGInond ZIP or ZICH flood GIS, which have separate reuse restrictions and product-specific source lineage. Do not merge these different rights scopes.

## Provider rights and actual next input

The 5.66/7.19 published PDFs explicitly state that re-use of the underlying VIGINOND/ZIP data requires an exchange with the producing/managing authority and understanding the data lineage and terms. The author is **SPC SMYL**. No commercial or broader geospatial permission is inferred from PDF web accessibility. The Paris scenario simulations predate the 2016 flood and do not include all the observed mechanisms (e.g. tributary, groundwater and network flooding); independent historic field/extent references are needed.

**Causal next steps**, without inventing an asset:
1. Request authoritative exact `F700000103_6310` GIS/PDF identity if available, full underlying ZIP/ZICH product and version (including original-file checksum and permitted acquisition/reuse/redistribution scope), and any updated 2D hydraulic model or map.
2. Identify independently verified observed May/June 2016 flooded areas and high-water marks, with correct AOI, geometry/topology and timestamps. Compare model scenarios against them by geography/phenomenon, not merely by gauge height.
3. Before any downstream catastrophe-risk and insurer-capital model use, combine source-licensed flood depth, 2016-vintage building/valuation data and vulnerability/insurance policy terms; split calibration and independent validation to avoid using the same event for both.

**Do not** automatically infer a flood-depth field, a GUL/YLT/ELT or an insurance loss from the PDF maps or the 2017 retrospective.
