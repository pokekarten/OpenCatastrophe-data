<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-oasis-model-input-leads-20261105.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-oasis-model-input-leads-20261105.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-05`  
**Purpose:** Non-admission source-checked second pass of Oasis-relevant native model projects, synthetic storm catalogues, reusable exposure and vulnerability transformation leads, independent loss benchmarks, and licensed vendor discovery, deduplicated against the main OpenCatastrophe-data landscape. Metadata only: no model/data admission, rights grant, asset upload, successful external model execution or insurer-specific EP approval.

**Entries:** 9

## Community LA earthquake Oasis model and reproducible pipeline

**Candidate ID:** `oasis.community.la-earthquake-model.2026`  
**Provider:** Independent community model developer  
**Categories:** `earthquake`, `oasis_model_package`, `source_code`, `hazard`, `vulnerability`, `exposure`  
**Spatial scope:** Los Angeles County, California, USA  
**Temporal scope:** Historical USGS ShakeMap events and modelled earthquake rates; project changed October 2026  
**Resolution / granularity:** Native oasislmf.json; model_data/ includes footprint.csv ~2.35 MB, occurrence_lt.csv ~3.61 MB, vulnerability.csv ~49.17 MB, events_p.csv and returnperiods.csv; scripts fetch ShakeMaps, MS building footprints, derive Hazus 6.1 damage functions and UCERF3 source event rates  
**Potential roles:** `independent_oasis_model_architecture`, `earthquake_model_build_template`, `event_rate_provenance_challenge`, `source_model_validation`  
**Access hint:** `public_repo_no_declared_licence_no_reuse_permission`  
**Authoritative source:** <https://github.com/ekrishgupta/oasis-eq-cat-model>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official GitHub repo and README were accessed 2026-11-05: README blob 23c03b06a17e8c9cfa0cb92d021b26fadec2355a; oasislmf.json blob def63d07b2e146ea69ff9dc739b5877c15603827. README claims a runnable Docker Oasis API pipeline for ~2.42 million synthetic/economic buildings and a small event catalogue. No repository LICENSE or GitHub detected SPDX license was found; this is NOT permission to copy source code or model assets. Upstream USGS, FEMA Hazus, Microsoft building footprint and US Census sources each require version-specific rights review and provenance. No independent numerical scientific validation or local native run performed; claimed return periods are not accepted calibration evidence; keep examples read-only and do not deploy.

## C3S WISC synthetic European windstorms (22,980 footprints)

**Candidate ID:** `copernicus.c3s.wisc.synthetic-windstorms.22980`  
**Provider:** ECMWF Copernicus Climate Change Service / UK Met Office  
**Categories:** `windstorm`, `stochastic_candidate`, `event_footprints`, `netcdf`, `oasis_hazard`  
**Spatial scope:** Pan-Europe, 25W to 40.5E and 34.4N to 71.5N  
**Temporal scope:** Met Office HadGEM3 climate simulation analogue 1986-2011, September-May; product 2022-02-15, last metadata update 2025-01-31  
**Resolution / granularity:** 22,980 synthetic footprints over 3 alternative downscaling/recalibration methods; 5 independently initialized ensembles; 25km data interpolated to ~4.4km; maximum 3-second gust at 10m within 72h storm window; NetCDF-4 CF 1.6; DOI 10.24381/cds.ce973f02  
**Potential roles:** `european_windstorm_hazard_library`, `native_oasis_footprint_adapter_candidate`, `stochastic_catalogue_methodology`, `german_portfolio_windstorm_pilot`  
**Access hint:** `provider_page_cc_by_attribution_download_auth_and_catalogue_weights_unverified`  
**Authoritative source:** <https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-synthetic-events?tab=overview>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** CDS catalogue lists CC-BY licence and 22,980 storm footprints, derived from 3 versions of the historical 7,660-event WISC synthetic product. Historical WISC programme explicitly reported an Oasis-compatible 7,660-event set and exposure/vulnerability workflow, but its portal was retired; these are related lineage, NOT independent event populations to add to 22,980. The 3 calibration/downscaling methods and 5 ensemble initial conditions need a complete event/source-year/sample weighting contract; do not interpret 22,980 as 22,980 independent annual frequencies or as a validated 1-in-200-year loss model. Distinguish this new synthetic WISC dataset from the separate already-admitted ERA5 historical C3S EWS reanalysis source; no NetCDF bytes, size, checksum or current authenticated API download verified here.

## GFZ Ahrweiler sanitized building valuation model benchmarks

**Candidate ID:** `gfz.ahrweiler.sanitized-building-exposure.2026`  
**Provider:** GFZ Helmholtz Centre for Geosciences / Aaron Buhrmann  
**Categories:** `exposure`, `reconstruction_cost`, `building_archetypes`, `model_validation`  
**Spatial scope:** Ahrweiler county, Rhineland-Palatinate, Germany  
**Temporal scope:** Three valuation cost bases (2018 Eurostat, 2018 BEAM, 2020 EHRE); sanitized May 2026 Zenodo release  
**Resolution / granularity:** Public sanitized CSV dataset contains LoD1+Eurostat, LoD1+BEAM, EHRE value model outputs and an 844-building independent type/value benchmark (699 EHRE-matched subset). Full precise geographic coordinates are omitted by design; geometry requires separate access approval. Published source describes 24 BKI-derived building types and EUR/m3 valuation method.  
**Potential roles:** `german_synthetic_tiv_priors`, `building_archetype_loss_unit_testing`, `independent_value_model_comparison`, `flood_exposure_validation`  
**Access hint:** `public_zenodo_sanitized_csv_exact_licence_and_upstream_bki_rights_unverified`  
**Authoritative source:** <https://zenodo.org/records/20038906>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The later 2026 Zenodo version contains sanitized CSV files and is distinct from the 2025 record 17350277. Earlier original README identifies 844 benchmark assets (699 EHRE matches) and no coordinate geography to preserve privacy; attributes rely partly on external construction-cost material (BKI), which can carry independent restrictions. The exact updated Zenodo record rights field was not resolved to a machine-verifiable CC licence in this audit; do NOT assume CC-BY or unrestricted commercial use. Preserve vintage and methodology; no actual insurance value, policy, location, flood damage or direct Oasis-ready OED confirmed. No raw rows downloaded or imported.

## CatRiskTools worldwide insurer catastrophe model and Oasis compatibility catalogue

**Candidate ID:** `idf.rmsg.catrisktools.oasis-model-catalogue`  
**Provider:** Insurance Development Forum Risk Modelling Steering Group / RenaissanceRe  
**Categories:** `model_discovery`, `model_licensing`, `catastrophe_model_providers`, `oasis_compatibility`  
**Spatial scope:** Worldwide; filter by country, peril and vendor  
**Temporal scope:** Public catalogue description reviewed 2026-11-05; underlying vendor entries can change  
**Resolution / granularity:** Interactive inventory of off-the-shelf models with primary and secondary perils, model licence/access, whether available on Oasis and financial-module capability. No model binaries, hazard event catalogues or vulnerability data are supplied by the index itself.  
**Potential roles:** `find_oasis_vendor_models`, `find_regional_peril_coverage_gaps`, `commercial_model_acquisition_leads`  
**Access hint:** `public_model_metadata_catalogue_model_records_include_contract_licensed_products`  
**Authoritative source:** <https://idf-rmsg.github.io/CatRiskTools/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official IDF documentation states the index includes BOTH open-licence and commercially licensed model products, with a per-model Oasis availability indicator. The catalogue is a discovery lead and not a licence to obtain, run, copy or redistribute any particular model. A source-specific acceptance and commercial rights review are mandatory. Do not count database entries as successfully installed runnable models.

## Delft-FIAT damage functions and flood vulnerability CSV interface

**Candidate ID:** `deltares.delft-fiat.vulnerability-workflow`  
**Provider:** Deltares  
**Categories:** `flood`, `vulnerability`, `damage_curves`, `software_adapter`  
**Spatial scope:** Any region with consistent flood depth and exposure grids  
**Temporal scope:** Documentation and source read 2026-11-05; software version/method should be pinned per use  
**Resolution / granularity:** MIT Python damage-model library. Its documented vulnerability CSV format uses depth in metres, per-asset damage fractions between 0 and 1 and method metadata, with asset maximum potential damage. Potential to convert a rights-cleared Delft-FIAT curve into Oasis vulnerability bins after unit and damage semantics review.  
**Potential roles:** `flood_vulnerability_interoperability`, `depth_damage_conversion_candidate`, `independent_damage_model_challenger`  
**Access hint:** `mit_software_only_external_vulnerability_curves_license_unverified`  
**Authoritative source:** <https://github.com/Deltares/Delft-FIAT>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Repository README, pyproject.toml and PyPI metadata explicitly specify MIT for SOFTWARE, not for all external vulnerability CSVs or scientific functions. Delft-FIAT is a distinct loss engine and NOT an Oasis model package; its vulnerability format is an adapter research input requiring conversion of metres/depth fractions, taxonomy/coverage, bin discretization and original rights before any Oasis run. Example curves are not necessarily published calibrations for German insurance buildings.

## GEM 2026 national seismic risk profile benchmark outputs

**Candidate ID:** `gem.seismic-risk-profiles.v2026.0.0`  
**Provider:** Global Earthquake Model Foundation  
**Categories:** `earthquake`, `risk_benchmark`, `loss_validation`, `exposure_context`  
**Spatial scope:** 204 countries and territories including Germany  
**Temporal scope:** GEM Global Risk Model version v2026.0.0, released June 2026  
**Resolution / granularity:** Country/territory profiles of hazard, exposure and seismic-loss summary, linking GEM Global Exposure v2026.0.0, Global Vulnerability v2026.0.0 and hazard-map v2026.1. Published profiles are aggregate benchmarks, not an Oasis stochastic source-event catalogue.  
**Potential roles:** `earthquake_pml_aggregate_challenger`, `cross_model_validation_targets`, `country_cat_loss_context`  
**Access hint:** `gem_cc_by_nc_sa_4_0_noncommercial_sharealike_commercial_requires_contract`  
**Authoritative source:** <https://github.com/gem/risk-profiles/tree/v2026.0.0>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official GEM README pins 204 country/territory risk profiles and source versions. CC BY-NC-SA 4.0: non-commercial only with attribution and derivative share-alike; commercial risk/insurance production needs an independent licence. Related GEM Global Exposure Model v2026.0.0 and Global Vulnerability Model v2026.0.0 are ALREADY registered as distinct sources elsewhere in the OpenCatastrophe-data registry; do not import or duplicate their data. No synthetic insurer calibration or Oasis model parity established.

## Oasis model provider catalogue, May 2025 snapshot (mixed licensing)

**Candidate ID:** `oasis.lmf.model-provider-catalogue.may2025`  
**Provider:** Oasis Loss Modelling Framework  
**Categories:** `vendor_model_catalogue`, `commercial_models`, `windstorm`, `hail`, `earthquake`, `flood`  
**Spatial scope:** Worldwide; includes Europe and Germany licensed model listings  
**Temporal scope:** Snapshot labelled May 2025; current 2026 vendor availability requires reconfirmation  
**Resolution / granularity:** Official provider table lists examples: Gallagher Re Europe hail incl. Germany; Guy Carpenter G-CAT Hail incl. Germany; Impact Forecasting Europe Windstorm incl. Germany; Cat Risk Solutions Catrisk-EU earthquake across Europe, and numerous flood/TC/cyber provider models. These are catalogue claims, not public binaries.  
**Potential roles:** `german_hail_oasis_vendor_research`, `commercial_model_licence_contact`, `compare_public_vs_vendor_model_scope`  
**Access hint:** `official_provider_pdf_catalogue_mixed_commercial_vendor_agreements_required`  
**Authoritative source:** <https://oasislmf.org/download_file/force/1718/229>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Direct Oasis official May 2025 model-list PDF; check latest vendor availability, territory, release, price and financial model separately. Most mentioned third-party model packages require contractual permission; no provider event sets, vulnerability curves, binaries, evaluation access or API credentials have been acquired. Explicitly distinguish the full commercial Impact Forecasting Europe Windstorm model from publicly available deterministic Ciaran/Domingos scenario footprints: those are not equivalent. Provider catalogue does not prove that any model is free, open weight, scientifically reproducible or accessible to this account.

## GFZ European High-Resolution Exposure (EHRE) building-level methodology and code

**Candidate ID:** `gfz.ehre.european-high-resolution-exposure.2023`  
**Provider:** GFZ Helmholtz Centre for Geosciences / Nievas et al.  
**Categories:** `exposure`, `building_footprints`, `value_priors`, `methodology`  
**Spatial scope:** 44 European countries using ESRM20 building inventory and OpenBuildingMap footprints  
**Temporal scope:** Published 2023; data and code vintage conditional  
**Resolution / granularity:** Method and GitLab software combine ESRM20 aggregate exposure, OpenStreetMap/OpenBuildingMap footprints and GHSL built-up layers, estimating remainder buildings on around 100m support where OSM is incomplete. Ahrweiler extract described by 2026 research is a separate, privacy-sanitized output.  
**Potential roles:** `building_vs_aggregate_exposure_disaggregation`, `german_synthetic_portfolio_method_research`, `oed_location_construction_candidate`  
**Access hint:** `public_method_and_code_repository_exact_data_release_and_osm_odbl_rights_unreviewed`  
**Authoritative source:** <https://git.gfz-potsdam.de/ehre>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original publisher item and peer-reviewed descriptions establish methodology; source implementation and full fine-grained country exposure access, exact rights and source-vintage reproducibility not independently verified. ESRM20 original exposure v1.0 (CC BY 4.0) is ALREADY registered/admitted only for a bounded existing artefact; that approval does not carry over to EHRE derivatives, OSM ODbL footprints or a full source dataset. No observed insurer sites, real contracts or model-ready OED claimed.

## ElcoK/WISC: European windstorm building loss and risk modelling code

**Candidate ID:** `research.elcok.wisc.european-wind-damage`  
**Provider:** Elco Koks / Vrije Universiteit Amsterdam, Institute for Environmental Studies  
**Categories:** `windstorm`, `building_exposure`, `damage_functions`, `academic_loss_model`, `open_source_software`  
**Spatial scope:** Pan-European national and NUTS-region building exposure methods; real site and hazard inputs external  
**Temporal scope:** Academic model work developed 2018-2020; original WISC source event/footprint vintages separate  
**Resolution / granularity:** Python research code includes scripts/functions.py (region_exposure, region_losses, loss_calculation, load_max_dam, load_curves, source-storm list helpers) and scripts/analyze.py orchestration. Uses geopandas, rasterio, OSM and external model inputs. No original C3S WISC NetCDF footprints or complete damage-curve/financial portfolio assets are provided in this software repository.  
**Potential roles:** `independent_wind_damage_curve_research`, `european_building_exposure_valuation_method_challenger`, `wisc_model_loss_calculation_crosscheck`, `oasis_vulnerability_translation_candidate`  
**Access hint:** `mit_public_research_code_external_wisc_data_and_curves_licences_separate_not_oasis_model`  
**Authoritative source:** <https://github.com/ElcoK/WISC>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Direct GitHub source review 2026-11-05: README states MIT software, repository LICENSE Git blob 638dd62ec2a1b317979f283a533cee683dbdb447; scripts/functions.py blob da6278d5dc61fb05dd89018fa854d77b36f16f2b and scripts/analyze.py blob 79b311c58354bb478088ec547dc53b23c625f483. Reusable code methods are distinct from original data, non-bundled building geographies, external WISC simulated footprints and construction-cost/damage curves, which require independent rights/provenance reviews. It is NOT an OasisLMF native model package; no prebuilt event/hazard/occurrence/OED/RI files, no successful current 2026 runtime, independent calibration, annual OEP/AEP, source weights or insurer losses have been established. Treat as method and potential wind vulnerability adapter only, not a second independent WISC hazard catalogue.
