<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CAL FIRE DINS: bounded damage-observation semantics and CAT join contract (research, 2026-11-01)

**State:** research-only; neither data admission nor external-data acquisition. Canonical source candidate:
`us.calfire.dins.structure-damage` and access contract
`us.calfire.dins.postfire-feature-layer`. The access contract remains
`documented_only`, `probe_contract.mode=none`; this note grants no fetch.

## Authoritative evidence

1. Original state publication, provider, dated access, rights description and
   incomplete inspection frame:
   <https://publish.data.ca.gov/dataset/cal-fire-damage-inspection-dins-data>.
2. Exact official source-original ArcGIS layer `POSTFIRE_MASTER_DATA_SHARE`,
   item `994d3dc4569640caadbbc3198d5a3da1`, FeatureServer layer `0`:
   <https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/POSTFIRE_MASTER_DATA_SHARE/FeatureServer/0>.
3. Related source service description:
   <https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/POSTFIRE_MASTER_DATA_SHARE/FeatureServer>.

These links show public *documentation*; no original live JSON response byte
count, reproducible SHA-256, authorized feature payload or dataset snapshot has
been acquired here. The separate offline schema preflight accepts a future,
legally acquired **layer metadata JSON only**, never a feature query.

## Exact categorical mapping, not monetary damage ratios

The master ArcGIS layer declares `typeIdField=DAMAGE` and these six domain
values (do not substitute labels from an unrelated individual-fire view):

| Literal provider `DAMAGE` code | Research interpretation |
| --- | --- |
| `Destroyed (>50%)` | inspected, destroyed category |
| `Major (25-50%)` | inspected, major category |
| `Minor (10-25%)` | inspected, minor category |
| `Affected (>0-10%)` | inspected, affected category |
| `Inaccessible` | could not determine inspected damage state |
| `No Damage` | no observed damage **within the inspected frame** |

**Do not** substitute damage bands for paid loss, repair cost, building
replacement value, deductible, insured value, quantitative vulnerability ratio
or insurer claim. The service uses human inspection classifications and its
labels are not calibrated continuous financial loss percentages. Do not map
`Inaccessible` to undamaged or delete it silently from denominators.

For this specific master layer, verified field concepts include:
`OBJECTID` (technical source row ID), `GLOBALID`, `DAMAGE`,
`STRUCTURETYPE`, `INCIDENTNUM`, `INCIDENTNAME`,
`INCIDENTSTARTDATE` (ArcGIS date), `HAZARDTYPE`,
`ROOFCONSTRUCTION`, `EXTERIORSIDING`, `EAVES`, `VENTSCREEN`,
`YEARBUILT`, `ASSESSEDIMPROVEDVALUE`, `APN`, `SITEADDRESS` and
point geometry. Year built and assessed improvement values are **parcel
join** fields, not authenticated structure-level construction, replacement
cost or insurance coverage observations. Address/APN, coordinates and
inspector fields must not be committed as person-/parcel-level data.

## Time and selection bias gate

Provider service description states that the DINS digital damaged-building
records begin in **2013**, and **only damaged/destroyed structures** were
collected before **2018**. From 2018, non-damaged inspections were additionally
collected. Even from 2018, the provider warns that access and fire damage
cause missed inspections. Accordingly:

- 2013-2017: a zero `No Damage` observation means **not collected**, not
  proof that every unlisted structure was damaged and not a valid risk
  denominator. No observed damage frequency or loss rate may be estimated.
- 2018 onward: observed `No Damage` is conditioned on being inspected in the
  wildfire impact survey; it does not enumerate every geographically exposed
  structure. Never divide damaged inspections by all recorded DINS rows to
  claim an unbiased exposure-loss probability.
- No DINS record for a known building means **unknown inspection**, not
  zero damage. Event-inspection inclusion bias must be retained as a flag.
- Changes in source-year classification, reporting practices, and event scope
  must be tested before pooling across years.

## Future cross-source matching (not yet executed)

| Source pair | Proposed bounded join | Fail-closed conditions |
| --- | --- | --- |
| DINS ↔ official wildfire perimeter/incident index | Verify incident identifier, aliases, start date and the provider's event lineage; inspect point-in-buffer match in a reviewed local CRS | Never match solely on incident name or treat a post-event perimeter as observed intensity |
| DINS ↔ footprint / EUBUCCO / Overture | Spatial proximity and inspection timestamp, matching building-part vs structure semantics | No automatic nearest-neighbor match where footprints overlap, confidence is low, geometry snapshots differ or CRS differs |
| DINS ↔ LANDFIRE fuel/canopy rasters | Use a version-pinned pre-ignition fuel layer intersected with reviewed geospatial location | No temporal leakage from post-fire disturbance or future fuel maps; don't treat fuel classes as measured fire intensity |
| DINS ↔ insurer synthetic exposure / NextGen | Event-scoped *categorical inspection benchmark*, with explicit unknown/missing sample frame and unadmitted rights | **No** inferred insurance policy, loss amount, replacement value, damage ratio or commercial model admission |

## Next admissible acquisition milestone

A new, tightly bounded and **explicitly rights-reviewed** metadata-only T1
request must establish the exact source endpoint, retrieval UTC, raw
byte-length/SHA-256, media type, trusted request identity and the results of
`scripts/preflight_calfire_dins_metadata_v0.py`. Until API/service automation
terms are resolved and contract permissions upgraded, the project must not run
any feature `/query`, export, paginated crawl or address/APN retrieval.

Subsequently, choose **one** incident from 2018 onward and design a
privacy-preserving *aggregate-only* validation question based on an
independently sourced building exposure denominator and verified event
footprint. Admission, data rights, source completeness and scientific
validation remain separate gates.
