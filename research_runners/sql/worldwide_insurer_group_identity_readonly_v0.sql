-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only global insurer group identity readiness diagnostic.
-- Execute against an explicitly selected insurance-risk-core / insurance branch.
-- This measures research inventory, NOT worldwide group coverage or identity admission.
-- Group-code namespaces and ownership relations require regulator and GLEIF review.
SELECT
  (SELECT count(*) FROM research.insurer_directory_candidate_v0) AS directory_candidate_rows,
  (SELECT count(DISTINCT country_slug) FROM research.insurer_directory_candidate_v0) AS candidate_market_slugs,
  (SELECT count(*) FROM entity.organization WHERE identity_status = 'verified') AS verified_legal_organizations,
  (SELECT count(*) FROM entity.organization_candidate) AS organization_candidates,
  (SELECT count(*) FROM entity.organization_candidate WHERE identity_resolution_status = 'unmatched') AS unmatched_organization_candidates,
  (SELECT count(*) FROM entity.organization_identifier WHERE identifier_scheme = 'GLEIF_LEI' AND is_verified) AS verified_lei_identifiers,
  (SELECT count(*) FROM entity.organization_identifier WHERE identifier_scheme ILIKE 'NAIC%GROUP%' AND is_verified) AS verified_naic_group_code_identifiers,
  (SELECT count(*) FROM entity.organization_relationship) AS asserted_organization_relationships,
  (SELECT count(*) FROM research.insurer_directory_candidate_v0 WHERE model_input_approved IS TRUE) AS approved_directory_model_rows,
  false AS group_identity_auto_merge_authorized,
  false AS cat_model_admission_authorized;
