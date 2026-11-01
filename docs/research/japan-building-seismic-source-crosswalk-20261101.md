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
| GSI Fundamental Geospatial Data building outlines | https://service.gsi.go.jp/kiban/ ; https://service.gsi.go.jp/kiban/app/help/ | JPGIS/GML basic items include building exterior lines. GSI requires free registration and flags potential Survey Act reproduction/use applications. This is **not** anonymous open bulk access or preapproved raw-data redistribution. |
| NIED J-SHIS | https://www.j-shis.bosai.go.jp/en/downloads ; https://www.j-shis.bosai.go.jp/en/agreement | PSHM hazard grids/curves and site amplification metadata. Product download may be public, but exact map version, rights, attribution and permitted dissemination remain to be assessed; probability-horizon outputs cannot be treated as an actual earthquake event. |

**Provider-page check:** 2026-11-01, documentation viewed via public research search. No direct HTTP response, authenticated endpoint, original asset bytes, per-object statistics, catalogue SHA, licence-page snapshot or data-provenance receipt was produced. Access remains documentation-only; do not equate a live webpage with exact provider-file access.

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

## Existing OpenCatastrophe boundaries

Retain landscape discovery as `not_admitted`. This PR adds one non-executable T0 access contract in `access/jp.mlit.plateau.citygml.3d-city-models.json` for the officially documented PLATEAU `GET /datacatalog/plateau-datasets` endpoint. It deliberately remains `documented_only` with `probe_contract.mode=none`: unknown service automation terms, a potentially oversized unfiltered response, and mutable 'latest' releases block an actual probe. GSI and J-SHIS still lack repository access contracts; their access/rights must be reviewed separately. No manifest or model run-evidence is created. Technical probes require a new bounded source-specific review, while admitted uses require accepted `manifests/` plus source review. Existing European building overlap lessons (notably Luxembourg/EUBUCCO) are a methodological precedent, not evidence that the Japan identity matching problem has already been solved.
