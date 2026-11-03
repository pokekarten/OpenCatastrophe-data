-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only reproducible cross-check against the independent CAT-only
-- insurance-risk-core / insurance Neon main database (SELECT only).
--
-- Eleven official GLEIF original HTTP JSON:API response receipts freshly
-- read at Golden Copy 2026-11-03T08:00:00Z. SHA-256 of exact HTTP bodies
-- (NOT of rendered text) and lengths are included; original bytes stay
-- outside Git. This is a PINNED historical source snapshot, not automatic
-- API monitoring or a claim that GLEIF never updates source relationships.
--
-- Compare only exact LEI + endpoint, declared kind, parent, exception,
-- source-report status, and RELATIONSHIP_PERIOD start with the 11 existing
-- research observations staged from two source-scoped internal research assets on 2026-10-31.
-- The earlier source-scoped research assets remain research_only/source_scoped/raw_import_allowed
-- = false. Neither original body hashes nor latest Golden Copy bytes are
-- stored in the older Neon relationship observations.
--
-- Regulated cross-border branch/passport observations are separate from
-- legal insurer entities. A foreign regulator LEI must never create an
-- additional insurer organization or insurer exposures by name similarity.
-- Legal relationships = accounting consolidation, NOT beneficial ownership,
-- supervisory group perimeter, Solvency II capital group, or CAT portfolios.
WITH official_receipts(
  child_lei, endpoint_suffix, parent_lei, relationship_kind,
  reported_status, exception_reason, original_http_sha256,
  original_http_bytes, relationship_period_start
) AS (
 VALUES
  ('529900UCN37OZCXGVW88', 'direct-parent-relationship', '529900KIN5BE45V5KB18', 'DIRECT_ACCOUNTING_CONSOLIDATION', 'ACTIVE', NULL, 'fb9787df6ecb6761ea28b35158f15fe7ac16b9be206a09bd4ef9e7eb37d38cf5', 1295, '2018-02-15T23:00:00Z'),
  ('529900KIN5BE45V5KB18', 'direct-parent-relationship', '5299006ZIILJ6VJVSJ32', 'DIRECT_ACCOUNTING_CONSOLIDATION', 'ACTIVE', NULL, '40d09bfeb68c37e27d1f78d07c9dc5a6e94148e7d03a998fdbd40f7a874b8499', 1295, '2024-01-11T23:00:00Z'),
  ('5299006ZIILJ6VJVSJ32', 'direct-parent-relationship', '529900F2F9VZ5FRROH89', 'DIRECT_ACCOUNTING_CONSOLIDATION', 'ACTIVE', NULL, 'fdc53e938542980e3915784fe5c197c9644e090347bfae5aa2856cfe28547611', 1296, '2017-09-17T22:00:00Z'),
  ('529900KIN5BE45V5KB18', 'ultimate-parent-relationship', '529900F2F9VZ5FRROH89', 'ULTIMATE_ACCOUNTING_CONSOLIDATION', 'ACTIVE', NULL, 'f6d69a570ade5258ed6c98ab78b36cab96af78040d037ac95be8d5868b5aea8b', 1299, '2024-01-11T23:00:00Z'),
  ('529900UCN37OZCXGVW88', 'ultimate-parent-relationship', '529900F2F9VZ5FRROH89', 'ULTIMATE_ACCOUNTING_CONSOLIDATION', 'ACTIVE', NULL, 'b750d625adc41d665f17f6f6c4a4fe8a32c0e6774e17601757c8a8c7c5594c21', 1299, '2018-02-15T23:00:00Z'),
  ('969500VV8Y4PQ7XJWE02', 'direct-parent-relationship', 'F240A7PWJB2BLKELB442', 'DIRECT_ACCOUNTING_CONSOLIDATION', 'ACTIVE', NULL, 'b70f1f72dd6734e99001491d0899b8d4ee3877ee6a6d8be2e2d2998977db225d', 1361, '2008-12-18T23:00:00Z'),
  ('969500VV8Y4PQ7XJWE02', 'ultimate-parent-relationship', '529900K9B0N5BT694847', 'ULTIMATE_ACCOUNTING_CONSOLIDATION', 'ACTIVE', NULL, '337388e1394038eb5a2c36b8aa3440add66da98f5030649ece387aef3e24c5eb', 1365, '2004-12-31T23:00:00Z'),
  ('F240A7PWJB2BLKELB442', 'direct-parent-relationship', '529900K9B0N5BT694847', 'DIRECT_ACCOUNTING_CONSOLIDATION', 'ACTIVE', NULL, '5231655c385e79f8f0367f222f0041ca398ed26bf54d973e04acd7b06eb36ade', 1295, '2018-04-02T22:00:00Z'),
  ('F240A7PWJB2BLKELB442', 'ultimate-parent-relationship', '529900K9B0N5BT694847', 'ULTIMATE_ACCOUNTING_CONSOLIDATION', 'ACTIVE', NULL, 'ea55cc7b01b16102e29f625eaf9100a9f4cae68d16637c7b4898431733b54dd8', 1299, '2018-04-02T22:00:00Z'),
  ('529900MUF4C20K50JS49', 'direct-parent-reporting-exception', NULL, 'PARENT_REPORTING_EXCEPTION', 'REPORTED', 'NO_KNOWN_PERSON', '6af504fd9a84a42bffd4ba3f2be263821259a3dd08af79f194dcc76b73c50893', 531, NULL),
  ('549300KCPG3666EE4546', 'direct-parent-reporting-exception', NULL, 'PARENT_REPORTING_EXCEPTION', 'REPORTED', 'NON_CONSOLIDATING', '55bb6867207c8b645af0ae43c0b3ee8a88754b0ae168adaf6807ceac215ff884', 533, NULL)
), snapshot AS (
 SELECT *,
   'https://api.gleif.org/api/v1/lei-records/' || child_lei
     || '/' || endpoint_suffix AS source_url,
   '2026-11-03T08:00:00Z'::text AS golden_copy_published
 FROM official_receipts
), evidence AS (
 SELECT s.*,
   obs.observation_count,obs.source_asset_id,obs.last_ingested_at,
   obs.key_fields_match,obs.relationship_period_match,
   a.evidence_status AS source_asset_evidence_status,
   a.rights_status AS source_asset_rights_status,
   a.raw_import_allowed AS source_asset_raw_import_allowed,
   coalesce(child_legal.n,0) AS verified_legal_child_count,
   coalesce(parent_legal.n,0) AS verified_legal_parent_count,
   child_legal.legal_name AS verified_child_name,
   parent_legal.legal_name AS verified_parent_name,
   coalesce(branch.n,0) AS matching_foreign_branch_count,
   branch.branch_country,branch.branch_semantics,branch.branch_head_lei,
   coalesce(head_legal.n,0) AS verified_branch_head_count,
   feed.rights_status AS gleif_feed_rights_status,
   feed.automated_import_allowed AS gleif_feed_automated_import_allowed
 FROM snapshot s
 LEFT JOIN LATERAL (
   SELECT count(*) AS observation_count,
       min(o.source_asset_id) AS source_asset_id,
       max(o.ingested_at) AS last_ingested_at,
       bool_and(
         o.parent_identifier_value IS NOT DISTINCT FROM s.parent_lei
         AND o.relation_kind=s.relationship_kind
         AND o.reported_status=s.reported_status
         AND o.exception_reason IS NOT DISTINCT FROM s.exception_reason
       ) AS key_fields_match,
       bool_and(
         (SELECT p->>'startDate'
          FROM jsonb_array_elements(o.periods) AS p
          WHERE p->>'type'='RELATIONSHIP_PERIOD' LIMIT 1)
         IS NOT DISTINCT FROM s.relationship_period_start
       ) AS relationship_period_match
   FROM entity.relationship_observation o
   WHERE o.child_identifier_scheme='GLEIF_LEI'
     AND o.child_identifier_value=s.child_lei
     AND o.source_uri=s.source_url
 ) obs ON true
 LEFT JOIN registry.repository_asset a ON a.asset_id=obs.source_asset_id
 LEFT JOIN LATERAL (
   SELECT count(*) AS n, min(o.legal_name) AS legal_name
   FROM entity.organization_identifier i
   JOIN entity.organization o ON o.organization_id=i.organization_id
   WHERE i.identifier_scheme='GLEIF_LEI' AND i.is_verified IS TRUE
     AND i.identifier_value=s.child_lei AND o.identity_status='verified'
 ) child_legal ON true
 LEFT JOIN LATERAL (
   SELECT count(*) AS n, min(o.legal_name) AS legal_name
   FROM entity.organization_identifier i
   JOIN entity.organization o ON o.organization_id=i.organization_id
   WHERE i.identifier_scheme='GLEIF_LEI' AND i.is_verified IS TRUE
     AND i.identifier_value=s.parent_lei AND o.identity_status='verified'
 ) parent_legal ON true
 LEFT JOIN LATERAL (
   SELECT count(*) AS n, min(b.regulator_country::text) AS branch_country,
          min(b.relation_semantics) AS branch_semantics,
          min(b.primary_head_office_lei) AS branch_head_lei
   FROM entity.foreign_branch_observation b
   WHERE b.observed_branch_lei=s.child_lei
     AND b.observed_lei_registration_status='ISSUED'
 ) branch ON true
 LEFT JOIN LATERAL (
   SELECT count(*) AS n
   FROM entity.organization_identifier i
   JOIN entity.organization o ON o.organization_id=i.organization_id
   WHERE i.identifier_scheme='GLEIF_LEI' AND i.is_verified IS TRUE
     AND i.identifier_value=branch.branch_head_lei
     AND o.identity_status='verified'
 ) head_legal ON true
 LEFT JOIN registry.entity_feed feed ON feed.feed_id='gleif_global'
)
SELECT child_lei, endpoint_suffix, relationship_kind, parent_lei,
       exception_reason, source_url, golden_copy_published,
       original_http_sha256,original_http_bytes,
       relationship_period_start,observation_count,key_fields_match,
       relationship_period_match,last_ingested_at,
       source_asset_id,source_asset_evidence_status,
       source_asset_rights_status,source_asset_raw_import_allowed,
       verified_legal_child_count,verified_legal_parent_count,
       verified_child_name,verified_parent_name,
       matching_foreign_branch_count,branch_country,
       branch_semantics,branch_head_lei,verified_branch_head_count,
       gleif_feed_rights_status,gleif_feed_automated_import_allowed,
 CASE
   WHEN observation_count <> 1
     THEN 'BLOCKED_RESEARCH_OBSERVATION_MISSING_OR_DUPLICATE'
   WHEN key_fields_match IS DISTINCT FROM TRUE
     THEN 'BLOCKED_RESEARCH_OBSERVATION_CONTRADICTS_OFFICIAL_SOURCE'
   WHEN relationship_period_match IS DISTINCT FROM TRUE
     THEN 'BLOCKED_RELATIONSHIP_PERIOD_MISMATCH'
   WHEN relationship_kind='PARENT_REPORTING_EXCEPTION'
     THEN 'GLEIF_EXPLICIT_EXCEPTION_NO_PARENT_EDGE'
   WHEN verified_legal_child_count=1 AND verified_legal_parent_count=1
     THEN 'RESEARCH_VERIFIED_LEI_PAIR_RIGHTS_HOLD'
   WHEN verified_legal_child_count=0
     AND matching_foreign_branch_count=1
     AND branch_country='FR'
     AND branch_semantics='eu_inward_passport'
     AND verified_branch_head_count=1
     AND verified_legal_parent_count=1
     THEN 'RESEARCH_FR_PASSPORT_BRANCH_NOT_DISTINCT_LEGAL_INSURER'
   ELSE 'BLOCKED_MISSING_OR_AMBIGUOUS_LEGAL_OR_BRANCH_IDENTITY'
 END AS identity_disposition,
 false AS authorized_to_materialize,
 false AS approved_regulatory_group_membership,
 false AS approved_equity_ownership,
 false AS neon_written,
 false AS model_input_approved
FROM evidence
ORDER BY child_lei,endpoint_suffix;
