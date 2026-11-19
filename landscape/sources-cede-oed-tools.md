<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-cede-oed-tools.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-cede-oed-tools.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-02`  
**Purpose:** Non-admission discovery registry of reusable Oasis CEDE-to-OED exposure interoperability tools and explicit source/target version boundaries.

**Entries:** 2

## ODS Tools ODTF CEDE-to-OED location and account mapping examples

**Candidate ID:** `oasis.odstools.cede-oed.transform.2026`  
**Provider:** Oasis Loss Modelling Framework (OasisLMF)  
**Categories:** `interoperability`, `exposure`, `oed`, `cede`, `open_source`, `transformation`  
**Spatial scope:** Format translation across geographic markets; example mappings contain regional code assumptions  
**Temporal scope:** public ODS Tools main inspected 2026-11-02; embedded mapping headers state CEDE v10.0.0 to OED v3.0.2  
**Resolution / granularity:** YAML location mapping (80,867 characters) and account mapping (8,195 characters); associated CSV and MS SQL Server example configurations  
**Potential roles:** `cede10_oed302_reference_mapping`, `transformation_gap_analysis`, `synthetic_interop_validation`  
**Access hint:** `public_bsd3_code_example_version_gapped_for_cede13`  
**Authoritative source:** <https://github.com/OasisLMF/ODS_Tools/tree/main/ods_tools/odtf/examples/oed-cede>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Current mapping header explicitly specifies AIR CEDE database v10.0.0 and OED v3.0.2, NOT CEDE 13.0. Location mapping SHA b5433d6bc7f5ecd926fba4899dc12245d9b1e64a and account mapping SHA 81a0f2e0aab4d140e8dd403f16ebd12d42d804c8 at observation. Requires explicit semantic version gate, compatibility diff and lossiness audit before CEDE 13 output claims. No actual insurance data is provided or admitted.

## OpenDataTransform AIR CEDE-to-OED transformation framework (legacy reference)

**Candidate ID:** `oasis.opendatatransform.air-oed.legacy`  
**Provider:** Oasis Loss Modelling Framework (OasisLMF)  
**Categories:** `interoperability`, `exposure`, `oed`, `cede`, `open_source`, `legacy`  
**Spatial scope:** Exposure format conversion; supported location and code scopes depend on individual mapping files  
**Temporal scope:** public project inspected 2026-11-02; documented AIR mapping refers to older CEDE v8  
**Resolution / granularity:** BSD-3-Clause Python transformation framework with AIR/OED location and modifier mappings; earlier converter lineage  
**Potential roles:** `historical_cede_mapping_provenance`, `odi_mapping_validation_reference`, `version_migration_research`  
**Access hint:** `public_open_source_conversion_code_not_vendor_model_data`  
**Authoritative source:** <https://github.com/OasisLMF/OpenDataTransform>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** README identifies AIR↔OED transformation as partially developed, with CEDE v8 model reference. Newer ODS Tools embeds CEDE v10/OED v3.0.2 examples. Do not infer CEDE v13 mapping completeness from this legacy status or confuse conversion code with rights to proprietary AIR model/event datasets.
