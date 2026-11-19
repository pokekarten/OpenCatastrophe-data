<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Global Dam Watch v1.0 — alternate original Geodatabase quality check

**Review:** 2026-11-04. This is source-quality research, never publication
of original GIS features or CAT-model data admission.

## Source basis and rationale

The exact original Shapefile ZIP (GDW_v1_0_shp.zip, file 47913754) has
been independently hashed and structurally reviewed:
https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41885048219.
The original GEOS topology audit:
https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41887835566
found 35,074 valid and **221 GEOS-invalid** original reservoir polygons,
all in the ring_self_intersection family, among 35,295 source reservoirs.
Its original ZIP SHA-256 is
2fe0b367ed3fcfb299160cd9652b16a8a19338951026ee2ac91edfebf1f3b7ae.

**That does not prove** the other original GIS representation has
the same topology. Frozen public Figshare v1 original metadata
https://api.figshare.com/v2/articles/25988293/versions/1
lists the alternate GDW_v1_0_gdb.zip, file **47913742**,
**57,476,758 bytes**, provider MD5
410d1ed16312ac613975fd092c193c65.

## Explicitly bounded original source procedure

The new isolated read-only runner
research_runners/gdw_v1_original_filegdb_quality_v0.py
checks original ZIP length/MD5 and computes original SHA-256; rejects
unsafe/traversal ZIP members, symlinks, duplicates, encryption,
unsupported formats and expansion beyond 1 GiB. Bounded streaming
extraction occurs only inside an ephemeral private temporary folder.
Pinned Fiona 1.10.1 OpenFileGDB + Shapely 2.1.2 GEOS read two original
layers; the folder is automatically deleted.

Fail-closed source checks require original GDW_ID, WGS 84, exactly
41,145 barrier points, 35,295 reservoir polygons and 5,850 legitimate
point-only barrier records. The GDB-native polygon validity and coarse
GEOS reason families are counted. Barrier containment is measured
inside valid matched polygons only.

The GitHub workflow
.github/workflows/gdw-v1-original-filegdb-quality.yml
executes only synthetic tests during pull-request review. An exact
reviewed main-branch workflow push executes a single bounded anonymous
HTTPS GET of the original file https://ndownloader.figshare.com/files/47913742
to RUNNER_TEMP, then runs the aggregate-only source audit and removes
the file. No source coordinates, IDs, geometries, original archives,
signed URLs or records are placed in Git or workflow artifacts.

## Scientific and rights caveats

A GDB-only profile can compare *aggregate* native validity counts but
not automatically determine overlap of individual invalid GDW_IDs
between formats. A source-only per-ID concordance audit is a possible
subsequent step. GDW itself remains a curated reservoir/barrier inventory,
not an independently validated hydraulic inundation, insured exposure,
dam breach frequency or loss calibration source.

Never automatically repair, buffer, snap, impute or treat invalid source
polygons as model-admitted; never infer missing-value sentinels as
measured zero. The final v1 technical document identifies CC BY 4.0
and asks that the entire unmodified original not be mirrored elsewhere
without author permission. The original ZIP is not republished.
