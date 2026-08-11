<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: manifests/eiopa.catastrophe-data-hub.historical-loss.2023-12-05.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Dataset manifest: `eiopa.catastrophe-data-hub.historical-loss.2023-12-05.json`

> This Markdown file is a deterministic, lossless human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this projection does not change rights, admission, publication or scientific-review state.

```json
{
  "schema_version": "1.0.0",
  "dataset_id": "eiopa.catastrophe-data-hub.historical-loss.2023-12-05",
  "provider": "European Insurance and Occupational Pensions Authority (EIOPA)",
  "product_name": "Historical loss data - catastrophe data hub.xlsx",
  "version_or_release": "2023-12-05 public resource",
  "canonical_source": "https://www.eiopa.europa.eu/tools-and-data/catastrophe-data-hub_en",
  "retrieved_at": "2026-08-10T01:10:00Z",
  "retrieval_query_or_filters": "Metadata-only review of the EIOPA Catastrophe Data Hub historical-loss workbook listed on 2023-12-05. No XLSX bytes were acquired. Raw/derived redistribution remains unreviewed pending inspection of the exact workbook and any file-specific or third-party notices.",
  "access_class": "open",
  "modelling_layer": "observed_loss",
  "intended_use": "Public aggregated incurred-claims benchmark for selected European catastrophe events. Useful for observed insurance-loss semantics and cautious validation, but not a complete market loss history, ground-up economic loss dataset, insurer-specific claims history, or transferable vulnerability curve.",
  "raw_artifact": null,
  "derived_artifact": null,
  "licensing": {
    "status": "verified",
    "spdx_expression": null,
    "licence_name": "EIOPA website copyright/reuse notice",
    "terms_reference": "https://www.eiopa.europa.eu/legal-notice_en",
    "terms_reviewed_at": "2026-08-10T01:10:00Z",
    "terms_version_or_date": "EIOPA legal notice reviewed 2026-08-10; public resource dated 2023-12-05",
    "terms_content_sha256": null,
    "commercial_use_status": "allowed",
    "attribution_requirements": "Acknowledge EIOPA as the source as required by the EIOPA legal notice. Follow its conditions for transformed/republished material and EIOPA material incorporated into sold documents.",
    "share_alike_or_derivative_requirements": "No share-alike requirement is recorded in the general EIOPA website notice. Third-party material is excluded and must be reviewed separately.",
    "notes": "Because the workbook is based on insurer-reported claims and has not been inspected for file-specific notices, only metadata-level reuse is cleared by this review. This is an engineering rights assessment, not legal advice."
  },
  "redistribution": {
    "status": "allowed",
    "scope": "metadata_only",
    "conditions": "Only repository-authored metadata about the public EIOPA resource is cleared here. Raw or derived workbook redistribution remains blocked until exact-file and third-party rights are explicitly reviewed."
  },
  "privacy": {
    "personal_data_status": "none",
    "confidential_or_proprietary_status": "none",
    "notes": "This admission describes only EIOPA's aggregated public release. The technical description states that each displayed loss point represents at least three company-submitted values to preserve anonymity; undertaking-level submissions remain outside scope."
  },
  "spatial": {
    "crs": null,
    "extent": "European regions affected by the selected published events; exact geographic identifiers and suppression/aggregation rules require workbook review"
  },
  "temporal": {
    "extent": "Selected events: Central European flood 2013, Portugal wildfire 2017, and European windstorm Ciara/Sabine 2020; public resource dated 2023-12-05"
  },
  "variables_and_units": [
    {
      "name": "incurred claims for buildings",
      "unit": null,
      "description": "Aggregated incurred claims for building coverage; exact monetary unit and workbook field semantics require workbook review."
    },
    {
      "name": "other incurred claims",
      "unit": null,
      "description": "Aggregated incurred claims outside building coverage; EIOPA notes examples such as contents or business interruption. Exact monetary unit requires workbook review."
    }
  ],
  "transformation": null,
  "review": {
    "status": "approved_metadata_only",
    "reviewed_at": "2026-08-10T01:10:00Z",
    "reviewer": "OpenCatastrophe source audit",
    "notes": "Metadata-only approval. Raw/derived XLSX publication remains blocked pending exact-file rights, byte identity, workbook schema and unit review."
  }
}
```
