-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READ ONLY. Explicitly select CAT Neon isolated br-steep-lab-baeo8bmc.
-- Two immutable historical baselines and two unapproved proposed versions.
-- No producer/raw/model authorization is conferred by passing this query.
WITH evidence AS (
 SELECT access_id,git_blob_sha,git_commit_sha,review_status,rights_status,
        probe_mode,evidence_role,contract_metadata,authorized_for_production,
        provider_bytes_admitted,model_input_approved
 FROM research.access_contract_revision_evidence_v0
), history AS (
 SELECT e.access_id,e.git_blob_sha,e.contract_metadata,
        s.raw_metadata AS registered_metadata,
        s.git_blob_sha AS registered_git_blob
 FROM evidence e
 LEFT JOIN registry.source_record s ON s.classification='access_contract'
    AND s.source_id=e.access_id
 WHERE e.evidence_role='historical_observed'
)
SELECT 'ACCESS_REVISIONS_ISOLATED_RESEARCH_ONLY'::text AS scope,
       count(*)::int AS total_version_receipts,
       count(DISTINCT access_id)::int AS unique_access_contracts,
       count(*) FILTER(WHERE evidence_role='historical_observed')::int
             AS historical_revisions,
       count(*) FILTER(WHERE evidence_role='proposed_unapproved')::int
             AS proposed_unapproved_revisions,
       count(*) FILTER(WHERE review_status='documented_only'
          AND probe_mode='none')::int AS inactive_historical_access,
       count(*) FILTER(WHERE review_status='probe_ready'
          AND probe_mode IN ('head','provider_specific'))::int
             AS proposed_bounded_access,
       count(*) FILTER(WHERE authorized_for_production
          OR provider_bytes_admitted OR model_input_approved)::int
             AS authorization_violations,
       count(*) FILTER(WHERE evidence_role='proposed_unapproved'
          AND (contract_metadata->>'status') <> 'probe_ready')::int
             AS unreviewed_status_drift,
       (SELECT count(*)::int FROM history
          WHERE registered_metadata IS DISTINCT FROM contract_metadata
             OR registered_git_blob IS DISTINCT FROM git_blob_sha)
             AS mutated_historical_contracts,
       bool_and(rights_status='verified') AS rights_labels_preserved,
       FALSE AS production_migration_approved,
       FALSE AS commercial_provider_download_approved,
       FALSE AS science_or_cat_loss_admitted
FROM evidence;
