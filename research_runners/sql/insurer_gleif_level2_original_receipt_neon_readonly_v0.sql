-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only, exact-LEI reconciliation of FIVE GLEIF Level-2 ORIGINAL HTTP
-- response receipts captured with the official GLEIF API on 2026-11-03.
-- Source GOLDEN COPY publish date for each was 2026-11-03T00:00:00Z.
--
-- The SHA-256 values below are for the source HTTP response bytes, not
-- browser-rendered text; response bytes are not committed to Git. They were
-- inspected directly, independently of local group_hint strings.
-- Only GLEIF ACCOUNTING CONSOLIDATION (not beneficial ownership), and
-- exact reporting exceptions are evidenced. No Neon writes or admissions.
-- This query is a manually pinned research snapshot, not a live API check.
--
-- Reconfirm source bytes/status/terms before any authorised relationship
-- materialisation; `registry.entity_feed.gleif_global` currently has
-- `automated_import_allowed=false`.
WITH gleif_original_receipts(
  child_lei, parent_lei, record_kind, reporting_exception,
  original_sha256, response_bytes, source_url, golden_copy_published
) AS (
  VALUES
    ('529900UCN37OZCXGVW88','529900KIN5BE45V5KB18',
     'IS_DIRECTLY_CONSOLIDATED_BY',NULL,
     '88a2204b3721a1916b36a1f0df390c8b7a5c0c1ca5551abb1194bd7e1017af9c',1295,
     'https://api.gleif.org/api/v1/lei-records/529900UCN37OZCXGVW88/direct-parent-relationship',
     '2026-11-03T00:00:00Z'),
    ('529900KIN5BE45V5KB18','5299006ZIILJ6VJVSJ32',
     'IS_DIRECTLY_CONSOLIDATED_BY',NULL,
     '2ecb0188bd2ef2ebb2f8cfeed757fffc17e29e81638b4910f1bde8eb12b89653',1295,
     'https://api.gleif.org/api/v1/lei-records/529900KIN5BE45V5KB18/direct-parent-relationship',
     '2026-11-03T00:00:00Z'),
    ('5299006ZIILJ6VJVSJ32','529900F2F9VZ5FRROH89',
     'IS_DIRECTLY_CONSOLIDATED_BY',NULL,
     '533b8e18d880e84e4922e03e0f59a0c8966ac452c85c6a8ae6326d3e72a8ac23',1296,
     'https://api.gleif.org/api/v1/lei-records/5299006ZIILJ6VJVSJ32/direct-parent-relationship',
     '2026-11-03T00:00:00Z'),
    ('529900MUF4C20K50JS49',NULL,
     'DIRECT_ACCOUNTING_CONSOLIDATION_PARENT_EXCEPTION','NO_KNOWN_PERSON',
     'df25b9584023978cb55ac6386d71e35ecd32a0071940453992fed961425008de',531,
     'https://api.gleif.org/api/v1/lei-records/529900MUF4C20K50JS49/direct-parent-reporting-exception',
     '2026-11-03T00:00:00Z'),
    ('549300KCPG3666EE4546',NULL,
     'DIRECT_ACCOUNTING_CONSOLIDATION_PARENT_EXCEPTION','NON_CONSOLIDATING',
     'a45bc039db8eae386f59bae7a570eacc562e6c4c14bb87882d85e44a20b2c84c',533,
     'https://api.gleif.org/api/v1/lei-records/549300KCPG3666EE4546/direct-parent-reporting-exception',
     '2026-11-03T00:00:00Z')
), legal_identity_check AS (
 SELECT
   r.*,
   child_match.n AS child_verified_matches,
   child_match.org_id AS child_organization_id,
   child_match.legal_name AS child_legal_name,
   parent_match.n AS parent_verified_matches,
   parent_match.org_id AS parent_organization_id,
   parent_match.legal_name AS parent_legal_name
 FROM gleif_original_receipts r
 LEFT JOIN LATERAL (
   SELECT count(*) AS n, min(o.organization_id::text) AS org_id,
          min(o.legal_name) AS legal_name
   FROM entity.organization_identifier i
   JOIN entity.organization o ON o.organization_id = i.organization_id
   WHERE i.identifier_scheme = 'GLEIF_LEI' AND i.is_verified IS TRUE
     AND i.identifier_value = r.child_lei AND o.identity_status = 'verified'
 ) child_match ON TRUE
 LEFT JOIN LATERAL (
   SELECT count(*) AS n, min(o.organization_id::text) AS org_id,
          min(o.legal_name) AS legal_name
   FROM entity.organization_identifier i
   JOIN entity.organization o ON o.organization_id = i.organization_id
   WHERE i.identifier_scheme = 'GLEIF_LEI' AND i.is_verified IS TRUE
     AND i.identifier_value = r.parent_lei AND o.identity_status = 'verified'
 ) parent_match ON TRUE
)
SELECT
 r.child_lei,r.child_legal_name,r.child_organization_id,
 r.parent_lei,r.parent_legal_name,r.parent_organization_id,
 r.record_kind,r.reporting_exception,r.golden_copy_published,
 r.original_sha256,r.response_bytes,r.source_url,
 r.child_verified_matches,r.parent_verified_matches,
 (SELECT count(*) FROM entity.organization_relationship er
  WHERE er.child_id::text = r.child_organization_id
    AND er.parent_id::text = r.parent_organization_id
 ) AS existing_neon_relationship_rows,
 CASE
   WHEN r.record_kind = 'DIRECT_ACCOUNTING_CONSOLIDATION_PARENT_EXCEPTION'
        THEN 'BLOCKED_GLEIF_REPORTING_EXCEPTION_NO_PARENT_EDGE'
   WHEN r.child_verified_matches <> 1 OR r.parent_verified_matches <> 1
        THEN 'BLOCKED_MISSING_OR_AMBIGUOUS_EXACT_VERIFIED_LEI'
   WHEN r.child_organization_id = r.parent_organization_id
        THEN 'BLOCKED_SELF_RELATIONSHIP'
   ELSE 'RESEARCH_EXACT_GLEIF_ACCOUNTING_LINK_REVIEW_REQUIRED'
 END AS evidence_disposition,
 'GLEIF_ACCOUNTING_CONSOLIDATION_NOT_BENEFICIAL_OWNERSHIP'::text
    AS legal_relationship_scope,
 false AS regulator_insurance_group_membership_verified,
 false AS materialisation_authorized,
 false AS neon_written,
 false AS model_input_approved
FROM legal_identity_check r
ORDER BY r.record_kind, r.child_lei;
