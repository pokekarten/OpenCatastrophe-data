<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Netherlands 3DBAG static release lock and fictional volumetric rebuilding-value sensitivity

**Research date:** 2026-11-05  
**Status:** No original per-building 3DBAG/PDOK data, no addresses, no real property or policy prices are ingested by the new tools. The valuation fixture is entirely invented. None of these results is an insured sum, CAT exposure, R+V portfolio or model-approval receipt.

## 1. Versioned, original-provider 3DBAG metadata

Original public [3DBAG downloads](https://3dbag.nl/download) offer the static **v2025.09.03** dataset. We fetched the actual [release-specific metadata.json](https://data.3dbag.nl/v20250903/metadata.json) on 2026-11-05 and verified:

| Release attribute | Original source value |
| --- | --- |
| Identification | `3DBAG`, `identificationInfo.citation.edition=v2025.09.03` |
| Source creation date | `2025-09-03` |
| Original citation identifier | `8ebe360c-88f5-11f0-9f7f-81a0b9c40fe3` |
| Model reference system | `EPSG:7415` (RD New + NAP) |
| Rights metadata | CC BY 4.0 attribution to TU Delft and 3DGI |
| Lineage completeness | Five source entries and five processing steps documented |
| Official all-Netherlands dump SHA-256 | `421265c55361ea7593074bf37d0195d7406efe77fd75290cb44403d7c7bd5d29` (19 GB compressed GPKG ZIP, **not downloaded**) |

The [3DBAG release notes](https://docs.3dbag.nl/en/overview/release_notes/) describe release limitations, missing models and topology risks. The static release's published source lineage is material for deciding which BAG/AHN vintage a specific model represents. The experimental `https://api.3dbag.nl/collections/pand/items/NL.IMBAG.Pand.<id>` response's `metadata.version=2.0` identifies **CityJSON serialization, not a static 3DBAG release**. The prior five-building pilot therefore remains **live-unpinned** despite correct IDs and geometry-quality flags. The 2026.02.21 string in an upstream developer test fixture does NOT prove a publicly published or accessible national model release.

**New source gate:** `scripts/audit_3dbag_static_release_provenance_v0.py` reads *only* an independently obtained local original static metadata file. It enforces citation edition, date, ID, original CC BY 4.0 source attribution, CRS, nonempty source/processing lineage and returns source-metadata SHA-256. Optional **static CityJSON tile header** can be verified against the exact edition and documented metadata URL. It does **not** accept live API `CityJSON 2.0` as release proof, and never sets `source_admitted`/`model_input_approved` true. Synthetic-only regression tests live in `tests/test_audit_3dbag_static_release_provenance_v0.py`.

```sh
python -m unittest tests.test_audit_3dbag_static_release_provenance_v0 -v
python scripts/audit_3dbag_static_release_provenance_v0.py --release-metadata /private/3dbag/v20250903/metadata.json
```

## 2. Fictional 3D volume × rebuilding-cost scenarios (no real insurer value)

**Separate math-only experiment:** `research_runners/nl_fictional_volume_to_rebuild_sensitivity_v0.py` with a checked-in *wholly invented* source-free fixture `research/scenarios/nl_fictional_volume_rebuild_math_v0.toml` and synthetic test `tests/test_nl_fictional_volume_to_rebuild_sensitivity_v0.py`.

One illustrated fictional scenario deliberately assumes **five imaginary standard residential buildings**, each with non-provider model-like volumes: LoD1.2 110m³, LoD1.3 100m³, LoD2.2 90m³. Fictional residential reconstruction unit rates: **€100/m³ to €200/m³** (deliberately arbitrary, **not CBS, AnsvarIdéa, Verbond or actual observed Dutch rates**). Hypothetical index 100 → 110 is likewise **not** an observed CBS value. It exists only to test the ratio mechanics and accidental double escalation:

| Purely fictional result | Amount |
| --- | ---: |
| LoD sensitivity minimum (min LoD volume × fictional €100/m³ × 1.10) | **€49,500.00** |
| LoD1.3 midpoint × midpoint fictional cost rate × 1.10 | **€82,500.00** |
| LoD sensitivity maximum (max LoD volume × fictional €200/m³ × 1.10) | **€121,000.00** |

Formula for building j: `low_j=min(volume_j[lod12,lod13,lod22]) × assumed_rate_low × (fictional_index_target / fictional_index_base)` and analogously for the high bound. Per-building LoD alternatives must **NEVER be added as if independent buildings**. Output is aggregate scenario money only and explicitly **not** an actuarial credible interval, audited construction value, insurance building TIV or observed provider data.

The cost component is kept separate from geometry because **BAG usable unit area m², 3DBAG derived building envelope m³, insured building reinstatement costs, business-interruption sums and land/property market prices are different metrics**. The range of three model detail levels is an input-definition sensitivity, **not stochastic confidence uncertainty**. Commercial use/reproduction of the private Dutch insurer rebuilding-value PDF remains unapproved; rates from it were not copied.

**Hard guards:** accepted input must declare `invented_fixture_only`, `real_provider_rows=0`, `real_insurer_identity=false`, `model_input_approved=false` and only fictional residential typology. No real source IDs, coordinates or insurer identity. Cost-rate/index period and already-indexed flags prevent applying an inflation ratio twice to a 2026-priced method; two correlated CBS input/output indices are never multiplied together. Missing independent rates means **no real valuation**, irrespective of how precise the 3D geometry is.

```sh
python -m unittest tests.test_nl_fictional_volume_to_rebuild_sensitivity_v0 -v
python research_runners/nl_fictional_volume_to_rebuild_sensitivity_v0.py --fixture research/scenarios/nl_fictional_volume_rebuild_math_v0.toml
python scripts/check_all.py
```

## 3. Blockers before building a real carrier synthetic exposure

1. Fix 3DBAG **source release** on actual static tile-level bytes and record per-tile hash, provider BAG/AHN input vintages and attribution. Verify 3DBAG building coverage/quality in several stratified urban/rural/industrial regions rather than one tiny selected window.
2. Reconcile **complete** BAG `verblijfsobject.pand[]` relations via a privacy-reviewed URI/UUID ↔ BAG-ID crosswalk; the WFS singular `pandidentificatie` cannot establish these. Do not publish exact addresses, technical IDs or per-unit crosswalks.
3. Obtain a **rights-cleared**, current €/m³ or €/m² baseline by comparable typology, consistent VAT, debris/demolition, contractor margin, materials, region and year. Preserve monotone uncertainty bands and avoid double CBS escalation.
4. Apply per-building characteristic/occupancy filtering with separate quality/confidence weights, no false building-to-parcel ownership inference, and explicit no-data states. An independently selected building value is a *replacement-cost proxy*, not insured TIV.
5. Separately model insurer-specific location weights, policy counts, coverage limits, deductibles, inflation, hazard/vulnerability and inward/outward RI terms before gross/net OEP/AEP/IP curves. The fictional maths tool does **not** write any OED/Oasis/Neon portfolio data or start a stochastic CAT run.

## 4. NEW original CBS observed price-level benchmark: new-home permit costs by m³

**This is a materially stronger candidate than a dimensionless cost index:** the existing project now also records [official CBS table 83673NED](https://www.cbs.nl/nl-nl/cijfers/detail/83673NED), *Bouwvergunningen; kerncijfers nieuwbouwwoningen; bouwkosten, inhoud, regio*, as fourth non-admitted entry in `landscape/sources-nl-rebuild-cost-priors-20261105.json`. It remains distinct from the actual replacement-value guide and from both CBS *input and output index* time series.

On 2026-11-05, original provider [CBS OData v4 Properties](https://datasets.cbs.nl/odata/v1/CBS/83673NED/Properties) returned `Identifier=83673NED`, `Version=202608200000`, `Modified=2026-08-20T00:00:00+02:00`, CC BY 4.0. Original `/MeasureCodes` identifies `M002974` as average construction cost **EUR/m³**; `/EigendomCodes` maps rental `A028867` and owner-occupied `A028868`; `/RegioSCodes` maps national `NL01` and landsdelen `LD01` North, `LD02` East, `LD03` West, `LD04` South. The original filtered `/Observations` API, `Perioden eq '2026VJ06' and Measure eq 'M002974'`, returned **exactly 10** rows, no continuation link, all with present numeric data:

| Original CBS region | Rental new dwellings €/m³ (`A028867`) | Owner-occupied new dwellings €/m³ (`A028868`) |
| --- | ---: | ---: |
| Netherlands `NL01` | **488** | **438** |
| North `LD01` | 400 | 442 |
| East `LD02` | 446 | 417 |
| West `LD03` | **552** | **481** |
| South `LD04` | 417 | 394 |

**Time basis:** `2026VJ06` = July 2025–June 2026, 12-month rolling, **provisional** at 2026-08-20 release. These are **building-permit budgeted new-home construction costs** for pure residential construction permit projects ≥€50,000 **excluding VAT**. They exclude mixed housing plus commercial/hospitality or other combined projects. The average applies to permitted *new dwelling construction volume*, not a 3DBAG existing building's automatically modelled LoD envelope. The unit price cannot simply be multiplied by observed 3DBAG m³ to produce replacement value or a legal insurance TIV: construction type, gross/usable area, permission vs actual cost, price level, land, demolition, debris, architectural typology, demand inflation, VAT/fees, insurer terms and company portfolio allocation differ.

**Additional code:** `scripts/audit_cbs_83673_permit_m3_grid_v0.py` + `tests/test_audit_cbs_83673_permit_m3_grid_v0.py`. These enforce immutable original CBS version/date/CC-BY metadata, exact `M002974` EUR/m³ metric and `2026VJ06` period, complete 2-tenure × 5-region observation grid, no suppressed/missing/nonnumeric cells, and explicit **`valid_for_existing_building_rebuild_cost_directly=false`**, `real_insured_tiv_calculated=false`, `source_admitted=false` regardless of successful QA. The outputs are ten aggregate CBS price-level observations only; no property or insurance microdata.

```sh
python -m unittest tests.test_audit_cbs_83673_permit_m3_grid_v0 -v
python scripts/audit_cbs_83673_permit_m3_grid_v0.py \
  --properties /private/cbs/83673NED-20260820-properties.json \
  --observations /private/cbs/83673NED-2026VJ06-M002974.json
```

**Research implication:** We now have (a) version-aware 3D building geometry and volumes, (b) public aggregate NL construction **price levels** by region/tenure, and (c) temporal CBS inflation-index series. The missing *bridge* is a jointly reviewed, independently measured relationship between permitted new-dwelling m³ and 3DBAG geometries of existing building classes, with rights and actual costs. Do NOT present this as empirical insurer reconstruction-cost calibration or model source admission yet.
