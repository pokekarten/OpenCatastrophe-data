<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EMSN028: 2016 original observed versus estimated maximum flood at two **current** RNB reference points

**Review date:** 2026-11-01. This is **point-only, research-only source diagnostics**. Not a 2016-vintage building portfolio, an AOI04-specific observed flood extent, insured exposure, claims or admission into a CAT model.

## Evidence

The original Copernicus FileGDB is downloaded ephemerally from the [published EMSN028 ZIP](https://mapping.emergency.copernicus.eu/download/EMSN028/EMNS028_AOI_FRANCE_utm31n.gdb.zip). The full archive SHA-256 was reverified on the runner against the research pin
`7ef43d0637447abae705728723c06d2f05415a21667fdee1f10e8fc25b5bf3c2`. The fixed source is read with Fiona 1.10.1 and Shapely 2.1.2.

[Complete and successful original-source + invalid-bbox repair challenge run 41353881837](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41353881837), with [machine-readable non-admission receipt](cems-emns028-current-rnb-original-estimated-max-point-challenge-20261101.toml).

Only two public **present-day** RNB footprint centroids, derived read-only from the separate CAT-only Neon research database, were used as diagnostic points. Their original WGS84 coordinate bytes are not included in the log output or saved in this document. **The current RNB geometries do not prove that identical buildings or their footprints existed in June 2016.**

## Four-stage audit, not an insurer loss join

| Observed source or candidate | Result |
| --- | --- |
| Actual `Flooded_area` source | **1 invalid original MultiPolygon**; research-only linework repair |
| Distances from the two current points to research-repaired observed `Flooded_area` | **338.24 m and 373.35 m**, neither point inside |
| Original `Estimated_Max_Flood_Extent` | **1,237** source features |
| Valid maximum source features | **1,206**, neither point covered; nearest valid polygons **523.09 m / 589.26 m** |
| Invalid maximum source features | **31**, never assumed to be empty flood |
| Invalid-feature bounding boxes covering the two points | **1 each**; both are from **the same source feature** |
| Target invalid feature, original iteration ordinal | **1,235 zero-based** (1,236th record). Not a provider-issued feature ID |
| Target invalid geometry and error | 33,229 source coordinates; `Ring Self-intersection[496686.5675 5359323.6527]` in EPSG:32631 |
| Target invalid geometry's *bounding rectangle* | about 3,805.14 km²; not inundation area |
| In-memory `make_valid(linework)` | valid MultiPolygon; **5 parts, 144,858,199.84 m²**; covers **both** current points |
| In-memory `make_valid(structure)` | valid MultiPolygon; **5 parts, 144,858,199.84 m²**; covers **both** current points |
| Between two repairs | symmetric difference area **0.00 m²**, rounded; this does **not** prove geophysical truth |

**Finding:** Excluding the 31 invalid source polygons would have produced a false-looking negative result for both RNB points on the **estimated maximum** source. Both points are covered by the same targeted repaired invalid source polygon. Conversely, **this is not measured floodwater**: `Estimated_Max_Flood_Extent` is an estimated maximum extent, scientifically different from `Flooded_area`. Only one ambiguous invalid source feature was repaired **temporarily**; the other 30 remain invalid and were not repaired in the targeted test.

The point tests are not building-polygon intersections, satellite acquisition checks, water-depth measurements, insurer-specific exposure, per-risk policy facts, validated historical building footprints or claims. Nor does `aoi` (one broad source feature) identify an independently proven AOI04 polygon in the FileGDB. The 2016 original scene and historic buildings must still be independently verified.

## Delivered code and limits

- [Current RNB centroid vs original-source layer diagnostics](../../research_runners/cems_emns028_current_rnb_point_context_v0.py) reads the **entire** estimated layer, accounts for all valid/invalid/null features and conservatively checks bounding boxes before challenging any repaired polygon. Only an invalid polygon with a point in its bounding box is tested with both repair methods.
- [Synthetic regression tests](../../tests/test_cems_emns028_current_rnb_point_context_v0.py) cover invalid synthetic source geometries, bbox uncertainty, original/estimated distinction and mandatory non-admission flags.
- [Pinned public-source test workflow](../../.github/workflows/cems-emns028-priority-layer-semantics.yml) checks full original-archive SHA, runs offline synthetic tests before any live acquisition, and deletes all provider ZIP and extracted geodata after inspection. It does not write to Neon or save raw source polygons.
- [Existing topology comparison](../../research_runners/cems_emns028_topology_repair_challenge_v0.py) preserves a separate **observed** `Flooded_area` repair sensitivity check.

The original 2016 source-specific and third-party licence review remains open (see original file- and rights-audit). A public URL and a SHA-256 pin are **not** a commercial licence, model approval or historical flood certification.

## Next evidence gates

1. Verify original AOI04 observed flood polygon and sensor acquisition time; do not substitute the repaired activation-wide or maximum-estimated flood products.
2. Verify period-correct independent 2016 building polygons in Seine-et-Marne using the precise candidate [BD TOPO D077 March 24 2016 research PR #937](https://github.com/pokekarten/OpenCatastrophe-data/pull/937), including original bytes and product reuse rights.
3. Separate building geometry vintages from insurer ownership, occupancy, insured TIV, physical depth, event validation and vulnerability.
4. Run spatial and Monte Carlo modelling only after these stage-specific inputs have passed explicit provenance, rights and science gates.

**Live Neon status after the test:** 3 CEMS AOI04 research product rows, 0 approved original polygon geometries and 0 CAT model admissions. No Neon data were inserted or altered.
