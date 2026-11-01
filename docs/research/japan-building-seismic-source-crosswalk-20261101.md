<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Japan building geometry + seismic hazard: non-admission research gate (2026-11-01)

**Scope:** discovery-only, zero external source bytes and zero CAT-model input admissions. This note supports the canonical `landscape/sources-japan-building-seismic-20261101.json` shard; it is not a duplicate machine registry, a licence approval, or a download authorization.

## Verified provider surfaces

| Source | Official starting points | Evidence and blocking limitation |
| --- | --- | --- |
| MLIT PLATEAU | https://www.mlit.go.jp/plateau/en/ ; https://www.mlit.go.jp/plateau/faq/ ; https://docs.plateauview.mlit.go.jp/datasets/citygml/ | Municipality-authored CityGML 3D models, building semantics and varying LoD; public programme says several open licence families, with commercial use possible. Select exact city, data edition, licence and attribution before requesting assets. PLATEAU CityGML API is experimental and has no guaranteed schema/service availability. |
| GSI Fundamental Geospatial Data building outlines | https://service.gsi.go.jp/kiban/ ; https://service.gsi.go.jp/kiban/app/help/ | Basic JPGIS/GML includes building exterior lines. Registered ID/password is required for downloading; Survey Act reproduction/use approval may apply. GSI documents a shift from JGD2011 to JGD2024 in newer provisioned files and GML download specification v5.3 from 2026-07-31. The source is **not** anonymous bulk access or automatically approved for CAT-data reuse. |
| NIED J-SHIS | https://www.j-shis.bosai.go.jp/en/downloads ; https://jmapweb6v.bosai.go.jp/en/agreement | Official Article 5 **prohibits raw-map duplication and third-party distribution even when format-converted**, while allowing some processing/derived publication subject to restrictions. Sale of derived results requires provider contact and possibly application. Article 4 imposes attribution and special site-amplification citations. The data are not actual observed event/damage records. |

**Provider-page check:** 2026-11-01, documentation and primary J-SHIS terms viewed via public research search. No direct HTTP response, authenticated endpoint, original asset bytes, per-object statistics, catalogue SHA, licence-page snapshot or data-provenance receipt was produced. Access remains documentation-only; do not equate a live webpage with exact provider-file access.

## Operational link hypotheses (do not implement automatic joins yet)

1. **PLATEAU ↔ GSI:** choose one municipality and an explicit common acquisition-era window; compare only published coverage footprints and legal permitted reuse. A later bounded study may project GSI building exterior lines and PLATEAU CityGML LOD0/LOD1 footprints into a documented common metre-based CRS, repair only explainable geometry defects, and compute aggregate intersection/union, split/merge, and date-mismatch rates. Retain native dataset/building identifiers and lineage separately; geometry overlap is not proof of legal building identity.
2. **PLATEAU ↔ J-SHIS:** intersect only a reviewed mesh polygon with reviewed building geometries, preserving J-SHIS version, hazard intensity measure, exceedance probability and exposure-time horizon. Site amplification factors are not fragility curves, damage rates or event observations. No asset-level deterministic damage, insured sum, replacement cost or insurer attribution from overlay.
3. **PLATEAU / GSI ↔ OSM / Microsoft / Overture / GlobalBuildingAtlas:** any comparative exercise must first identify common upstream footprint imports, licence incompatibilities and release vintages. Do **not** count aligned polygons as independent validation without source-lineage checks. GlobalBuildingAtlas LoD1 height sources are not interchangeable with the separately licensed ODbL polygon subset.

## Proposed smallest rights-safe technical experiment

