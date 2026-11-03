-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only research preflight over the EXISTING GLEIF Level-2 observations
-- in independent CAT-only Neon insurance main, not an ETL or schema migration.
-- Source original-byte receipts live in the independently pinned
-- gleif11_original_http_neon_branch_readonly_20261103.sql contract.
-- The research records here are previously staged, NOT currently authorised
-- source ingests. This query never fetches provider bytes, writes tables,
-- invents effective dates, asserts legal equity or approves CAT exposures.
--
-- GLEIF RELATIONSHIP_PERIOD != ACCOUNTING_PERIOD != DOCUMENT_FILING_PERIOD.
-- Publication / observation time != relationship start; DATE-only consumer
-- effective_from columns cannot preserve source's timezone-aware timestamp.
-- Reporting exceptions are not edges; international branch/passport
-- registration must not create an additional legally independent insurer.
--
-- Read-only scope is bounded to existing two internal research asset IDs;
-- do not reveal private source paths or raw source records in the output.
WITH research_observations AS (
 SELECT r.child_identifier_value AS child_lei,
        r.parent_identifier_value AS parent_lei,
        r.relation_kind,r.reported_status,r.exception_reason,
        r.source_uri,r.source_asset_id,r.source_record_key,
        r.ingested_at,r.periods,
        a.evidence_status AS source_evidence_status,
        a.rights_status AS source_rights_status,
        a.raw_import_allowed AS source_raw_import_allowed
 FROM entity.relationship_observation r
 JOIN registry.repository_asset a ON a.asset_id=r.source_asset_id
 WHERE r.child_identifier_scheme='GLEIF_LEI'
   AND r.source_asset_id IN (21,28)
   AND r.source_uri LIKE 'https://api.gleif.org/api/v1/lei-records/%'
), staged AS (
 SELECT r.*,
        period.n_relationship,
        period.n_accounting,
        period.n_filing,
        period.relationship_start,
        period.relationship_end,
        period.accounting_start,
        period.accounting_end,
        period.filing_start,
        child.cnt AS verified_child_leis,
        parent.cnt AS verified_parent_leis,
        child.org_id AS verified_child_org_id,
        parent.org_id AS verified_parent_org_id,
        child.legal_name AS verified_child_name,
        parent.legal_name AS verified_parent_name,
        branches.n AS foreign_branch_observations,
        branches.head_lei AS declared_branch_head_lei,
        branches.branch_semantics,
        branches.country AS branch_regulator_country,
        branches.source_raw_import_allowed AS branch_source_raw_import_allowed,
        branch_head.cnt AS verified_branch_head_leis,
        feed.rights_status AS gleif_rights_status,
        feed.automated_import_allowed AS gleif_automated_import_allowed
 FROM research_observations r
 CROSS JOIN LATERAL (
   SELECT
     count(*) FILTER (WHERE p->>'type'='RELATIONSHIP_PERIOD') AS n_relationship,
     count(*) FILTER (WHERE p->>'type'='ACCOUNTING_PERIOD') AS n_accounting,
     count(*) FILTER (WHERE p->>'type'='DOCUMENT_FILING_PERIOD') AS n_filing,
     min((p->>'startDate')::timestamptz) FILTER
       (WHERE p->>'type'='RELATIONSHIP_PERIOD') AS relationship_start,
     min(NULLIF(p->>'endDate','')::timestamptz) FILTER
       (WHERE p->>'type'='RELATIONSHIP_PERIOD') AS relationship_end,
     min((p->>'startDate')::timestamptz) FILTER
       (WHERE p->>'type'='ACCOUNTING_PERIOD') AS accounting_start,
     min(NULLIF(p->>'endDate','')::timestamptz) FILTER
       (WHERE p->>'type'='ACCOUNTING_PERIOD') AS accounting_end,
     min((p->>'startDate')::timestamptz) FILTER
       (WHERE p->>'type'='DOCUMENT_FILING_PERIOD') AS filing_start
   FROM jsonb_array_elements(r.periods) p
 ) period
 CROSS JOIN LATERAL (
   SELECT count(*) AS cnt, min(o.organization_id::text) AS org_id,
          min(o.legal_name) AS legal_name
   FROM entity.organization_identifier i
   JOIN entity.organization o ON o.organization_id=i.organization_id
   WHERE i.identifier_scheme='GLEIF_LEI' AND i.is_verified IS TRUE
     AND i.identifier_value=r.child_lei AND o.identity_status='verified'
 ) child
 CROSS JOIN LATERAL (
   SELECT count(*) AS cnt, min(o.organization_id::text) AS org_id,
          min(o.legal_name) AS legal_name
   FROM entity.organization_identifier i
   JOIN entity.organization o ON o.organization_id=i.organization_id
   WHERE i.identifier_scheme='GLEIF_LEI' AND i.is_verified IS TRUE
     AND i.identifier_value=r.parent_lei AND o.identity_status='verified'
 ) parent
 CROSS JOIN LATERAL (
   SELECT count(*) AS n, min(b.primary_head_office_lei) AS head_lei,
          min(b.relation_semantics) AS branch_semantics,
          min(b.regulator_country::text) AS country,
          bool_and(a.raw_import_allowed) AS source_raw_import_allowed
   FROM entity.foreign_branch_observation b
   JOIN registry.repository_asset a ON a.asset_id=b.source_asset_id
   WHERE b.observed_branch_lei=r.child_lei
     AND b.observed_lei_registration_status='ISSUED'
 ) branches
 CROSS JOIN LATERAL (
   SELECT count(*) AS cnt
   FROM entity.organization_identifier i
   JOIN entity.organization o ON o.organization_id=i.organization_id
   WHERE i.identifier_scheme='GLEIF_LEI' AND i.is_verified IS TRUE
     AND i.identifier_value=branches.head_lei AND o.identity_status='verified'
 ) branch_head
 JOIN registry.entity_feed feed ON feed.feed_id='gleif_global'
)
SELECT child_lei,parent_lei,relation_kind,reported_status,exception_reason,
       source_uri,source_asset_id,ingested_at,
       n_relationship,n_accounting,n_filing,
       relationship_start,relationship_end,accounting_start,
       accounting_end,filing_start,
       verified_child_leis,verified_parent_leis,
       verified_child_org_id,verified_parent_org_id,
       verified_child_name,verified_parent_name,
       foreign_branch_observations,declared_branch_head_lei,
       branch_semantics,branch_regulator_country,
       verified_branch_head_leis,
       source_evidence_status,source_rights_status,
       source_raw_import_allowed,branch_source_raw_import_allowed,
       gleif_rights_status,gleif_automated_import_allowed,
 CASE
   WHEN relation_kind='PARENT_REPORTING_EXCEPTION'
     AND parent_lei IS NULL AND exception_reason IS NOT NULL
     THEN 'NO_EDGE_REPORTED_EXCEPTION'
   WHEN relation_kind='PARENT_REPORTING_EXCEPTION'
     OR reported_status<>'ACTIVE' OR parent_lei IS NULL
     OR n_relationship<>1 OR relationship_start IS NULL
     OR (relationship_end IS NOT NULL AND relationship_end<relationship_start)
     THEN 'BLOCKED_INVALID_RELATIONSHIP_SOURCE_PERIOD'
   WHEN verified_child_leis=0 AND foreign_branch_observations=1
     AND branch_regulator_country='FR'
     AND branch_semantics='eu_inward_passport'
     AND verified_branch_head_leis=1 AND verified_parent_leis=1
     THEN 'BRANCH_NOT_A_SECOND_LEGAL_INSURER'
   WHEN verified_child_leis<>1 OR verified_parent_leis<>1
     OR verified_child_org_id=verified_parent_org_id
     THEN 'BLOCKED_NOT_EXACTLY_TWO_DISTINCT_VERIFIED_LEGAL_ENTITIES'
   WHEN n_accounting<>1 OR accounting_start IS NULL
     OR accounting_end IS NULL OR accounting_end<accounting_start
     THEN 'REVIEW_LEGAL_EDGE_MISSING_COMPLETE_ACCOUNTING_PERIOD'
   WHEN n_filing<>1 OR filing_start IS NULL
     THEN 'REVIEW_LEGAL_EDGE_MISSING_FILING_PERIOD'
   WHEN source_raw_import_allowed IS DISTINCT FROM TRUE
     OR gleif_automated_import_allowed IS DISTINCT FROM TRUE
     THEN 'REVIEW_LEGAL_EDGE_EXACT_PERIODS_BUT_IMPORT_NOT_AUTHORIZED'
   ELSE 'REVIEW_LEGAL_EDGE_REQUIRES_MANUAL_SEMANTIC_APPROVAL'
 END AS research_review_bucket,
 'GLEIF_ACCOUNTING_CONSOLIDATION_ONLY'::text AS relationship_semantics,
 false AS safe_to_coerce_source_timestamp_into_date_only_effective_from,
 false AS legal_equity_ownership_proven,
 false AS regulatory_insurer_group_membership_proven,
 false AS materialization_authorized,
 false AS neon_written,
 false AS nextgen_cat_exposure_admitted
FROM staged
ORDER BY child_lei,relation_kind
LIMIT 100;
