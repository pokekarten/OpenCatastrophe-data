<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Worldwide CAT source-register gap audit and linkage plan (2026-11-01)

**State:** research and non-admission discovery only. No third-party data bytes acquired, no new rights or scientific admission, no real-world hazard-loss runs. The executable candidate register for the six new sources is `landscape/sources-global-cat-gaps-20261101.json`; `landscape/sources-global-cat-gaps-20261101.md` is generated. The source-linkage report includes conservative hypotheses, not executable joins.

## Evidence anchor and scope

- Audited public `main` at commit `f3d047f6e67e8ac3140b295368325b8b5de4032d` (2026-11-01); 34 canonical `sources*.json` shards contained 263 candidate entries at that snapshot. There were 42 JSON access contracts and 15 JSON accepted manifests. Counts describe *registry files*, not successful downloads or model-ready datasets.
- The same 263 candidate IDs were enumerated from both halves of the live GitHub landscape directory; this is a search/inventory count, **not** a local run of `python scripts/check_all.py` and not an assertion about a private data lake or Neon rows.
- This PR proposes 6 genuinely different provider/product identities; if merged, the expected landscape inventory becomes 269 candidates in 35 shards, subject to the repository's duplicate-ID and projection checks.
- Open pull requests at audit time included #937 (historical French BD TOPO original 2016 bytes), #935 (fully synthetic CAT-XL calculation), #907 (US market stock), #899 (international insurer directories), #898 (NFIP API), #894 (Natural Earth basemap), #891 (EIOPA source preflight). Keep these overlapping upstream access, legal and insurer efforts in their existing branches; this PR does not claim their work or duplicate their source entries.

## Actual access-state breakdown (all 42 access JSON records on audited main)

| Contract status | Count | Meaning for readiness |
| --- | ---: | --- |
| `documented_only` | **31** | Describes metadata/access and boundaries; no authorised enabled retrieval follows from this status. |
| `probe_ready` | **6** | Bounded provider-specific probe contract defined, not a full source-data pipeline or model admission. |
| `blocked_credentials` | **3** | Access may require a provider account/token; no credentials or backend secrets in Git. |
| `restricted_by_terms` | **2** | Terms explicitly restrict automation; preserve `do_not_automate` rather than trying alternate hosts. |

Of the 42 access contracts, original `rights_and_policy.dataset_rights_status` entries are **26 verified**, **12 not_reviewed**, **2 restricted**, **1 conflicting**, and **1 unknown**. "Verified" is the provider/dataset *rights-evidence review state*, **not** global permission for commercial use, all derived products or source-byte redistribution. A `probe_ready` contract is a bounded technical path, **not** proof of a successful live source retrieval.

Current practical lead: `wsv.pegelonline.rest-v2.dresden` is `probe_ready` with `implementation_decision=build_adapter_now`; `geoboundaries.gbopen`, `dwd.cdc.extreme-wind.http-file`, `emsc.seismicportal.fdsn-event`, `gfz.geomagnetic-kp` and `noaa.swpc.real-time-solar-wind` are `probe_ready` with `build_later`. Prioritise source-specific bounded tests where the right to query and record evidence is clear. Note that `eubucco.buildings.v0.2` remains `documented_only` despite its detailed object-store specification.

## Registered already — do not create aliases

| Data layer | Existing canonical candidates/admissions | Practical warning |
| --- | --- | --- |
| EU building stock | `eubucco.buildings.v0.2`, `overture.maps.buildings`, `ec-jrc.ghsl.ghs-obat.r2024a`, `fr.rnb.buildings`, `nl.kadaster.bag`, national registers | Each covers different vintages and semantic building objects. Source-family overlap with OSM and Microsoft is substantial; EUBUCCO's v0.2 NUTS2016 partition and regional licences must be preserved. |
| Modelled/observed river flood | `ec-jrc.cems.europe-mediterranean-river-flood-hazard-maps.2026`, `ec-jrc.cems.global-river-flood-hazard-maps.2026`, `copernicus.cems.gfm.v4.1.1`, `copernicus.cems.glofas-historical` | Static return-period depth, event-derived satellite extent and discharge time series are distinct quantities. |
| Earthquake | `efehr.eshm20` (admitted manifest), `gem.global-exposure-model.v2026.0.0`, `gem.global-vulnerability-model.v2026.0.0`, `usgs.anss.comcat`, `usgs.shakemap` | Observed event catalogue, ground motion, building taxonomy and fragility are not interchangeable. |
| Tropical cyclone / storm | `noaa.ncei.ibtracs.v04r01`, `storm.ibtracs.present-climate.v4` (admitted manifest), `noaa.ncei.hursat-b1.v06`, `climk.winds.storm-footprints.v2` | Stochastic synthetic years and observational events require separate IDs, wind definitions, climate baselines and lineage. |
| Wildfire / heat / hydro | `global.fire-atlas.v20260408`, `nasa.lance.firms.active-fire`, `nasa.modis.mcd64a1.v6.1`, `nasa.smap.spl4smgp.v8`, `worldpop.global2.r2024b` | Sensor detections, derived burned areas and exposure proxies are not claims or insured values. |
| Insured exposures and losses | EIOPA CAT Hub accepted **metadata** manifests, EIOPA sample and NFIP landscape records, `usace.nsi.base.2026` | Aggregate, modelled and sampled holdings must not become property-level policy or full-market exposures by interpolation. |

