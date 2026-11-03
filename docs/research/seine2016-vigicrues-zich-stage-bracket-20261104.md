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

## Provider rights and actual next input

The 5.66/7.19 published PDFs explicitly state that re-use of the underlying VIGINOND/ZIP data requires an exchange with the producing/managing authority and understanding the data lineage and terms. The author is **SPC SMYL**. No commercial or broader geospatial permission is inferred from PDF web accessibility. The Paris scenario simulations predate the 2016 flood and do not include all the observed mechanisms (e.g. tributary, groundwater and network flooding); independent historic field/extent references are needed.

**Causal next steps**, without inventing an asset:
1. Request authoritative exact `F700000103_6310` GIS/PDF identity if available, full underlying ZIP/ZICH product and version (including original-file checksum and permitted acquisition/reuse/redistribution scope), and any updated 2D hydraulic model or map.
2. Identify independently verified observed May/June 2016 flooded areas and high-water marks, with correct AOI, geometry/topology and timestamps. Compare model scenarios against them by geography/phenomenon, not merely by gauge height.
3. Before NextGen/FFBK usage, combine source-licensed flood depth, 2016-vintage building/valuation data and vulnerability/insurance policy terms; split calibration and independent validation to avoid using the same event for both.

**Do not** automatically infer a flood-depth field, a GUL/YLT/ELT or an insurance loss from the PDF maps or the 2017 retrospective.
