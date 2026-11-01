-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0

-- RESEARCH VIEW ONLY. Sources are not model inputs, downloads, or rights-cleared.
-- Apply after the canonical GitHub landscape shards are synced as metadata-only
-- registry.source_record documents into the independent insurance-risk-core Neon DB.
-- No real building/policy/location bytes are created, copied or exposed.
-- Read-only consumers must honor exact GitHub source lineage.

CREATE VIEW research.building_source_shortlist_v0 AS
SELECT
    c.candidate_id,
    c.name AS candidate_name,
    c.provider,
    c.authoritative_url,
    c.canonical_candidate ->> 'spatial_scope' AS spatial_scope,
    c.canonical_candidate ->> 'temporal_scope' AS temporal_scope,
    c.canonical_candidate ->> 'resolution_or_granularity' AS granularity,
    c.canonical_candidate ->> 'access_class_hint' AS access_hint,
    c.categories,
    c.potential_roles,
    (c.categories ?| ARRAY['building_ids','ids','building_attributes','cadastral_buildings','building_register']) AS possible_id_or_attribute_lane,
    (c.categories ?| ARRAY['footprints','building_footprints','geometry','cadastral','buildings','building_geometry']) AS possible_footprint_lane,
    (c.categories ?| ARRAY['lidar','height','building_height','3d_geometry','building_3d','roof_shapes']) AS possible_height_lane,
    (c.categories ?| ARRAY['epc','energy_certificates','construction','material_types','building_archetypes','building_materials']) AS possible_attributes_lane,
    (c.categories ?| ARRAY['statistics','building_stock','construction_age','floor_area','heat_demand','age_distribution']) AS aggregate_only_or_modelled_lane,
    c.admission_status,
    c.rights_review_status,
    c.scientific_review_status,
    false AS model_input_ready,
    'original_asset_receipt_rights_and_scientific_review'::text AS next_evidence_gate,
    s.repo AS canonical_repo,
    s.git_path AS canonical_path,
    s.git_blob_sha AS canonical_blob_sha,
    s.git_commit_sha AS canonical_commit_sha
FROM registry.landscape_candidates c
JOIN registry.source_record s
    ON s.source_key = c.registry_document_key
WHERE s.classification = 'landscape_candidate'
  AND c.categories ?| ARRAY[
    'buildings','building_ids','ids','building_attributes','cadastral_buildings',
    'footprints','building_footprints','geometry','cadastral',
    'lidar','height','building_height','3d_geometry','building_3d','roof_shapes',
    'epc','energy_certificates','construction','construction_year','material_types',
    'building_archetypes','building_materials','building_stock','construction_age',
    'floor_area','heat_demand','age_distribution','building_samples','roof',
    'buildings_3d','addresses'
  ]
  AND c.admission_status = 'not_admitted'
  AND c.rights_review_status = 'not_reviewed'
  AND c.scientific_review_status = 'not_reviewed'
  AND s.admissible_for_raw = false;