## Six additional source products discovered from primary evidence

| New candidate ID | Authoritative provider/format | Why distinct and how to join | Rights and scientific stop sign |
| --- | --- | --- | --- |
| `ec.jrc.satellite-flood-depth-europe.2015-2024` | [JRC satellite-derived European flood depths](https://data.jrc.ec.europa.eu/dataset/0bc96690-b89c-4909-9166-c2c322a20130); event GeoTIFFs | Depth reconstructed for historical Sentinel-1 flooding, not simply the existing GFM extent. Link by original event interval and geometry, **not** a presumed same event ID. | Depth is **centimetres**, background/seasonal-water **9999** is a mask, topography-assisted derivation shares input lineage with GFM. Provider catalogue 2015-2024; [EuroFlood](https://github.com/cisgroup/euroflood) currently advertises an extended archive — verify the version and footprint before using it. |
| `gfz.openbuildingmap.global.2025` | [OpenBuildingMap](https://www.openbuildingmap.org/); tiled footprints, usage, height, floorspace | Adds a consolidated global *derived* building layer for coverage/attribute comparisons. Link polygons and, if proven, original source IDs with EUBUCCO, Overture and GHS-OBAT. | ~2.7B objects does **not** mean 2.7B newly independent assets. Uses OSM, Google, Microsoft and GHSL input families; ODbL rights and independent holdouts require review. |
| `wri.aqueduct-flood-hazard.v2.2020` | [WRI Aqueduct Floods v2](https://datasets.wri.org/datasets/aqueduct-floods-hazard-maps); coastal and river depth GeoTIFFs | Global cross-model comparison with JRC flood grids, with exact return period, climate horizon and coastal/river method. | Simulated flood depths are **metres**, no flood defences, 2020-10-20 river-map correction. Do not silently conflate with Aqueduct **4** water-risk indicators. |
| `wri.aqueduct.water-risk-atlas.v4.0` | [WRI Aqueduct 4.0 global indicators](https://datasets.wri.org/datasets/aqueduct-global-maps-40-data); basin and country/administrative views | Drought and water-stress *context*, stratification and sensitivity tests for global exposure; crosswalk basin polygons + vintage. | This is not an event-loss generator or flood-depth map; combined indices/aggregate rankings are lossy. Exact WRI reuse and registration requirements remain to check. |
| `gem.global-seismic-hazard-map.v2026.1` | [GEM global probabilistic seismic hazard](https://www.globalquakemodel.org/product/global-seismic-hazard-map); vector/raster | Cross-regional benchmark and future combination with GEM taxonomy/fragility and OpenQuake engines, using exact intensity measures. | Base PGA on rock Vs30=800m/s at **10% exceedance in 50 years** is *not* an annual event set; public map has non-commercial/share-alike restrictions and commercial licences differ by layer. |
| `imperial.iris.synthetic-tropical-cyclones.2024` | [Sparks & Toumi 2024 IRIS dataset](https://doi.org/10.1038/s41597-024-03250-y); separate Figshare data + [GitHub model](https://github.com/njsparks/iris) | Independent *model methodology* for the already catalogued STORM/IBTrACS synthetic TC research, but built partly from common observational inputs. | 10,000 synthetic years, only post-peak-intensity life cycle, 1980-2021 IBTrACS training, independent model years with **no interannual correlation**. Original data rights must not be inferred from the GPL code or article license. |

### Software interoperability projects (tools, **not** independent source datasets)

- [Delft-FIAT](https://github.com/Deltares/Delft-FIAT): raster/vector flood impact; [HydroMT-FIAT](https://github.com/Deltares/hydromt_fiat) constructs inputs and vulnerability mappings. [HydroMT-FIAT example data](https://zenodo.org/records/20157939) **explicitly delegates individual data licence checks** to the source configurations/providers, so never blanket-admit its archive.
- [CLIMADA](https://github.com/CLIMADA-project/climada_python): reference calculation and uncertainty methodology, not a guaranteed transferable hazard catalogue.
- [CLIMAAX FLOODS](https://github.com/CLIMAAX/FLOODS): concrete river/coastal flood and building-damage workflows; its JRC return-period maps require scenario/version review.
- [EuroFlood](https://github.com/cisgroup/euroflood): promising event index/access adapter for the new JRC European flood-depth product; it is not a new independent observation provider.
- [Oasis Open Data Standards](https://github.com/OasisLMF/OpenDataStandards) and [RDLS](https://github.com/GFDRR/rdl-standard): candidate **projections** of native data and evidence, not permission to dilute native lineage/admission. Versions and lossiness must be pinned.

## Executable cross-registry research view (this PR)

The repository already has three separate validated tools: `scripts/build_source_access_inventory.py` (discovery/admissions/access), `scripts/source_linkage_audit_v0.py` (manual candidate-to-candidate scientific hypotheses), and `scripts/export_cat_source_registry_sqlite.py` (isolated CAT-only **discovery metadata** projection). They must **not** be replaced by a second independently maintained canonical register.

`scripts/build_cat_source_crosswalk_v0.py` now joins the two *read-only derived research views by exact source ID* and adds source-by-source inspection fields:

- canonical discovery shard; provider and scope; existing access contract IDs/status; bounded next access step;
- explicit linked candidate IDs, relationship hypothesis, missing proof requirements and prohibited inferences;
- sources sharing the **exact same authoritative provider page** as a separate potential-overlap review group (never assumed to contain the same bytes, never automatically deduplicated);
- fail-closed check that candidate ID, provider, authoritative URL and canonical shard name agree between the independently generated access and linkage inventories (prevents silently attributing another provider's access contract to a similarly named source);
- separate admitted manifest entries with no privilege inheritance if the same ID also appears in a discovery record;
- aggregate counts for candidates with no reviewed concrete access contract and candidates with manual linkage hypotheses;
- research-only source `rights_posture`, known licence/terms flags and access-automation decision, without granting execution;
- a **non-disjoint** breakdown of *uncontracted* discovery candidates by their existing source categories, so original providers and scientific model layers can be prioritised without claiming country/peril completeness.

Run from a Git checkout after the normal dependency install:

```bash
python scripts/build_cat_source_crosswalk_v0.py --summary
python scripts/build_cat_source_crosswalk_v0.py --out /tmp/cat-source-crosswalk.json
python -m unittest tests.test_cat_source_crosswalk_v0 -v
```

The output is a **deterministic transient report**, not an approved warehouse schema and not an import queue that may execute requests. An unlinked source does not imply scientific independence: this script marks `scientific_independence_proven=false` even for candidates with no currently authored relationship hypothesis. A `probe_ready` source is still not proven downloaded or model-ready. All joins into original source bytes require source-specific evidence and separate admission.

## Optional isolated CAT3 SQLite source/access/linkage research index

A validated JSON crosswalk is also exposed as a **new, separate, queryable CAT-only research database**, without modifying the already existing `CAT1` geographic SQLite, `CAT2` NUTS crosswalk SQLite or existing `scripts/export_cat_source_registry_sqlite.py` export. The new script `scripts/export_cat_source_crosswalk_sqlite_v0.py` builds SQLite **application ID 0x43415433 (CAT3)** and schema version 1 from the existing crosswalk report. It requires a *new*, absolute `*.cat.sqlite` path **outside** the Git checkout, will not overwrite or follow an existing output symlink, and performs integrity/foreign-key checks.

```bash
mkdir -p /secure/cat-data/staging
python -m unittest tests.test_export_cat_source_crosswalk_sqlite_v0 -v
python scripts/export_cat_source_crosswalk_sqlite_v0.py \
  --out /secure/cat-data/staging/source-research.cat.sqlite

# Example: inspect work queue with locally available sqlite3 CLI
sqlite3 -readonly /secure/cat-data/staging/source-research.cat.sqlite \
  "SELECT candidate_id, provider, readiness FROM uncontracted_candidates ORDER BY candidate_id LIMIT 20;"
sqlite3 -readonly /secure/cat-data/staging/source-research.cat.sqlite \
  "SELECT r.recipe_id, r.relationship, e.candidate_id FROM source_link_recipe r JOIN recipe_endpoint e USING(recipe_id) ORDER BY r.recipe_id, e.candidate_id LIMIT 30;"
sqlite3 -readonly /secure/cat-data/staging/source-research.cat.sqlite \
  "SELECT category, uncontracted_candidates FROM uncontracted_by_category ORDER BY uncontracted_candidates DESC LIMIT 20;"
sqlite3 -readonly /secure/cat-data/staging/source-research.cat.sqlite \
  "SELECT candidate_id, rights_posture, automation_decision FROM candidate_rights_review_queue ORDER BY candidate_id LIMIT 30;"
sqlite3 -readonly /secure/cat-data/staging/source-research.cat.sqlite \
  "SELECT candidate_id, terms_flag FROM candidate_rights_flag ORDER BY candidate_id, terms_flag LIMIT 30;"
```

The `/secure` location is illustrative, must already exist and must be user-controlled. It is **not** a cloud database service and creates no persistent application database on its own. `source_link_recipe` and `recipe_endpoint` encode **manually authored hypotheses**, not successful scientific joins. `existing_manifest_separate` preserves the existing manifest trust domain; `source_access_assignment` preserves documented access ID rather than implying a successful probe. `candidate_category` and `candidate_role` enable source-layer/role filters. `candidate_access_status` retains **source-level aggregate** status labels; it does not invent a one-to-one relationship between access-interface IDs and statuses. `candidate_rights_flag` preserves terms and licensing flags, and `candidate_rights_review_queue` keeps review visibility even where the source rights posture says `source_rights_verified` but a material restriction is flagged. The `uncontracted_by_category` counts are deliberately **not disjoint**: one source can have multiple categories. `candidate.access_next_action` remains an evidence-backed suggested review action, not an executable command. `shared_provider_page` stores same-page *review* hints only, never duplicate-confirmation. The export refuses unsupported authority state or inconsistent counts; rows assert no newly proven join, admitted model input, source bytes or granted rights. It never fetches third-party data, touches insurer/TCG databases or exports provider bytes.

## Highest-impact error/risk classes found in the existing workflow

1. **Metadata completeness mistaken for usable data:** 263 candidates are not 263 downloaded or licenced assets; 42 access contracts are not 42 authorized running importers. Gate by actual provider bytes, SHA256, deterministic parser receipt and explicit rights/model role.
2. **Upstream overlap mistaken for independent evidence:** EUBUCCO, OpenBuildingMap, Overture, Microsoft/OSM/Google and GHS-OBAT share footprint sources; GFM and the JRC depth dataset share detection lineage. Track *source-family and per-attribute* parentage before assigning validation holdouts.
3. **Units and sentinel semantics:** JRC 2015-2024 observed/reconstructed depth is in cm with special value 9999; Aqueduct/JRC flood hazard depths are generally metres. Conversions must precede joins, with masked cells not mapped to high depth or 0.
4. **Mismatched temporal/administrative support:** building footprint vintage, hazard event timestamp, climate scenario, NUTS/GADM version, fiscal exposure date and claims period are different; cannot reconstruct past covered property from today's physical buildings without an explicit assumption.
5. **Aggregate-to-property or physical-to-insured inference:** GEM modelled replacement cost, NSI property value, EIOPA limited sample and WRI aggregated water-risk cannot be used as observed insurer TIV or a named company's portfolio.
6. **Stochastic catalogue versus return-period map:** GEM PGA and WRI flood return period maps do not by themselves generate physically consistent globally correlated event years. OpenQuake/NextGen/Oasis need versioned event catalogue, dependence, and explicit loss/order contracts.
7. **Non-commercial and derived-data licensing:** GEM open seismic products are non-commercial; EUBUCCO has regional non-commercial exceptions; OpenBuildingMap is ODbL. A downloaded raster's availability never overrides its dataset licence.
8. **Source-linkage audit is currently a conservative hypothesis inventory:** `scripts/source_linkage_audit_v0.py` lists manually curated recipes and marks all automatic joins false. A hypothetical link is not a run-tested spatial or record-level match; model-consumer proof must be separate.

These are verified architectural gaps and high-risk potential failure modes, **not** claims that a defect in a currently executing importer or a wrong scientific number has been reproduced.

## Three controlled pilot pipelines

### P0: historical European flood holdout
1. Freeze one municipality/catchment and event window; get separate exact checked rights and hashes for a *bounded* JRC satellite flood-depth event and existing GFM extent.
2. Decode cm -> m with 9999/valid-pixel mask; preserve original Sentinel acquisition and topographic reconstruction provenance. Never treat GFM extent as an independent validation target for its derivative depth.
3. Match an independently sourced building inventory (official geometry if possible; EUBUCCO documented provenance) only in valid spatial and temporal support. Report hit/miss/ambiguous polygon join, per-field provenance and withheld pixels.
4. For actual loss estimates add separately licence-reviewed vulnerability curves and independent damage holdout. No insured portfolio until coverage/terms are supplied and approved.

### P1: global flood competing models
1. Freeze WRI Aqueduct Floods v2 corrected raster and matching current/climate scenario and JRC global model period, then align defended assumptions, return period, units and grid.
2. Compare *physical flood depth* on a reproducible sample, with differences by flood mechanism, coastal overlap, country and upstream model assumptions. Never average incompatible return periods.
3. Validate independently where observations actually exist; report skill at each grid and return period and explicit missing/excluded geography.

### P2: global cyclone and earthquake risk model components
1. IRIS versus STORM: compare basin/tracks/10-min vs 1-min wind and pre/post-LMI stage; maintain multi-year correlation hypotheses separately from independent simulated years.
2. GEM hazard: compare matched PGA/soil/reference conditions and regional source-model lineage to admitted EFEHR products without claiming independent verification of shared model families.
3. Only then map hazard -> vulnerability -> physical loss -> explicitly synthetic policy loss -> reinsurance and retro; record Oasis OED/ORD or RDLS views as derived projections with source/hash bindings.

## Required per-artifact research/provenance ledger (proposed; NOT existing schema)

| Class | Non-negotiable fields |
| --- | --- |
| Identity + access | provider, exact product, edition/version, downloadable object/query, original documentation, authentication method, current rate/size bounds, retrieved UTC, SHA256, byte count |
| Licence + permitted roles | terms evidence URL and review time; download/commercial use/derivation/redistribution/AI-training permissions **separately**; restrictions by underlying source component; admission/holdout role |
| Space/time + semantics | CRS and axis order, vertical datum, depth/velocity/intensity units, resolution, observation time/event interval, validity masks, coverage polygon, NUTS/GADM vintage, perils and loss metrics |
| Lineage | original upstream source family, original record ID where valid, transform hash/configuration, `measured|official_record|derived|modelled|estimated`, confidence and uncertainty, common-input groups |
| Join proof | stable ID or spatial candidate method, approved match level (building/event/grid/region), precision/recall or manually checked sample, many-to-many cardinality, temporal alignment, unmatched/ambiguous denominator |
| Scientific evaluation | peril-specific physical meaning, vulnerability curve identifier, sample/training/calibration/validation/holdout split, independent observation type, sensitivity tests, known physical/insurance exclusions |

**Acceptance rule:** one qualified original asset + frozen rights/metadata + checksum + a bounded parser/QA test + a scientifically explicit role is stronger evidence of progress than a hundred additional URL records. No source is silently promoted from `landscape/` to `manifests/`. No provider bytes are committed to Git without exact approval.

## Reproducible checks and open work

The intended post-merge checks are:

```bash
python scripts/render_public_views.py --check
python -m unittest tests.test_global_cat_linkage_v0 -v
python scripts/source_linkage_audit_v0.py --out /tmp/source-linkages.json
python scripts/check_all.py
```

The source-linkage audit should report the six new candidates and six new conservative recipes after merging; it is not an evidence-bearing physical join. Before a wider global onboarding wave, validate the source landscape against primary provider metadata, then build bounded access contracts and parser checks one coherent provider/product at a time. Prioritize existing high-value but `documented_only` records rather than registering exact aliases as new achievements.

## SQLite application identity separation (2026-11-01)

The existing partial German ADM1↔NUTS2021 stage (#971) has reserved **CAT3** SQLite application ID `0x43415433` for provisional 14-region/2-withheld geographic evidence. The derived cross-domain **source-access/linkage research** exporter here must not share this `PRAGMA application_id`; it now uses its own **CAT4** ID `0x43415434`, separate source-research schema/profile and an explicit test asserting pairwise disjoint application IDs across CAT1, CAT2, CAT3 and CAT4. Neither SQL research stage is a canonical provider dataset, insurance exposure store or model-authorized join. Existing German CAT3 stays unchanged; no migration of its geographic source data occurs.
