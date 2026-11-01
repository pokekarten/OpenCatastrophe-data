-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Stage ONLY after review in insurance-risk-core / insurance.
-- Non-destructive, append-only registry-version research. It does NOT
-- acquire third-party data or grant source/model admission.
-- Live isolated Neon test: 2026-11-02, 115 revisions/114 source keys,
-- 0 raw/model approvals. DO NOT use on tcgp2p-core.
-- GitHub tree pinned: 45f637f8d381480c794fefba6c14605ae969a098.
-- WorldCover blob pinned: 2884e2f50b495eee3b399f55c08d43cfa100b602.
CREATE TABLE IF NOT EXISTS registry.source_contract_revision_v0 (
 source_key text NOT NULL REFERENCES registry.source_record(source_key),
 git_commit_sha text NOT NULL CHECK (git_commit_sha ~ '^[0-9a-f]{40}$'),
 git_blob_sha text NOT NULL CHECK (git_blob_sha ~ '^[0-9a-f]{40}$'),
 git_path text NOT NULL,
 contract_record jsonb NOT NULL,
 contract_status text NOT NULL,
 raw_import_allowed boolean NOT NULL DEFAULT false CHECK (raw_import_allowed IS FALSE),
 model_input_approved boolean NOT NULL DEFAULT false CHECK (model_input_approved IS FALSE),
 receipt_kind text NOT NULL,
 recorded_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(source_key,git_blob_sha)
);
-- Preserve independently recorded, historical Neon metadata without
-- mutating source_record. Different revisions must stay distinguishable.
INSERT INTO registry.source_contract_revision_v0
 (source_key,git_commit_sha,git_blob_sha,git_path,contract_record,contract_status,receipt_kind)
 SELECT source_key,git_commit_sha,git_blob_sha,git_path,raw_metadata,review_status,'neon_historical'
 FROM registry.source_record
 WHERE git_blob_sha ~ '^[0-9a-f]{40}$' AND git_commit_sha ~ '^[0-9a-f]{40}$'
 ON CONFLICT DO NOTHING;
-- New ESA contract: a digest-linked canonical Git metadata pointer only.
-- Complete authoritative JSON remains access/esa.worldcover.2021.v200.json.
-- This is NOT a raster, source-data import or model admission.
INSERT INTO registry.source_contract_revision_v0
 (source_key,git_commit_sha,git_blob_sha,git_path,contract_record,contract_status,receipt_kind)
 VALUES ('access:esa.worldcover.2021.v200',
 '45f637f8d381480c794fefba6c14605ae969a098',
 '2884e2f50b495eee3b399f55c08d43cfa100b602',
 'access/esa.worldcover.2021.v200.json',
 '{"access_id":"esa.worldcover.2021.v200","status":"probe_ready","provider":"ESA WorldCover / VITO","source":"pinned_original_github_json","raw_data_import":"prohibited","model_admission":"prohibited","bounded_one_block_canary":true}'::jsonb,
 'probe_ready','github_pinned_review') ON CONFLICT DO NOTHING;
-- Verification gates (read-only after staging):
-- SELECT count(*) AS revisions,count(DISTINCT source_key) AS sources,
--   count(*) FILTER (WHERE raw_import_allowed OR model_input_approved) AS unsafe
-- FROM registry.source_contract_revision_v0;
-- SELECT git_blob_sha,contract_status,receipt_kind
-- FROM registry.source_contract_revision_v0
-- WHERE source_key='access:esa.worldcover.2021.v200';