- **T0 — exact provider metadata:** identify one municipality PLATEAU catalogue record (city, fiscal release, dataset ID, stable provider landing URL, CityGML LoD, rights) and one GSI mesh in the same area; identify one J-SHIS versioned mesh/map edition. Record authoritative terms timestamp, attribution and allowed action separately for all three.
- **T1 — strictly bounded access:** permit at most one fixed *anonymous, metadata-only* PLATEAU catalogue/API probe after verifying the endpoint-specific API terms and redirect policy. Use a small response cap, fixed URL and timeouts, no pagination or downloads. **No** GSI credentialed request without authorization/rights review; J-SHIS first uses provider metadata and version documentation only.
- **T2 — original asset proof (new PR):** only after exact licence, intended commercial/derived/raw use, privacy and attribution decisions, fetch one predeclared small original provider file to transient isolation; verify response length, SHA-256, native file format, object count, CRS/axis/vertical datum, measured-height units, LoD, null coverage, dates and any duplicate IDs; do not persist raw bytes in Git.
- **T3 — scientific evidence:** bounded aggregate overlap/confusion matrix with one city and one comparison mesh, source lineage and independent holdout. No import to an exposure database or use in catastrophe loss calculation until additional review and admission.

## Fail-closed acceptance criteria

- No join that treats a PLATEAU feature, GSI exterior line and insurance risk as the same entity solely because geometries overlap.
- No building-height inference from J-SHIS site amplification or from PLATEAU LOD1 coordinates where the source does not provide an admissible measured-height field and verified vertical datum.
- No treating probabilistic hazard (for example a 50-year exceedance statistic) as an individual quake footprint or damage observation.
- No claiming 100% Japan-wide building coverage or construction year completeness; list municipal releases and per-field missingness first.
- No anonymous-GSI access bypass, no bulk data acquisition and no commercial/redistribution permission extrapolation from general programme pages.

## Implemented offline PLATEAU catalogue gate (synthetic tests only)

The fixed Shinjuku municipality code `13104` and fiscal CityGML release year `2024` are illustrative identifiers from the official PLATEAU REST API documentation; they do **not** prove the currently live API returns that release. `python research_runners/plateau_citygml_catalogue_preflight_v0.py --input /path/to/externally-held-catalogue.json` validates only a previously lawfully supplied offline JSON catalogue. It requires exactly one concrete target release, consistent city and prefecture IDs, usable feature-type metadata including `bldg`, valid fiscal years, spec, safe URL field syntax and source metadata caps; it explicitly refuses a `latest` release as a historical identity. The diagnostic emits only bounded structural booleans, target city/year, a hash of user-supplied input, and provenance/approval=false flags. There is no network client, building-geometry parsing, original ZIP download, live receipt or CAT admission. See synthetic adversarial regression tests in `tests/test_plateau_citygml_catalogue_preflight_v0.py`. The potentially full, unfiltered REST catalogue can exceed the 2 MiB offline budget: in that case the tool fails closed until a legally and technically reviewed bounded metadata provider call is defined.

## Existing OpenCatastrophe boundaries

Retain landscape discovery as `not_admitted`. This PR adds one non-executable T0 access contract in `access/jp.mlit.plateau.citygml.3d-city-models.json` for the officially documented PLATEAU `GET /datacatalog/plateau-datasets` endpoint. It deliberately remains `documented_only` with `probe_contract.mode=none`: unknown service automation terms, a potentially oversized unfiltered response, and mutable 'latest' releases block an actual probe. J-SHIS now has a static contract `access/jp.nied.jshis.pshm.site-amplification.json` with `restricted_by_terms`, `do_not_automate` and `probe_contract.mode=none`. GSI also has an explicit static contract `access/jp.gsi.fgd.building-outline.gml.json` with `blocked_registration`, `do_not_automate` and `probe_contract.mode=none`; provider-account registration and Survey Act rights are not bypassed. The J-SHIS terms are binding for the public-source pathway, not an approval to publish a raster, derived commercial products or CAT inputs. No manifest or model run-evidence is created. Technical probes require a new bounded source-specific review, while admitted uses require accepted `manifests/` plus source review. Existing European building overlap lessons (notably Luxembourg/EUBUCCO) are a methodological precedent, not evidence that the Japan identity matching problem has already been solved.
