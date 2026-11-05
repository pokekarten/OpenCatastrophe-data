<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-oasis-public-models-20261105.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-oasis-public-models-20261105.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-05`  
**Purpose:** Non-admission discovery catalogue of public Oasis executable demo models, deterministic scenario/model package families, vulnerability inputs and explicitly licence-gated data leads. Metadata only; never a data or model admission, commercial-use approval, source-byte acquisition, or stochastic-insurance calibration.

**Entries:** 24

## OasisPiWind original demo model

**Candidate ID:** `oasislmf.piwind.original-demo`  
**Provider:** OasisLMF  
**Categories:** `windstorm`, `flood`, `model_demo`  
**Spatial scope:** UK toy geography; fictitious Melton Mowbray setting  
**Temporal scope:** fictional event years; model commit specific  
**Resolution / granularity:** Runnable demo plus model_data, keys_data, OED examples, generated ORD result fixtures  
**Potential roles:** `oasis_engine_regression`, `aal_oep_aep_result_bridge`, `financial_module_validation`  
**Access hint:** `public_github_repository_software_terms_check_separately`  
**Authoritative source:** <https://github.com/OasisLMF/OasisPiWind>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** An independent external benchmark pins OasisPiWind commit 94820c59f169b222d4c1a72256ff0a8f86a9e5bf and reconstructs 1000-year sample AAL/OEP/AEP from published IL SPLT/PALT/PSEPT. PiWind is a fictional demo, not observed UK hazard or a calibrated insurer model. Independent licence review for each embedded asset remains required; do not import source bytes by registry entry.

## UKWind large-scale wind performance model

**Candidate ID:** `oasislmf.oasismodels.ukwind`  
**Provider:** OasisLMF OasisModels  
**Categories:** `windstorm`, `model_demo`, `performance_benchmark`  
**Spatial scope:** United Kingdom  
**Temporal scope:** synthetic 100000-year test set  
**Resolution / granularity:** 10,000 events/100,000 simulated years and advertised 20m-location scaling test; GitHub model_data includes events.bin (40,000 B), occurrence.bin (21,435,572 B), vulnerability.bin (12,716,004 B), damage_bin_dict.bin, returnperiods.bin. External script references footprint.bin.z, footprint.idx.z, location_full.parquet on a public S3 endpoint.  
**Potential roles:** `large_scale_oasis_engine_testing`, `event_period_measure_benchmark`, `synthetic_portfolio_stress`  
**Access hint:** `github_bsd3_software_s3_32byte_range_retrieved_full_asset_rights_unreviewed`  
**Authoritative source:** <https://github.com/OasisLMF/OasisModels/tree/main/UKWind>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Pinned source review: OasisModels/UKWind/get_large_data.sh Git blob 3f8678c873d6eaf7dfb637aadab5597eadf103e7; GitHub file listings were accessible as metadata. A bounded public connector HTTP Range: bytes=0-31 probe on 2026-11-05 retrieved exactly 32 binary bytes each from footprint.bin.z, footprint.idx.z and location_full.parquet (content type binary/octet-stream). This is first-byte public-access evidence ONLY, not proof of complete successful downloads, content lengths, file integrity, stable object versions, SHA-256, reproducible model execution or permission to reuse/redistribute assets; direct Linux DNS and generic web reader did not support the test. Root OasisModels software BSD-3-Clause does NOT authenticate separately hosted S3 licence; no historical hazard or insurer calibration inferred.

## ParisWindstorm example

**Candidate ID:** `oasislmf.oasismodels.paris-windstorm`  
**Provider:** OasisLMF OasisModels  
**Categories:** `windstorm`, `model_demo`  
**Spatial scope:** Paris, France demonstration region  
**Temporal scope:** single-event instructional model  
**Resolution / granularity:** Small example model; separate training example also at https://github.com/OasisLMF/ParisWindstormModel  
**Potential roles:** `european_storm_demo`, `oed_financial_module_test`  
**Access hint:** `public_github_example_bsd3_software_external_data_rights_unreviewed`  
**Authoritative source:** <https://github.com/OasisLMF/OasisModels/tree/main/ParisWindstorm>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Small single-peril example, not a calibrated pan-European event set. Root OasisModels software BSD-3-Clause; inspect local test/model assets and terms individually. Keep distinct from separately published Impact Forecasting EUWS scenario family.

## PiCyber example cyber model

**Candidate ID:** `oasislmf.oasismodels.picyber`  
**Provider:** OasisLMF OasisModels  
**Categories:** `cyber`, `model_demo`  
**Spatial scope:** fictional cyber exposure geography  
**Temporal scope:** illustrative only  
**Resolution / granularity:** Cyber model example uses annual revenue as exposure with vulnerability and area-peril lookup  
**Potential roles:** `cyber_oasis_prototype`, `nonproperty_exposure_adapter`  
**Access hint:** `public_github_example_bsd3_code_data_unreviewed`  
**Authoritative source:** <https://github.com/OasisLMF/OasisModels/tree/main/PiCyber>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Root OasisModels software is BSD-3-Clause; sample exposures and any external input rights not independently reviewed. Not an insured cyber portfolio or validated accumulation model.

## ComplexModelAPI ground-up loss model hook

**Candidate ID:** `oasislmf.oasismodels.complex-model-api`  
**Provider:** OasisLMF OasisModels  
**Categories:** `earthquake`, `software_adapter`, `model_demo`  
**Spatial scope:** example geography unspecified  
**Temporal scope:** demonstration only  
**Resolution / granularity:** Custom earthquake building/content GUL module integrated through Oasis complex model API  
**Potential roles:** `custom_ground_up_loss_integration`, `openquake_oasis_bridge`  
**Access hint:** `public_github_example_bsd3_software_data_unreviewed`  
**Authoritative source:** <https://github.com/OasisLMF/OasisModels/tree/main/ComplexModelAPI>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Technology example demonstrating replacement of standard GUL calculation, not a validated earthquake event catalogue or evidence of complete vendor model readiness.

## Oasis DeterministicModel example

**Candidate ID:** `oasislmf.oasismodels.deterministic`  
**Provider:** OasisLMF OasisModels  
**Categories:** `deterministic_scenario`, `software_adapter`, `model_demo`  
**Spatial scope:** exposure-defined geography  
**Temporal scope:** one nominated event per experiment  
**Resolution / granularity:** Applies predetermined damage factors from OED location file and passes resulting losses to Oasis financial module  
**Potential roles:** `oed_to_financial_module_smoke`, `scenario_loss_benchmark`  
**Access hint:** `public_github_example_bsd3_software_data_unreviewed`  
**Authoritative source:** <https://github.com/OasisLMF/OasisModels/tree/main/DeterministicModel>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Single-event deterministic test cannot by itself identify annual probabilities, AEP/OEP or calibrated risk. OED exposure and sample files require independent rights checks.

## DynamicFootprint example

**Candidate ID:** `oasislmf.oasismodels.dynamic-footprint`  
**Provider:** OasisLMF OasisModels  
**Categories:** `dynamic_footprint`, `model_demo`  
**Spatial scope:** example region not established  
**Temporal scope:** demonstration only  
**Resolution / granularity:** Separate DynamicFootprint folder exists in official OasisModels repository; exact hazard/peril and run completeness not evaluated  
**Potential roles:** `dynamic_hazard_interface_research`  
**Access hint:** `public_github_example_bsd3_software_data_unreviewed`  
**Authoritative source:** <https://github.com/OasisLMF/OasisModels/tree/main/DynamicFootprint>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Directory existence checked; contents, execution prerequisites, event and source rights remain unverified. Do not promote to model-ready.

## PiWind technical variants (multi-repository family)

**Candidate ID:** `oasislmf.oasismodels.piwind-variants`  
**Provider:** OasisLMF OasisModels  
**Categories:** `windstorm`, `flood`, `model_demo`, `software_adapter`  
**Spatial scope:** fictional UK PiWind setting  
**Temporal scope:** synthetic test set; variant specific  
**Resolution / granularity:** Official repository folders: PiWind, PiWindAbsoluteDamage, PiWindAzure, PiWindBI, PiWindComplexModel, PiWindDtype, PiWindPostLossAmplification, PiWindPostcode, PiWindPreAnalysis, PiWindS3, PiWindSinglePeril, PiWindVulnerability  
**Potential roles:** `postcode_geocoding_test`, `vulnerability_adjustment_test`, `loss_amplification_test`, `financial_semantics_test`  
**Access hint:** `public_github_example_bsd3_software_data_unreviewed`  
**Authoritative source:** <https://github.com/OasisLMF/OasisModels>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Index of 12 technical variants including main PiWind, not 12 independently calibrated natural-hazard models. AbsoluteDamage includes absolute loss amounts; Postcode illustrates disaggregation; PreAnalysis external geocoding; PostLossAmplification uplift; SinglePeril wind-only; Vulnerability adjustments, BI, data type and cloud variants require individual assessment. Root software licence BSD-3-Clause; linked assets need specific review.

## Bangladesh tropical cyclone historical catalogue Oasis models

**Candidate ID:** `oasislmf.bangladesh-cyclone.wind-surge`  
**Provider:** UK Met Office / BUET / Catrisk Solutions / Oasis Palmtree  
**Categories:** `tropical_cyclone`, `storm_surge`, `historical_event_catalogue`  
**Spatial scope:** Bangladesh  
**Temporal scope:** 12 tropical cyclones, 1991-2019; ensemble events  
**Resolution / granularity:** Model_data and lookup/test folders in Git; BGWTCSS1 footprint.bin.z and footprint.idx.z downloaded separately using download_bgwtcss1.sh  
**Potential roles:** `cyclone_wind_surge_pilot`, `event_footprint_validation`, `historical_catalogue_benchmark`  
**Access hint:** `repository_mit_software_separate_s3_hazard_terms_pending`  
**Authoritative source:** <https://github.com/OasisLMF/BangladeshCyclone>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Repo LICENSE states MIT; that alone does not prove all separately hosted footprint scientific input or third-party data redistribution/commercial rights. Read README, download script and provider terms; pin exact files and event probability semantics before risk modelling. A 12-cyclone historical/ensemble source must not be treated as an arbitrary independent 10000-year stochastic catalogue.

## UCL FITTER Indonesian tsunami Oasis model

**Candidate ID:** `oasislmf.uclfitter.indonesia-tsunami`  
**Provider:** University College London / FITTER project  
**Categories:** `tsunami`, `earthquake`, `submarine_landslide`, `model_data`  
**Spatial scope:** Indonesia, including Java and Sumatra model folders  
**Temporal scope:** research project published circa 2023; hazard scenarios are release specific  
**Resolution / granularity:** High-resolution tsunami risk model; model_data, keys_data, docs and separate footprint.bin.z/footprint.idx.z acquired by download_footprint.sh  
**Potential roles:** `tsunami_vulnerability_research`, `coastal_exposure_test`, `independent_loss_challenge`  
**Access hint:** `cc_by_nc_sa_4_0_noncommercial_sharealike_license_commercial_blocked`  
**Authoritative source:** <https://github.com/OasisLMF/UCLFitter>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Repo README and LICENSE expressly identify CC BY-NC-SA 4.0: attribution, non-commercial limitation and share-alike on adaptations; commercial model or redistributed derived assets need an independent permitted-rights basis. Source data licence and each upstream input still require confirmation. No footprint download, byte authentication or approval undertaken here.

## GEM Oasis earthquake demo model

**Candidate ID:** `oasislmf.gem.earthquake-demo`  
**Provider:** OasisLMF / GEM Foundation  
**Categories:** `earthquake`, `model_demo`, `oasis_adapter`  
**Spatial scope:** region to be verified from exact model data; not inferred from repository name  
**Temporal scope:** model vintage from data_version.json required  
**Resolution / granularity:** Contains keys_data, model_data, meta-data, tests, oasislmf.json and run-mdk.sh  
**Potential roles:** `openquake_oasis_comparison`, `earthquake_gul_test`  
**Access hint:** `software_bsd2_repo_assets_upstream_rights_unverified`  
**Authoritative source:** <https://github.com/OasisLMF/gem>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Repository LICENSE says BSD-2-Clause for code, not necessarily GEM-origin model data. Geographic coverage, catalogue rates, event footprint version, vulnerability rights and source hashes have not been checked; do not label as Dominican Republic without proving model metadata.

## Impact Forecasting EUWS deterministic windstorm scenarios

**Candidate ID:** `oasislmf.scenarios.impact-forecasting.euws`  
**Provider:** Aon Impact Forecasting / OasisLMF Scenarios  
**Categories:** `windstorm`, `scenario_footprint`, `model_demo`  
**Spatial scope:** Europe  
**Temporal scope:** Two actual November 2023 windstorms: Ciarán 1-2 Nov and Domingos 4-7 Nov; 3 alternative interpolated hazard footprints for each; not a complete stochastic annual catalogue  
**Resolution / granularity:** Model version CSV: ImpactForecasting,EUWS,1.0.0; two 12-byte event-set files; footprint.bin 4,518,908 B, vulnerability.bin 17,085,348 B; occurrence.bin 0 B; separate source_data/EUWS.zip 25,243,236 B. Footprint alternatives use 15/30/40 station neighbours.  
**Potential roles:** `european_storm_scenario_benchmark`, `german_carrier_stress_scenario`  
**Access hint:** `scenarios_repo_bsd3_provider_footprint_conditions_require_review`  
**Authoritative source:** <https://github.com/OasisLMF/Scenarios/tree/main/ImpactForecasting/EUWS>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Source README blob dc47f484937fe5d55415868694c917c5b15ddc6b, model_settings.json blob 08f07cf6d8b52c1d0fc2c47af390ec8c6cd5fd1e. Ciarán and Domingos are two 2023 physical storm scenarios with three alternative spatial wind-field reconstructions each: NOT six independent stochastic occurrences. Source declares pan-European measured-station interpolation and includes Germany. The example analysis_settings.json selects 'ciaran', but model_settings.json declares default 'cieren' absent from option IDs 'ciaran' and 'domingos' — CONFIGURATION DEFECT CANDIDATE, verify with real model runtime before calling it an execution blocker. Empty occurrence.bin means a complete annual event probability measure is not established by this folder. Repository BSD-3-Clause text and vendor-specific footprint terms require version-by-version review; no PML/AEP/OEP or German exposure claim.

## Impact Forecasting MAEQ scenario package

**Candidate ID:** `oasislmf.scenarios.impact-forecasting.maeq`  
**Provider:** Aon Impact Forecasting / OasisLMF Scenarios  
**Categories:** `earthquake`, `scenario_footprint`  
**Spatial scope:** code MAEQ; exact territory must be confirmed from model metadata  
**Temporal scope:** 1.0.0 scenario model folder  
**Resolution / granularity:** oasislmf.json includes model_data/1.0.0, lookup and example MAEQ location/account CSV paths  
**Potential roles:** `earthquake_scenario_challenge`  
**Access hint:** `scenarios_repo_bsd3_provider_asset_conditions_unknown`  
**Authoritative source:** <https://github.com/OasisLMF/Scenarios/tree/main/ImpactForecasting/MAEQ>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Only the code MAEQ and runnable-layout paths were verified; do not infer exact country, physical intensity units, vulnerability or event frequency without metadata and rights review. Vendor assets may have additional licence restrictions.

## Impact Forecasting TREQ scenario package

**Candidate ID:** `oasislmf.scenarios.impact-forecasting.treq`  
**Provider:** Aon Impact Forecasting / OasisLMF Scenarios  
**Categories:** `earthquake`, `scenario_footprint`  
**Spatial scope:** code TREQ; exact territory must be confirmed from model metadata  
**Temporal scope:** 1.0.0 scenario model folder  
**Resolution / granularity:** oasislmf.json includes model_data/1.0.0, lookup and example TREQ location/account CSV paths  
**Potential roles:** `earthquake_scenario_challenge`  
**Access hint:** `scenarios_repo_bsd3_provider_asset_conditions_unknown`  
**Authoritative source:** <https://github.com/OasisLMF/Scenarios/tree/main/ImpactForecasting/TREQ>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Only TREQ folder and model configuration paths were checked. No original hazard bytes, source-specific commercial permissions or annualized event rates verified.

## Impact Forecasting USTC source-data lead

**Candidate ID:** `oasislmf.scenarios.impact-forecasting.ustc`  
**Provider:** Aon Impact Forecasting / OasisLMF Scenarios  
**Categories:** `tropical_cyclone`, `scenario_source_lead`  
**Spatial scope:** US-related USTC code; exact geography and peril require provider confirmation  
**Temporal scope:** scenario archive, version unresolved  
**Resolution / granularity:** USTC directory currently exposes source_data only; do not claim a complete executable model package  
**Potential roles:** `us_cyclone_scenario_discovery`  
**Access hint:** `public_source_directory_vendor_rights_and_model_completeness_unknown`  
**Authoritative source:** <https://github.com/OasisLMF/Scenarios/tree/main/ImpactForecasting/USTC>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Directory inspected: source_data present, no top-level model_data or oasislmf.json observed. Distinguish discoverable source records from a runnable deterministic model.

## ARA US Hurricane historical scenario

**Candidate ID:** `oasislmf.scenarios.ara.us-hurricane`  
**Provider:** Applied Research Associates / OasisLMF Scenarios  
**Categories:** `hurricane`, `windstorm`, `historical_scenario`  
**Spatial scope:** United States; Hurricane Michael 2018 reference file  
**Temporal scope:** 2018 Michael and scenario-specific test vintages  
**Resolution / granularity:** US_Hurricane folder includes 2018-Michael_windgrid_ver36.csv.v2, model_data, source_data, keys_data, analysis settings and tests  
**Potential roles:** `us_hurricane_stress_scenario`, `oasis_footprint_ingest_test`  
**Access hint:** `scenarios_repo_bsd3_external_ara_hazard_licence_pending`  
**Authoritative source:** <https://github.com/OasisLMF/Scenarios/tree/main/ARA/US_Hurricane>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Reference file is a lead to original hazard field, not proof of permission to copy, redistribute or commercially reuse vendor footprint. The folder README appears to contain unrelated ParisWindstorm content; follow actual file names and inspect provider terms before using.

## JBA Philippines-Taiwan flood scenarios

**Candidate ID:** `oasislmf.scenarios.jba.philippines-taiwan`  
**Provider:** JBA Risk Management / OasisLMF Scenarios  
**Categories:** `flood`, `river_flood`, `surface_water_flood`, `scenario_footprint`  
**Spatial scope:** Philippines and Taiwan  
**Temporal scope:** scenario event/version dependent  
**Resolution / granularity:** Folder provides FLRF and FLSW, combined defended and undefended model folders, source_data and tests  
**Potential roles:** `defence_sensitivity_research`, `asia_flood_scenario_comparison`  
**Access hint:** `scenarios_repo_bsd3_jba_provider_rights_unverified`  
**Authoritative source:** <https://github.com/OasisLMF/Scenarios/tree/main/JBA/Philippines-Taiwan>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Defended and undefended variants must remain distinct. Different source model assumptions, design standards, hazard intensity, defence failure and vulnerability cannot be silently pooled; JBA vendor rights require exact review.

## JBA Ghana flood scenario set

**Candidate ID:** `oasislmf.scenarios.jba.ghana`  
**Provider:** JBA Risk Management / OasisLMF Scenarios  
**Categories:** `flood`, `scenario_footprint`  
**Spatial scope:** Ghana  
**Temporal scope:** event codes E635900, E689982, E760461  
**Resolution / granularity:** Three event scenario folders, source_data and tests  
**Potential roles:** `west_africa_flood_scenario_pilot`, `oasis_financial_module_test`  
**Access hint:** `scenarios_repo_bsd3_jba_provider_rights_unverified`  
**Authoritative source:** <https://github.com/OasisLMF/Scenarios/tree/main/JBA/Ghana>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Three named event scenarios, not independently annualized loss distributions. Source hazard/vulnerability science, additional JBA terms and full model binaries need review.

## JBA Nepal flood scenario set

**Candidate ID:** `oasislmf.scenarios.jba.nepal`  
**Provider:** JBA Risk Management / OasisLMF Scenarios  
**Categories:** `flood`, `scenario_footprint`  
**Spatial scope:** Nepal  
**Temporal scope:** event codes E151185, E432557, E505423  
**Resolution / granularity:** Three event scenario folders, source_data and tests  
**Potential roles:** `himalayan_flood_scenario_pilot`, `oasis_financial_module_test`  
**Access hint:** `scenarios_repo_bsd3_jba_provider_rights_unverified`  
**Authoritative source:** <https://github.com/OasisLMF/Scenarios/tree/main/JBA/Nepal>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Three scenario event folders are not a complete stochastic event catalogue; original hazard/vulnerability/right-to-redistribute checks remain open.

## IPE FranceHail deterministic scenario model

**Candidate ID:** `oasislmf.scenarios.ipe.france-hail`  
**Provider:** Insurance Partners Europe / OasisLMF Scenarios  
**Categories:** `hail`, `severe_convective_storm`, `scenario_footprint`  
**Spatial scope:** France  
**Temporal scope:** Historical storm Ela, 6-10 June 2014; six model event IDs 11-16 all assigned to period 1 of the example occurrence.csv  
**Resolution / granularity:** Source contains 6 events and a single period in occurrence.csv; model_data includes footprint.bin.z (9,108 B), footprint.csv (40,959 B), vulnerability.bin (9,476 B), vulnerability.csv (6,340 B), occurrence.bin (80 B), and events/occurrence CSV. Source contains areaperil_dict.parquet (22,014,048 B).  
**Potential roles:** `europe_hail_scenario_benchmark`, `hail_oed_test`  
**Access hint:** `scenarios_repo_bsd3_vendor_footprint_licence_conditions_unknown`  
**Authoritative source:** <https://github.com/OasisLMF/Scenarios/tree/main/IPE/FranceHail>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original source metadata: model_settings.json Git blob 5f9361339f2acfd31975b32dc15c2438ee8351f9 (Ela, June 2014); events.csv blob bf415bd0437f066ee593d37503fc50bb17f19fcf (IDs 11-16); occurrence.csv blob dde40cb030a4a1de06f6cb4d3f04d5b07c709900 (all period_no=1); source_data/Read Me blob 133cc294221a4033b8b8ae215a30aaf221a9e9bb (homeowners code 102, general auto 105). Analysis settings request GUL and example AEP/OEP but IL is disabled and a one-period historical example does not establish a validated annual stochastic measure, cedant net losses or reliable return periods. Neither six IDs nor identical placeholder dates prove six independent physical events. Regional damage functions require validation before German property use; vendor source rights remain unverified despite Scenarios repository BSD-3-Clause.

## GEM vulnerability function conversion library

**Candidate ID:** `oasislmf.vulnerability-library.gem`  
**Provider:** GEM Foundation / OasisLMF  
**Categories:** `earthquake`, `vulnerability`, `conversion_tools`  
**Spatial scope:** source model country-dependent  
**Temporal scope:** published source vintages vary  
**Resolution / granularity:** VulnerabilityFunctions/GEM includes original source/conversion code and model_data  
**Potential roles:** `earthquake_vulnerability_candidate`, `oasis_format_conversion`  
**Access hint:** `gem_data_cc_by_nc_sa_4_0_noncommercial_sharealike_blocked_for_commercial`  
**Authoritative source:** <https://github.com/OasisLMF/VulnerabilityLibrary/tree/main/VulnerabilityFunctions/GEM>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** GEM subfolder README explicitly applies CC BY-NC-SA 4.0 to vulnerability functions; repository-level converter code is BSD-3-Clause. Separate GEM input, transformed curves and modifications must respect noncommercial/sharealike. Confirm applicability and original curve licensing before admission.

## JRC vulnerability conversion candidates

**Candidate ID:** `oasislmf.vulnerability-library.jrc`  
**Provider:** European Commission JRC / OasisLMF  
**Categories:** `vulnerability`, `flood`, `conversion_tools`  
**Spatial scope:** country, continental or global options depending on source model  
**Temporal scope:** specific source functions and publication versions need review  
**Resolution / granularity:** JRC folder includes source_data, keys_data, model_data and JrcModel conversion code; converter supports country and continent selection  
**Potential roles:** `flood_damage_function_research`, `oasis_vulnerability_adapter`  
**Access hint:** `vulnerabilitylibrary_bsd3_converter_code_jrc_source_function_licence_unverified`  
**Authoritative source:** <https://github.com/OasisLMF/VulnerabilityLibrary/tree/main/VulnerabilityFunctions/JRC>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Root repository licence covers conversion code; JRC source functions may have their own rights, curve units, geographies and interpolation assumptions. Do not use for commercial insurance calibration without explicit original data terms.

## Emanuel vulnerability function conversion candidate

**Candidate ID:** `oasislmf.vulnerability-library.emanuel`  
**Provider:** OasisLMF VulnerabilityLibrary / Emanuel source family  
**Categories:** `vulnerability`, `windstorm`, `conversion_tools`  
**Spatial scope:** region/source model dependent; not established  
**Temporal scope:** specific function source publication to identify  
**Resolution / granularity:** Emanuel folder includes keys_data, model_data and source conversion code  
**Potential roles:** `tropical_cyclone_wind_vulnerability_research`  
**Access hint:** `vulnerabilitylibrary_bsd3_converter_code_external_emanuel_data_rights_unverified`  
**Authoritative source:** <https://github.com/OasisLMF/VulnerabilityLibrary/tree/main/VulnerabilityFunctions/Emanuel>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Inspect source function attribution and intensity/damage units before using; do not infer unrestricted commercial rights or calibrated exposure class transfer from root BSD-3-Clause converter licence.

## Oasis Risk Explorer open parametric risk tool

**Candidate ID:** `oasislmf.riskexplorer.multi-peril`  
**Provider:** Insurance Development Forum / OasisLMF / Maximum Information  
**Categories:** `tropical_cyclone`, `drought`, `earthquake`, `parametric_insurance`, `research_software`  
**Spatial scope:** tropical cyclone and drought global; earthquake selected locations  
**Temporal scope:** historical vs statistical scenario workflows  
**Resolution / granularity:** R Shiny application and support docs; separate data and model workflows, educational analysis rather than ready Oasis stochastic catastrophe model  
**Potential roles:** `parametric_risk_benchmark`, `event_catalogue_methods_research`  
**Access hint:** `root_software_bsd3_external_source_dataset_rights_to_review`  
**Authoritative source:** <https://github.com/OasisLMF/RiskExplorer>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** README describes public free open-source tool with BSD-3-Clause software licence and guided parametric workflow. Do not treat tool output as property-insured losses or its component data as universally redistributable.
