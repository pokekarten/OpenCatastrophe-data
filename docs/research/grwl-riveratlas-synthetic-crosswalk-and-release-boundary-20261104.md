<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GRWL and RiverATLAS: release identity and synthetic spatial crosswalk

Reviewed: 2026-11-04. Scope: original-provider publication evidence and a deterministic, *synthetic-only* geometric diagnostic. This is **not** an admission, verified real-world join, original dataset download or flood model.

## Two GRWL release identities cannot be interchanged

Original 2018 dataset: https://zenodo.org/records/1297434 (DOI 10.5281/zenodo.1297434). The provider lists the simplified archive GRWL_summaryStats_V01.01.zip with MD5 **c37021e144fbff19ae3fc4e701d85d38**.

Separate 2026 dataset: https://zenodo.org/records/18624542 (DOI 10.5281/zenodo.18624542). Its **file list** has GRWL_summaryStats_V01.02.zip with MD5 **cac403c1a59bce7a74432085d3f5bd3a**, even though its descriptive text mentions the older V01.01. Keep 2018 and 2026 as different record/file identities; actual file content differences and independently measured SHA-256 remain **unverified**. Provider-reported MD5 is not a verified SHA-256 receipt.

GRWL segment width_mean is a mean wetted width under selected near-mean-discharge Landsat conditions, not flood-stage width, flow volume or loss severity. Simplified lakeflag means 0 river, 1 lake/reservoir, 2 tidal river, 3 canal. Upstream documentation: https://zenodo.org/records/1297434

HydroRIVERS v1 (~8.5 million river reaches) is defined separately from the GRWL mapped river geometry: https://www.hydrosheds.org/products/hydrorivers. HydroATLAS enriches the HydroRIVERS network with many hydro-environmental attributes: https://www.hydrosheds.org/hydroatlas. No shared GRWL↔RiverATLAS identity key is established by these provider pages; joining requires spatial/topological evidence.

## Executed synthetic research step

The script research_runners/grwl_riveratlas_synthetic_crosswalk_v0.py implements a **bounded, offline and synthetic-only** input contract. It rejects real geographic coordinate system declarations such as EPSG:4326. It requires exact release name, archive name and provider-listed MD5, a fictitious LOCAL_METRIC_SYNTHETIC coordinate frame, bounded 2-D fictional line strings and positive width in metres.

It proposes a one-to-one geometry candidate only when fictional river lines are near-parallel, at most 20 synthetic metres apart, overlap at least 80% of each line in a 20 m buffer, and the reciprocal mapping is unambiguous. Crossing streams, remote segments, mismatched/split reaches and duplicated candidates fail closed. Non-river lakeflags are excluded. Thresholds are arbitrary **synthetic test parameters**, *not* calibrated hydrographic conflation accuracy.

Execution: python -m unittest discover -s tests -p 'test_grwl_riveratlas_synthetic_crosswalk_v0.py' -v

A 16-case synthetic test suite was run in the ChatGPT Linux execution environment on 2026-11-04 with all 16 passing. Exact-branch repository-wide tests and GitHub CI must be reviewed separately. The result always explicitly reports original_source_bytes_observed=false, model_input_approved=false, source_file_sha256_verified=false, licensing_admitted=false, real_world_geometry_processed=false and neon_production_modified=false. No original GIS bytes, insurer data, credentials or productive databases were accessed or modified.

## Required next real-world evidence

1. Choose one specific original GRWL record/file, original HydroRIVERS or RiverATLAS v1 file, exact use rights and per-column licence/ODbL obligations; original public download is not blanket CAT model admission.
2. Retrieve a bounded, permitted regional slice **outside Git**, freeze access time, file name, byte length and independently calculated SHA-256; check original DBF fields, CRS, edge cases, missingness and lakeflags. Quantify the difference between the 2018 and 2026 simplified archives before updating any model-source default.
3. Transform WGS84 geometries into a justified local metric projection. Do not use the fictional coordinate comparator on real geodetic degrees.
4. Build a real candidate crosswalk using unique provenance identities, topology, distance, direction and observation epoch. Review braided, tidal, split/merged rivers and one-to-many segments explicitly; compare matches to independent surveyed observations and report errors/biases.
5. Only after original provider rights and scientific validation should a derived river-width artifact be considered for downstream hazard research. The crosswalk cannot create discharge curves, return periods, flood depths, vulnerability, insured TIV, or loss records by itself.

Remaining blockers: exact original bytes/SHA-256, licence and per-column terms, validated regional crosswalk, and a defensible link to an independent flood hazard model.
