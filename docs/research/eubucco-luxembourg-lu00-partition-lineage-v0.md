<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EUBUCCO v0.2 Luxembourg LU00 original-file lineage preflight

**Date:** 2026-11-01. **Status:** research only, no original provider bytes acquired, no CAT model input admitted.

## Exact fixed research target

- EUBUCCO v0.2 distributes NUTS2-specific Apache Parquet partitions. The provider-documented path construction yields the **candidate** object https://s3.eubucco.com/eubucco/v0.2/buildings/parquet/nuts_id=LU00/LU00.parquet . This **specific object has not been independently downloaded or checked for existence**.
- The 2016 official EU NUTS annex identifies Luxembourg **LU00** as NUTS2 and **LU000** as NUTS3. EUBUCCO uses a modified 2016 geography. Do not infer equivalence with later NUTS versions.
- The producer documents WKB footprint geometries in EPSG:3035, original building identifiers, a geometry_source field and per-attribute source fields. OSM upstream IDs have a known provider caveat: they may be sequential provider-local IDs, not original OSM IDs.
- EUBUCCO v0.2 rights are generally ODbL 1.0, with Czech Prague (CC-BY-SA) and Italian Abruzzo (CC-BY-NC) exceptions. The Luxembourg original-source lineage and licence are **not individually admitted** by this review. Separate service terms and any original source database obligations must still be checked.
- Official provider metadata reference **input-datasets-metadata.xlsx** should establish upstream Luxembourg dataset/version, retrieval dates and licences before claiming ACT2023v2 is an independent validation source.

### Primary sources

- https://docs.eubucco.com/v0.2/data-access/cli/
- https://docs.eubucco.com/v0.2/data-format/partitioning/
- https://docs.eubucco.com/v0.2/data-format/schema/
- https://docs.eubucco.com/v0.2/data-format/metadata/
- https://docs.eubucco.com/v0.2/license/
- https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R2066

## Executable local source preflight

The new research_runners/eubucco_lu00_lineage_preflight_v0.py uses **optional pinned PyArrow 20.0.0** and only **one already-acquired local Parquet file**. A full 64-character SHA-256 is required in advance. The tool reads the bounded original bytes exactly once and parses that same in-memory snapshot. Hard limits: 256 MiB, 2 million rows and 10,000 row groups. It verifies the Parquet container, required source fields, WKB binary column type, unique IDs, exact LU000 region values and decoded row count.

It emits only original-file hash/size, aggregate government/OSM/Microsoft/estimated provenance-family counts, and explicit non-admission flags. No source records, IDs, geometry bytes, coordinates, crosswalks or individual insurance data are exported. It does not establish actual geographic validity, licensing or independent ground truth. Missing optional attribute source columns are reported, never imputed.

Reproduce **after independent trusted source receipt and rights review**:

    python -m pip install pyarrow==20.0.0
    python research_runners/eubucco_lu00_lineage_preflight_v0.py --original /local/original/LU00.parquet --expected-sha256 <trusted-64-character-lowercase-hex-sha>

The placeholder is intentionally not a valid SHA-256. A digest freshly calculated from a file is reproducibility evidence, not standalone provider authenticity.

Dedicated CI executes 10 synthetic-only tests under pinned PyArrow, with no original source download; the default core suite skips the optional tests when PyArrow is absent.

## ACT 2023v2 ↔ EUBUCCO proof gates

1. Independently bind the EUBUCCO v0.2 LU00 asset, full original SHA, producer metadata version, source-specific licence and upstream source family. Existing access contract remains documented_only and this work **does not** enable source acquisition.
2. Resolve Luxembourg ACT2023v2 roof-extent versus EUBUCCO footprint semantics, exact EPSG2169 axis handling and its source ZIP/GPKG receipt in parallel PR #912.
3. Preserve EUBUCCO per-building geometry source, version, observation year, official-versus-OSM-versus-MSFT uncertainty; a government source potentially reusing ACT data is *not* independent model validation.
4. Only after original data rights and CRS proofs, calibrate existing scripts/building_footprint_overlap_v0.py on manually adjudicated urban/rural and split/merge samples. Do not automatically merge property records, classify insured exposure or calculate claims/losses from high IoU.
