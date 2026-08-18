<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: manifests/copernicus.cems.glofas-historical.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Dataset manifest: `copernicus.cems.glofas-historical.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Dataset id:** copernicus.cems.glofas-historical

**Provider:** Copernicus Emergency Management Service (CEMS) / European Commission Joint Research Centre

**Product name:** River discharge and related historical data from the Global Flood Awareness System (GloFAS)

**Version or release:** `null`

**Canonical source:** <https://ewds.climate.copernicus.eu/datasets/cems-glofas-historical>

**Retrieved at:** 2026-08-10T01:04:00Z

**Retrieval query or filters:** Metadata-only review of DOI 10.24381/cds.a4fdd6b9. No EWDS request was submitted and no data files were acquired. The catalogue is rolling; a future raw proposal must freeze the complete request, returned files and byte hashes.

**Access class:** registration_required

**Modelling layer:** hazard

**Intended use:** Global/regional modelled hydrological-history source for river-discharge research, transparent event-detection experiments and comparison with independently admitted flood/hydraulic products. Discharge and related hydrological variables are not direct gauge observations, inundation depth/extent, vulnerability, insured loss or a stochastic event set.

**Raw artifact:** `null`

**Derived artifact:** `null`

## Licensing

**Status:** verified

**Spdx expression:** `null`

**Licence name:** CEMS-FLOODS datasets licence (rev. 1)

**Terms reference:** <https://cds.climate.copernicus.eu/licences/cems-floods>

**Terms reviewed at:** 2026-08-10T01:04:00Z

**Terms version or date:** CEMS-FLOODS datasets licence rev. 1; reviewed 2026-08-10

**Terms content sha256:** `null`

**Commercial use status:** allowed

**Attribution requirements:** When distributing CEMS EFAS/GloFAS data, identify the source using the CEMS notice required by the licence; when data are adapted or modified, use the corresponding modified-information notice or a materially equivalent notice.

**Share alike or derivative requirements:** The CEMS-FLOODS licence permits adaptation, modification and combination; no share-alike requirement is recorded. Required source/modification notices and all other licence conditions still apply.

**Notes:** The reviewed historical GloFAS catalogue entry points to the CEMS-FLOODS licence. The licence permits reproduction, distribution, public communication, adaptation, modification and combination. Some other CEMS data can be restricted, so rights are not generalized beyond this exact catalogue entry. This is an engineering rights assessment, not legal advice.

## Redistribution

**Status:** allowed

**Scope:** raw

**Conditions:** Source rights can support redistribution of the covered GloFAS product under the CEMS-FLOODS licence and its required notices. This manifest records repository review status approved_metadata_only. At the manifest review time, no exact EWDS request or returned artifact had been selected, acquired, hashed or approved for Git publication.

## Privacy

**Personal data status:** none

**Confidential or proprietary status:** none

**Notes:** The reviewed product is a publicly catalogued gridded hydrological model-data product, not a person-, customer-, policy-, claims- or portfolio-level dataset.

## Spatial

**Crs:** `null`

**Extent:** Global GloFAS domain; exact grid, CRS and selected sub-area must be taken from the exact retrieval request and returned metadata

## Temporal

**Extent:** Historical/rolling daily hydrological time series; exact requested date range and applicable system/version must be frozen per acquisition

## Variables and units

### Item 1

**Name:** river discharge in the last 24 hours

**Unit:** m3 s-1

**Description:** Modelled volume rate of river flow for the GloFAS grid; not a direct river-gauge observation.

### Item 2

**Name:** runoff water equivalent

**Unit:** kg m-2

**Description:** Modelled surface plus subsurface runoff water equivalent.

### Item 3

**Name:** snow depth water equivalent

**Unit:** kg m-2

**Description:** Modelled water-equivalent mass associated with snow.

### Item 4

**Name:** soil wetness index

**Unit:** dimensionless

**Description:** Modelled root-zone soil wetness index.


**Transformation:** `null`

## Review

**Status:** approved_metadata_only

**Reviewed at:** 2026-08-10T01:04:00Z

**Reviewer:** OpenCatastrophe source audit

**Notes:** Metadata-only engineering approval based on the exact EWDS GloFAS historical catalogue entry and CEMS-FLOODS datasets licence. Raw/derived publication remains blocked until the retrieval request, returned files, byte hashes, version/grid/time semantics, known issues and required notices are independently pinned and reviewed.
