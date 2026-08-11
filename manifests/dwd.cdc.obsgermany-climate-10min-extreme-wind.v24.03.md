<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: manifests/dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Dataset manifest: `dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03.json`

> This Markdown file is a deterministic, lossless human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this projection does not change rights, admission, publication or scientific-review state.

```json
{
  "schema_version": "1.0.0",
  "dataset_id": "dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03",
  "provider": "Deutscher Wetterdienst (DWD)",
  "product_name": "10-minute station observations of extreme wind for Germany",
  "version_or_release": "v24.03",
  "canonical_source": "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/",
  "retrieved_at": "2026-08-09T18:35:00Z",
  "retrieval_query_or_filters": "Metadata-only source review. Historical quality-controlled files are the intended first research subset; no station subset or source bytes have been acquired yet.",
  "access_class": "open",
  "modelling_layer": "hazard",
  "intended_use": "Public observational evidence for validation and later calibration research in a bounded Germany wind-hazard pilot. This source is not by itself a spatially complete catastrophe event set or production hazard model.",
  "raw_artifact": null,
  "derived_artifact": null,
  "licensing": {
    "status": "verified",
    "spdx_expression": "CC-BY-4.0",
    "licence_name": "Creative Commons Attribution 4.0 International",
    "terms_reference": "https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf",
    "terms_reviewed_at": "2026-08-09T18:35:00Z",
    "terms_version_or_date": "CDC Terms of use: May 2024; dataset description version v24.03; reviewed 2026-08-09",
    "terms_content_sha256": null,
    "commercial_use_status": "allowed",
    "attribution_requirements": "Credit Deutscher Wetterdienst (DWD) as source, comply with CC BY 4.0 attribution, and follow DWD source-notice guidance; indicate modifications where applicable.",
    "share_alike_or_derivative_requirements": "CC BY 4.0 permits adaptation without a share-alike requirement; attribution and indication of changes remain required.",
    "notes": "The source-specific DWD dataset description states that CC BY 4.0 applies and points users to the CDC terms of use. The CDC Open Data directory exposes Terms_of_use.pdf with status May 2024, which states that CC BY 4.0 applies; current DWD Open Data FAQ and legal notices independently confirm reuse of freely accessible DWD geodata under CC BY 4.0 with source attribution. terms_content_sha256 remains null until the exact raw terms bytes can be acquired and hashed in an acceptance environment; no hash is inferred from rendered/search text. This review is an engineering rights assessment, not legal advice."
  },
  "redistribution": {
    "status": "allowed",
    "scope": "raw",
    "conditions": "Subject to CC BY 4.0 and DWD source-attribution requirements. This records the source-rights ceiling only; OpenCatastrophe has not approved or identified any raw artifact yet."
  },
  "privacy": {
    "personal_data_status": "none",
    "confidential_or_proprietary_status": "none",
    "notes": "The admitted source metadata describes publicly available meteorological station observations. The DWD dataset description applies CC BY 4.0 to the product, including observations originating from DWD and legally/qualitatively equivalent partner networks."
  },
  "spatial": {
    "crs": "EPSG:4326",
    "extent": "Meteorological stations in Germany"
  },
  "temporal": {
    "extent": "1989-07-03 onward according to dataset description v24.03; historical files are versioned and quality-controlled, while recent/now data are mutable and not fully quality-controlled."
  },
  "variables_and_units": [
    {
      "name": "FX_10",
      "unit": "m/s",
      "description": "Maximum wind speed observed during the preceding 10-minute interval."
    },
    {
      "name": "FNX_10",
      "unit": "m/s",
      "description": "Minimum wind speed observed during the preceding 10-minute interval."
    },
    {
      "name": "FMX_10",
      "unit": "m/s",
      "description": "Maximum derived from one-minute mean wind speeds based on three-second maxima within the preceding 10 minutes."
    },
    {
      "name": "DX_10",
      "unit": "degree",
      "description": "Wind direction associated with the maximum wind speed in the preceding 10-minute interval."
    }
  ],
  "transformation": null,
  "review": {
    "status": "approved_metadata_only",
    "reviewed_at": "2026-08-09T18:35:00Z",
    "reviewer": "OpenCatastrophe source audit",
    "notes": "Metadata-only engineering approval based on the authoritative DWD dataset description, CDC source-specific terms of use, and current DWD legal/Open Data pages. No DWD source ZIP has been committed, acquired into an OpenCatastrophe artifact identity, or approved for repository publication. Raw/derived publication remains blocked pending exact artifact identity and explicit narrower asset review."
  }
}
```
